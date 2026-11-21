from datetime import date, datetime, time
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit import AuditAction
from app.services.audit_service import create_audit_entry
from app.core.events import ws_manager

logger = logging.getLogger("clinicq.jobs.noshow")


async def run_noshow_sweep(db: AsyncSession, reference_date: date | None = None) -> int:
    """
    Finds all unattended appointments that were scheduled for reference_date (or past dates)
    where status is still 'booked' (patient never checked in) and marks them as 'no_show'.
    Records an audit log entry for each.
    """
    today = reference_date or date(2026, 11, 21)
    logger.info(f"Running no-show sweep for appointments up to {today}...")

    # Select all appointments with status BOOKED scheduled on or before today
    # (If today, we can check those whose start_time has elapsed or end of clinic day)
    stmt = (
        select(Appointment)
        .where(
            and_(
                Appointment.status == AppointmentStatus.BOOKED,
                Appointment.appointment_date <= today,
            )
        )
    )
    result = await db.execute(stmt)
    unattended = list(result.scalars().all())

    updated_count = 0
    for app in unattended:
        app.status = AppointmentStatus.NO_SHOW
        await create_audit_entry(
            db=db,
            action=AuditAction.APPOINTMENT_NO_SHOW,
            entity_type="appointment",
            entity_id=app.id,
            user_name="Background System Job",
            user_role="system",
            details={
                "doctor_id": app.doctor_id,
                "patient_name": app.patient_name,
                "appointment_date": str(app.appointment_date),
                "start_time": str(app.start_time),
                "reason": "Patient did not check in by clinic close.",
            },
        )
        updated_count += 1

    if updated_count > 0:
        await db.commit()
        logger.info(f"Marked {updated_count} appointments as no-show.")
        await ws_manager.broadcast({
            "event": "NO_SHOW_SWEEP_COMPLETED",
            "count": updated_count,
            "date": str(today),
        })

    return updated_count
