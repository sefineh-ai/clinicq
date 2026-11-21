from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload
from app.models.queue import QueueTicket, QueueStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.user import User
from app.models.audit import AuditAction
from app.services.audit_service import create_audit_entry
from app.core.exceptions import NotFoundException, AppException, ConflictException
from app.core.events import ws_manager


async def get_queue_ticket_by_id(db: AsyncSession, ticket_id: int) -> QueueTicket:
    stmt = (
        select(QueueTicket)
        .options(
            selectinload(QueueTicket.appointment),
            selectinload(QueueTicket.doctor).selectinload(Doctor.user),
        )
        .where(QueueTicket.id == ticket_id)
    )
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundException(f"Queue ticket with ID {ticket_id} not found")
    return ticket


async def check_in_patient(
    db: AsyncSession,
    appointment_id: int,
    current_user: User,
    ip_address: str | None = None,
) -> QueueTicket:
    """
    Check-in patient for their appointment on the day.
    Creates a QueueTicket and puts them in doctor's queue.
    Broadcasts real-time WebSocket event to doctor and waiting room displays.
    """
    stmt = (
        select(Appointment)
        .options(selectinload(Appointment.doctor).selectinload(Doctor.user))
        .where(Appointment.id == appointment_id)
    )
    result = await db.execute(stmt)
    app = result.scalar_one_or_none()
    if not app:
        raise NotFoundException(f"Appointment with ID {appointment_id} not found")

    if app.status == AppointmentStatus.CANCELLED:
        raise AppException("Cannot check in a cancelled appointment.", status_code=400)
    if app.status == AppointmentStatus.COMPLETED:
        raise AppException("Appointment is already completed.", status_code=400)
    if app.status in (AppointmentStatus.CHECKED_IN, AppointmentStatus.CALLED, AppointmentStatus.IN_CONSULTATION):
        # Already checked in
        existing_stmt = select(QueueTicket).where(QueueTicket.appointment_id == appointment_id)
        existing_ticket = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing_ticket:
            return await get_queue_ticket_by_id(db, existing_ticket.id)

    # Generate daily sequential ticket number: e.g. Q-001, Q-002
    today_start = datetime.combine(app.appointment_date, datetime.min.time())
    today_end = datetime.combine(app.appointment_date, datetime.max.time())

    count_stmt = select(func.count(QueueTicket.id)).where(
        and_(
            QueueTicket.created_at >= today_start,
            QueueTicket.created_at <= today_end,
        )
    )
    daily_count = (await db.execute(count_stmt)).scalar_one()
    ticket_num = f"Q-{daily_count + 1:03d}"

    now = datetime.utcnow()
    app.status = AppointmentStatus.CHECKED_IN

    ticket = QueueTicket(
        appointment_id=app.id,
        doctor_id=app.doctor_id,
        ticket_number=ticket_num,
        status=QueueStatus.WAITING,
        check_in_time=now,
    )
    db.add(ticket)
    await db.flush()

    # Record audit log
    await create_audit_entry(
        db=db,
        action=AuditAction.PATIENT_CHECKED_IN,
        entity_type="queue_ticket",
        entity_id=ticket.id,
        user=current_user,
        details={
            "ticket_number": ticket_num,
            "appointment_id": app.id,
            "doctor_id": app.doctor_id,
            "doctor_name": app.doctor.user.full_name,
            "patient_name": app.patient_name,
        },
        ip_address=ip_address,
    )

    await db.commit()

    full_ticket = await get_queue_ticket_by_id(db, ticket.id)

    # Real-time WebSocket broadcast
    await ws_manager.broadcast({
        "event": "PATIENT_CHECKED_IN",
        "doctor_id": app.doctor_id,
        "ticket_id": ticket.id,
        "ticket_number": ticket_num,
        "patient_name": app.patient_name,
        "room_number": app.doctor.room_number,
        "doctor_name": app.doctor.user.full_name,
    })

    return full_ticket


