from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.models.queue import QueueTicket, QueueStatus
from app.models.user import User
from app.schemas.analytics import DailySummaryDoctorResponse, DailySummaryResponse


async def get_daily_summary(db: AsyncSession, target_date: date) -> DailySummaryResponse:
    # 1. Fetch all doctors
    doc_stmt = (
        select(Doctor)
        .options(selectinload(Doctor.user))
        .where(Doctor.is_active == True)
        .order_by(Doctor.id)
    )
    doctors = list((await db.execute(doc_stmt)).scalars().all())

    # 2. Fetch all appointments for target_date
    app_stmt = (
        select(Appointment)
        .where(Appointment.appointment_date == target_date)
    )
    appointments = list((await db.execute(app_stmt)).scalars().all())

    # 3. Fetch all queue tickets for target_date
    ticket_stmt = (
        select(QueueTicket)
        .join(Appointment, QueueTicket.appointment_id == Appointment.id)
        .where(Appointment.appointment_date == target_date)
    )
    tickets = list((await db.execute(ticket_stmt)).scalars().all())

    # Group by doctor
    app_by_doc: dict[int, list[Appointment]] = {d.id: [] for d in doctors}
    for a in appointments:
        if a.doctor_id in app_by_doc:
            app_by_doc[a.doctor_id].append(a)

    tickets_by_doc: dict[int, list[QueueTicket]] = {d.id: [] for d in doctors}
    for t in tickets:
        if t.doctor_id in tickets_by_doc:
            tickets_by_doc[t.doctor_id].append(t)

    doctor_summaries: list[DailySummaryDoctorResponse] = []

    total_bookings = 0
    total_checked_in = 0
    total_completed = 0
    total_no_shows = 0
    total_cancelled = 0
    all_wait_times = []
    all_consultation_times = []

    for doc in doctors:
        d_apps = app_by_doc.get(doc.id, [])
        d_tickets = tickets_by_doc.get(doc.id, [])

        booked_count = len(d_apps)
        no_show_count = sum(1 for a in d_apps if a.status == AppointmentStatus.NO_SHOW)
        cancelled_count = sum(1 for a in d_apps if a.status == AppointmentStatus.CANCELLED)
        checked_in_count = len(d_tickets)
        completed_count = sum(1 for t in d_tickets if t.status == QueueStatus.COMPLETED)

        # Wait times: from check_in_time to called_time
        doc_wait_times = []
        doc_consult_times = []

        for t in d_tickets:
            if t.called_time and t.check_in_time:
                wait_min = (t.called_time - t.check_in_time).total_seconds() / 60.0
                if wait_min >= 0:
                    doc_wait_times.append(wait_min)
                    all_wait_times.append(wait_min)

            if t.completed_time and t.consultation_start_time:
                consult_min = (t.completed_time - t.consultation_start_time).total_seconds() / 60.0
                if consult_min >= 0:
                    doc_consult_times.append(consult_min)
                    all_consultation_times.append(consult_min)

        avg_wait = round(sum(doc_wait_times) / len(doc_wait_times), 1) if doc_wait_times else 0.0
        avg_consult = round(sum(doc_consult_times) / len(doc_consult_times), 1) if doc_consult_times else 0.0

        doctor_summaries.append(
            DailySummaryDoctorResponse(
                doctor_id=doc.id,
                doctor_name=doc.user.full_name,
                specialty=doc.specialty,
                room_number=doc.room_number,
                total_bookings=booked_count,
                booked_count=booked_count,
                checked_in=checked_in_count,
                completed=completed_count,
                no_shows=no_show_count,
                no_show_count=no_show_count,
                cancelled=cancelled_count,
                average_wait_minutes=avg_wait,
                avg_wait_minutes=avg_wait,
                average_consultation_minutes=avg_consult,
                avg_consultation_minutes=avg_consult,
            )
        )

        total_bookings += booked_count
        total_checked_in += checked_in_count
        total_completed += completed_count
        total_no_shows += no_show_count
        total_cancelled += cancelled_count

    clinic_avg_wait = round(sum(all_wait_times) / len(all_wait_times), 1) if all_wait_times else 0.0

    return DailySummaryResponse(
        date=target_date,
        total_appointments=total_bookings,
        total_bookings=total_bookings,
        total_completed=total_completed,
        total_no_shows=total_no_shows,
        total_cancelled=total_cancelled,
        average_clinic_wait_minutes=clinic_avg_wait,
        clinic_avg_wait_minutes=clinic_avg_wait,
        doctor_metrics=doctor_summaries,
        doctors=doctor_summaries,
    )
