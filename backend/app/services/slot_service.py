from datetime import date, time, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.doctor import Doctor
from app.models.schedule import DoctorSchedule
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleBulkUpdateRequest,
    DaySlotsResponse,
    SlotInfo,
)
from app.core.exceptions import NotFoundException, ConflictException


async def get_doctor_schedules(db: AsyncSession, doctor_id: int) -> list[DoctorSchedule]:
    stmt = (
        select(DoctorSchedule)
        .where(DoctorSchedule.doctor_id == doctor_id)
        .order_by(DoctorSchedule.day_of_week)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def set_doctor_schedule(
    db: AsyncSession, doctor_id: int, schedule_in: ScheduleCreate
) -> DoctorSchedule:
    # Verify doctor exists
    doc = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    if not doc.scalar_one_or_none():
        raise NotFoundException(f"Doctor with ID {doctor_id} not found")

    # Check if schedule for this day exists
    stmt = select(DoctorSchedule).where(
        and_(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.day_of_week == schedule_in.day_of_week,
        )
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.start_time = schedule_in.start_time
        existing.end_time = schedule_in.end_time
        existing.slot_duration_minutes = schedule_in.slot_duration_minutes
        existing.is_active = schedule_in.is_active
        await db.commit()
        await db.refresh(existing)
        return existing

    new_schedule = DoctorSchedule(
        doctor_id=doctor_id,
        day_of_week=schedule_in.day_of_week,
        start_time=schedule_in.start_time,
        end_time=schedule_in.end_time,
        slot_duration_minutes=schedule_in.slot_duration_minutes,
        is_active=schedule_in.is_active,
    )
    db.add(new_schedule)
    await db.commit()
    await db.refresh(new_schedule)
    return new_schedule


async def bulk_update_doctor_schedules(
    db: AsyncSession, doctor_id: int, request: ScheduleBulkUpdateRequest
) -> list[DoctorSchedule]:
    doc = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    if not doc.scalar_one_or_none():
        raise NotFoundException(f"Doctor with ID {doctor_id} not found")

    # Fetch all existing schedules for doctor
    stmt = select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id)
    result = await db.execute(stmt)
    existing_map = {s.day_of_week: s for s in result.scalars().all()}

    for item in request.schedules:
        if item.day_of_week in existing_map:
            sch = existing_map[item.day_of_week]
            sch.start_time = item.start_time
            sch.end_time = item.end_time
            sch.slot_duration_minutes = item.slot_duration_minutes
            sch.is_active = item.is_active
        else:
            sch = DoctorSchedule(
                doctor_id=doctor_id,
                day_of_week=item.day_of_week,
                start_time=item.start_time,
                end_time=item.end_time,
                slot_duration_minutes=item.slot_duration_minutes,
                is_active=item.is_active,
            )
            db.add(sch)

    await db.commit()
    return await get_doctor_schedules(db, doctor_id)


DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


async def get_doctor_slots_for_date(
    db: AsyncSession, doctor_id: int, target_date: date
) -> DaySlotsResponse:
    # Doctor info
    stmt = select(Doctor).where(Doctor.id == doctor_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise NotFoundException(f"Doctor with ID {doctor_id} not found")

    from app.models.user import User

    u_stmt = select(User).where(User.id == doc.user_id)
    doc_user = (await db.execute(u_stmt)).scalar_one_or_none()
    doctor_name = doc_user.full_name if doc_user else f"Doctor #{doctor_id}"

    day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday
    day_name = DAY_NAMES[day_of_week]

    # Schedule for that day
    sch_stmt = select(DoctorSchedule).where(
        and_(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.day_of_week == day_of_week,
            DoctorSchedule.is_active == True,
        )
    )
    schedule = (await db.execute(sch_stmt)).scalar_one_or_none()

    if not schedule or not doc.is_active:
        return DaySlotsResponse(
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            date=target_date,
            day_of_week=day_of_week,
            day_name=day_name,
            is_working=False,
            slot_duration_minutes=20,
            slots=[],
        )

    # Fetch active booked appointments on this date
    app_stmt = select(Appointment).where(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == target_date,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
    )
    booked_appointments = (await db.execute(app_stmt)).scalars().all()
    booked_map = {a.start_time: a for a in booked_appointments}

    # Generate discrete slots between start_time and end_time
    slots: list[SlotInfo] = []
    duration = timedelta(minutes=schedule.slot_duration_minutes)

    curr_dt = datetime.combine(target_date, schedule.start_time)
    end_dt = datetime.combine(target_date, schedule.end_time)

    while curr_dt + duration <= end_dt:
        slot_start = curr_dt.time()
        slot_end = (curr_dt + duration).time()

        is_booked = slot_start in booked_map
        booked_app = booked_map.get(slot_start)

        slots.append(
            SlotInfo(
                start_time=slot_start,
                end_time=slot_end,
                is_available=not is_booked,
                appointment_id=booked_app.id if booked_app else None,
                patient_name=booked_app.patient_name if booked_app else None,
            )
        )
        curr_dt += duration

    return DaySlotsResponse(
        doctor_id=doctor_id,
        doctor_name=doctor_name,
        date=target_date,
        day_of_week=day_of_week,
        day_name=day_name,
        is_working=True,
        slot_duration_minutes=schedule.slot_duration_minutes,
        slots=slots,
    )


async def get_free_slots_for_doctor(
    db: AsyncSession, doctor_id: int, target_date: date
) -> list[SlotInfo]:
    day_slots = await get_doctor_slots_for_date(db, doctor_id, target_date)
    return [s for s in day_slots.slots if s.is_available]