async def call_patient(
    db: AsyncSession,
    ticket_id: int,
    current_user: User,
    ip_address: str | None = None,
) -> QueueTicket:
    ticket = await get_queue_ticket_by_id(db, ticket_id)
    now = datetime.utcnow()

    ticket.status = QueueStatus.CALLED
    ticket.called_time = now

    ticket.appointment.status = AppointmentStatus.CALLED

    await create_audit_entry(
        db=db,
        action=AuditAction.PATIENT_CALLED,
        entity_type="queue_ticket",
        entity_id=ticket.id,
        user=current_user,
        details={
            "ticket_number": ticket.ticket_number,
            "patient_name": ticket.appointment.patient_name,
            "doctor_name": ticket.doctor.user.full_name,
            "room_number": ticket.doctor.room_number,
        },
        ip_address=ip_address,
    )

    await db.commit()

    # Real-time broadcast for waiting room display and doctors
    await ws_manager.broadcast({
        "event": "PATIENT_CALLED",
        "doctor_id": ticket.doctor_id,
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "patient_name": ticket.appointment.patient_name,
        "room_number": ticket.doctor.room_number,
        "doctor_name": ticket.doctor.user.full_name,
    })

    return await get_queue_ticket_by_id(db, ticket.id)


async def start_consultation(
    db: AsyncSession,
    ticket_id: int,
    current_user: User,
    ip_address: str | None = None,
) -> QueueTicket:
    ticket = await get_queue_ticket_by_id(db, ticket_id)
    now = datetime.utcnow()

    ticket.status = QueueStatus.IN_CONSULTATION
    ticket.consultation_start_time = now
    ticket.appointment.status = AppointmentStatus.IN_CONSULTATION

    await create_audit_entry(
        db=db,
        action=AuditAction.CONSULTATION_STARTED,
        entity_type="queue_ticket",
        entity_id=ticket.id,
        user=current_user,
        details={
            "ticket_number": ticket.ticket_number,
            "patient_name": ticket.appointment.patient_name,
        },
        ip_address=ip_address,
    )

    await db.commit()

    await ws_manager.broadcast({
        "event": "CONSULTATION_STARTED",
        "doctor_id": ticket.doctor_id,
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
    })

    return await get_queue_ticket_by_id(db, ticket.id)


async def complete_visit(
    db: AsyncSession,
    ticket_id: int,
    current_user: User,
    ip_address: str | None = None,
) -> QueueTicket:
    ticket = await get_queue_ticket_by_id(db, ticket_id)
    now = datetime.utcnow()

    if not ticket.consultation_start_time:
        ticket.consultation_start_time = now

    ticket.status = QueueStatus.COMPLETED
    ticket.completed_time = now
    ticket.appointment.status = AppointmentStatus.COMPLETED

    await create_audit_entry(
        db=db,
        action=AuditAction.CONSULTATION_COMPLETED,
        entity_type="queue_ticket",
        entity_id=ticket.id,
        user=current_user,
        details={
            "ticket_number": ticket.ticket_number,
            "patient_name": ticket.appointment.patient_name,
            "doctor_name": ticket.doctor.user.full_name,
            "wait_seconds": (ticket.called_time - ticket.check_in_time).total_seconds() if ticket.called_time else 0,
            "consultation_seconds": (ticket.completed_time - ticket.consultation_start_time).total_seconds() if ticket.consultation_start_time else 0,
        },
        ip_address=ip_address,
    )

    await db.commit()

    await ws_manager.broadcast({
        "event": "VISIT_COMPLETED",
        "doctor_id": ticket.doctor_id,
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
    })

    return await get_queue_ticket_by_id(db, ticket.id)


# Alias for compatibility with router and tests
complete_consultation = complete_visit


async def list_doctor_queue(
    db: AsyncSession,
    doctor_id: int | None = None,
    statuses: list[QueueStatus] | None = None,
    target_date: date | None = None,
) -> list[QueueTicket]:
    stmt = (
        select(QueueTicket)
        .join(Appointment, QueueTicket.appointment_id == Appointment.id)
        .options(
            selectinload(QueueTicket.appointment),
            selectinload(QueueTicket.doctor).selectinload(Doctor.user),
        )
    )

    if doctor_id:
        stmt = stmt.where(QueueTicket.doctor_id == doctor_id)
    if statuses:
        stmt = stmt.where(QueueTicket.status.in_(statuses))
    if target_date:
        stmt = stmt.where(Appointment.appointment_date == target_date)

    # Order: active consultation first, called next, waiting ordered by check_in_time
    stmt = stmt.order_by(QueueTicket.check_in_time.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


# Alias for compatibility with router and test suite
async def get_doctor_queue(
    db: AsyncSession,
    doctor_id: int,
    target_date: date | None = None,
) -> list[QueueTicket]:
    return await list_doctor_queue(db, doctor_id=doctor_id, target_date=target_date)
