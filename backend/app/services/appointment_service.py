from datetime import date, time, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.schedule import DoctorSchedule
from app.models.user import User
from app.models.audit import AuditAction
from app.schemas.appointment import AppointmentCreate, AppointmentReschedule, AppointmentCancel
from app.services.audit_service import create_audit_entry
from app.core.exceptions import NotFoundException, ConflictException, AppException
from app.core.events import ws_manager


async def get_appointment_by_id(db: AsyncSession, appointment_id: int) -> Appointment:
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.doctor).selectinload(Doctor.user),
            selectinload(Appointment.booked_by_user),
        )
        .where(Appointment.id == appointment_id)
    )
    result = await db.execute(stmt)
    app = result.scalar_one_or_none()
    if not app:
        raise NotFoundException(f"Appointment with ID {appointment_id} not found")
    return app


async def book_appointment(
    db: AsyncSession,
    app_in: AppointmentCreate,
    current_user: User,
    ip_address: str | None = None,
) -> Appointment:
    """
    Book a patient into a doctor's slot.
    Guarantees race-condition safety:
    Even if two receptionists book the exact same slot at the exact same millisecond,
    PostgreSQL unique constraint and transactional locks ensure only ONE succeeds,
    and the second raises a 409 Conflict with a clear error message.
    """
    # 1. Validate doctor exists and is active
    doc_stmt = (
        select(Doctor)
        .options(selectinload(Doctor.user))
        .where(Doctor.id == app_in.doctor_id)
    )
    doc_result = await db.execute(doc_stmt)
    doctor = doc_result.scalar_one_or_none()
    if not doctor or not doctor.is_active:
        raise NotFoundException(f"Doctor with ID {app_in.doctor_id} not found or inactive")

    # 2. Validate day of week and working hours
    day_of_week = app_in.appointment_date.weekday()
    sch_stmt = select(DoctorSchedule).where(
        and_(
            DoctorSchedule.doctor_id == app_in.doctor_id,
            DoctorSchedule.day_of_week == day_of_week,
            DoctorSchedule.is_active == True,
        )
    )
    sch_result = await db.execute(sch_stmt)
    schedule = sch_result.scalar_one_or_none()
    if not schedule:
        raise AppException(
            f"Dr. {doctor.user.full_name} does not have working hours scheduled on {app_in.appointment_date.strftime('%A')}.",
            status_code=400,
        )

    # Check that start_time falls within schedule bounds
    slot_duration = timedelta(minutes=schedule.slot_duration_minutes)
    slot_start_dt = datetime.combine(app_in.appointment_date, app_in.start_time)
    slot_end_dt = slot_start_dt + slot_duration
    slot_end_time = slot_end_dt.time()

    sch_start_dt = datetime.combine(app_in.appointment_date, schedule.start_time)
    sch_end_dt = datetime.combine(app_in.appointment_date, schedule.end_time)

    if slot_start_dt < sch_start_dt or slot_end_dt > sch_end_dt:
        raise AppException(
            f"Appointment slot {app_in.start_time} - {slot_end_time} is outside doctor's working hours ({schedule.start_time} - {schedule.end_time}).",
            status_code=400,
        )

    # 3. Check for existing active appointment at that slot with FOR UPDATE lock
    existing_stmt = (
        select(Appointment)
        .where(
            and_(
                Appointment.doctor_id == app_in.doctor_id,
                Appointment.appointment_date == app_in.appointment_date,
                Appointment.start_time == app_in.start_time,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
        )
        .with_for_update()
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise ConflictException(
            f"Slot {app_in.start_time.strftime('%H:%M')} on {app_in.appointment_date} is already booked for Dr. {doctor.user.full_name}."
        )

    # 4. Insert new appointment
    appointment = Appointment(
        doctor_id=app_in.doctor_id,
        patient_name=app_in.patient_name,
        patient_phone=app_in.patient_phone,
        reason=app_in.reason,
        appointment_date=app_in.appointment_date,
        start_time=app_in.start_time,
        end_time=slot_end_time,
        status=AppointmentStatus.BOOKED,
        booked_by_user_id=current_user.id,
        notes=app_in.notes,
    )
    db.add(appointment)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise ConflictException(
            f"Slot {app_in.start_time.strftime('%H:%M')} on {app_in.appointment_date} was just booked by another user. Please choose another slot."
        )

    # 5. Record audit log
    await create_audit_entry(
        db=db,
        action=AuditAction.BOOKING_CREATED,
        entity_type="appointment",
        entity_id=appointment.id,
        user=current_user,
        details={
            "doctor_id": app_in.doctor_id,
            "doctor_name": doctor.user.full_name,
            "patient_name": app_in.patient_name,
            "patient_phone": app_in.patient_phone,
            "date": str(app_in.appointment_date),
            "start_time": str(app_in.start_time),
            "end_time": str(slot_end_time),
            "reason": app_in.reason,
        },
        ip_address=ip_address,
    )

    await db.commit()

    # Broadcast event via WebSocket
    await ws_manager.broadcast({
        "event": "APPOINTMENT_BOOKED",
        "doctor_id": appointment.doctor_id,
        "appointment_id": appointment.id,
        "date": str(appointment.appointment_date),
        "start_time": str(appointment.start_time),
        "patient_name": appointment.patient_name,
    })

    return await get_appointment_by_id(db, appointment.id)


async def reschedule_appointment(
    db: AsyncSession,
    appointment_id: int,
    reschedule_in: AppointmentReschedule,
    current_user: User,
    ip_address: str | None = None,
) -> Appointment:
    app = await get_appointment_by_id(db, appointment_id)
    if app.status in (AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW):
        raise AppException(
            f"Cannot reschedule appointment with status '{app.status.value}'.",
            status_code=400,
        )

    doctor = app.doctor
    day_of_week = reschedule_in.new_date.weekday()
    sch_stmt = select(DoctorSchedule).where(
        and_(
            DoctorSchedule.doctor_id == app.doctor_id,
            DoctorSchedule.day_of_week == day_of_week,
            DoctorSchedule.is_active == True,
        )
    )
    schedule = (await db.execute(sch_stmt)).scalar_one_or_none()
    if not schedule:
        raise AppException(
            f"Dr. {doctor.user.full_name} does not have working hours scheduled on {reschedule_in.new_date.strftime('%A')}.",
            status_code=400,
        )

    slot_duration = timedelta(minutes=schedule.slot_duration_minutes)
    slot_start_dt = datetime.combine(reschedule_in.new_date, reschedule_in.new_start_time)
    slot_end_time = (slot_start_dt + slot_duration).time()

    # Check conflict for new slot
    existing_stmt = (
        select(Appointment)
        .where(
            and_(
                Appointment.doctor_id == app.doctor_id,
                Appointment.appointment_date == reschedule_in.new_date,
                Appointment.start_time == reschedule_in.new_start_time,
                Appointment.id != app.id,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
        )
        .with_for_update()
    )
    if (await db.execute(existing_stmt)).scalar_one_or_none():
        raise ConflictException(
            f"New slot {reschedule_in.new_start_time.strftime('%H:%M')} on {reschedule_in.new_date} is already booked."
        )

    old_date = app.appointment_date
    old_time = app.start_time

    app.appointment_date = reschedule_in.new_date
    app.start_time = reschedule_in.new_start_time
    app.end_time = slot_end_time
    app.status = AppointmentStatus.BOOKED

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise ConflictException("Conflict when rescheduling appointment to new slot.")

    # Record audit log
    await create_audit_entry(
        db=db,
        action=AuditAction.BOOKING_RESCHEDULED,
        entity_type="appointment",
        entity_id=app.id,
        user=current_user,
        details={
            "old_date": str(old_date),
            "old_start_time": str(old_time),
            "new_date": str(app.appointment_date),
            "new_start_time": str(app.start_time),
            "reason": reschedule_in.reason,
            "patient_name": app.patient_name,
        },
        ip_address=ip_address,
    )

    await db.commit()

    await ws_manager.broadcast({
        "event": "APPOINTMENT_RESCHEDULED",
        "doctor_id": app.doctor_id,
        "appointment_id": app.id,
        "new_date": str(app.appointment_date),
        "new_start_time": str(app.start_time),
    })

    return await get_appointment_by_id(db, app.id)


async def cancel_appointment(
    db: AsyncSession,
    appointment_id: int,
    cancel_in: AppointmentCancel,
    current_user: User,
    ip_address: str | None = None,
) -> Appointment:
    app = await get_appointment_by_id(db, appointment_id)
    if app.status == AppointmentStatus.CANCELLED:
        raise AppException("Appointment is already cancelled.", status_code=400)
    if app.status == AppointmentStatus.COMPLETED:
        raise AppException("Cannot cancel an already completed appointment.", status_code=400)

    app.status = AppointmentStatus.CANCELLED
    if cancel_in.reason:
        app.notes = f"{app.notes or ''} [Cancelled: {cancel_in.reason}]".strip()

    await create_audit_entry(
        db=db,
        action=AuditAction.BOOKING_CANCELLED,
        entity_type="appointment",
        entity_id=app.id,
        user=current_user,
        details={
            "date": str(app.appointment_date),
            "start_time": str(app.start_time),
            "patient_name": app.patient_name,
            "reason": cancel_in.reason,
        },
        ip_address=ip_address,
    )

    await db.commit()

    await ws_manager.broadcast({
        "event": "APPOINTMENT_CANCELLED",
        "doctor_id": app.doctor_id,
        "appointment_id": app.id,
        "date": str(app.appointment_date),
        "start_time": str(app.start_time),
    })

    return await get_appointment_by_id(db, app.id)


async def list_appointments(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    doctor_id: int | None = None,
    appointment_date: date | None = None,
    status: AppointmentStatus | None = None,
    search: str | None = None,
) -> tuple[list[Appointment], int]:
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.doctor).selectinload(Doctor.user),
            selectinload(Appointment.booked_by_user),
        )
    )

    if doctor_id:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    if appointment_date:
        stmt = stmt.where(Appointment.appointment_date == appointment_date)
    if status:
        stmt = stmt.where(Appointment.status == status)
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            (Appointment.patient_name.ilike(search_filter))
            | (Appointment.patient_phone.ilike(search_filter))
            | (Appointment.reason.ilike(search_filter))
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(
        desc(Appointment.appointment_date), Appointment.start_time
    ).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total
