import asyncio
import os
import sys
from datetime import date, datetime, time, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.schedule import DoctorSchedule
from app.models.appointment import Appointment, AppointmentStatus
from app.models.queue import QueueTicket, QueueStatus
from app.models.audit import AuditLog, AuditAction
from app.core.security import get_password_hash

async def seed_data():
    print("🌱 Seeding ClinicQ database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(User).filter_by(email="admin@clinicq.com"))
        if result.scalar_one_or_none():
            print("Database already has admin user. Skipping seed.")
            return

        now_utc = datetime.now(timezone.utc)
        # Note: Today is 2026-11-21 (Saturday)
        today = date(2026, 11, 21)

        # 1. Create Admin User
        admin = User(
            email="admin@clinicq.com",
            hashed_password=get_password_hash("AdminPass123!"),
            full_name="Sarah Jenkins (Admin)",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)

        # 2. Create Receptionists
        receptionist1 = User(
            email="receptionist1@clinicq.com",
            hashed_password=get_password_hash("ReceptPass123!"),
            full_name="Emma Watson (Lead Reception)",
            role=UserRole.RECEPTIONIST,
            is_active=True,
        )
        receptionist2 = User(
            email="receptionist2@clinicq.com",
            hashed_password=get_password_hash("ReceptPass123!"),
            full_name="David Miller (Reception)",
            role=UserRole.RECEPTIONIST,
            is_active=True,
        )
        db.add_all([receptionist1, receptionist2])

        # 3. Create Doctor Users
        doc_user1 = User(
            email="dr.smith@clinicq.com",
            hashed_password=get_password_hash("DocPass123!"),
            full_name="Dr. Alex Smith",
            role=UserRole.DOCTOR,
            is_active=True,
        )
        doc_user2 = User(
            email="dr.patel@clinicq.com",
            hashed_password=get_password_hash("DocPass123!"),
            full_name="Dr. Priya Patel",
            role=UserRole.DOCTOR,
            is_active=True,
        )
        doc_user3 = User(
            email="dr.chen@clinicq.com",
            hashed_password=get_password_hash("DocPass123!"),
            full_name="Dr. Marcus Chen",
            role=UserRole.DOCTOR,
            is_active=True,
        )
        db.add_all([doc_user1, doc_user2, doc_user3])
        await db.flush()

        # 4. Create Doctor profiles
        doctor1 = Doctor(
            user_id=doc_user1.id,
            specialty="Cardiology",
            room_number="Room 101",
            bio="Senior Cardiologist with 15 years experience in preventive cardiology and heart health.",
            is_active=True,
        )
        doctor2 = Doctor(
            user_id=doc_user2.id,
            specialty="Pediatrics",
            room_number="Room 102",
            bio="Board-certified Pediatrician dedicated to adolescent health and developmental care.",
            is_active=True,
        )
        doctor3 = Doctor(
            user_id=doc_user3.id,
            specialty="General Medicine",
            room_number="Room 103",
            bio="Family physician focusing on holistic primary care and chronic illness management.",
            is_active=True,
        )
        db.add_all([doctor1, doctor2, doctor3])
        await db.flush()

        # 5. Create Schedules for Doctors
        # Working hours: Monday (0) through Saturday (5) 09:00 - 17:00, 20-minute slots
        schedules = []
        for doc in [doctor1, doctor2, doctor3]:
            # Monday through Saturday (0 to 5)
            for day in range(6):
                schedules.append(
                    DoctorSchedule(
                        doctor_id=doc.id,
                        day_of_week=day,
                        start_time=time(9, 0),
                        end_time=time(17, 0),
                        slot_duration_minutes=20,
                        is_active=True,
                    )
                )
        db.add_all(schedules)
        await db.flush()

        # 6. Seed today's sample appointments & queue tickets
        # Doctor 1 (Dr. Smith) appointments today:
        # 09:00 - Completed visit
        apt1 = Appointment(
            doctor_id=doctor1.id,
            patient_name="Robert Taylor",
            patient_phone="+1-555-0101",
            reason="Annual cardiovascular checkup",
            appointment_date=today,
            start_time=time(9, 0),
            end_time=time(9, 20),
            status=AppointmentStatus.COMPLETED,
            booked_by_user_id=receptionist1.id,
            notes="Blood pressure checked, ECG normal.",
        )
        db.add(apt1)
        await db.flush()

        q1 = QueueTicket(
            appointment_id=apt1.id,
            doctor_id=doctor1.id,
            ticket_number="Q-001",
            status=QueueStatus.COMPLETED,
            check_in_time=datetime(2026, 11, 21, 8, 50, 0, tzinfo=timezone.utc),
            called_time=datetime(2026, 11, 21, 9, 2, 0, tzinfo=timezone.utc),
            consultation_start_time=datetime(2026, 11, 21, 9, 3, 0, tzinfo=timezone.utc),
            completed_time=datetime(2026, 11, 21, 9, 22, 0, tzinfo=timezone.utc),
        )
        db.add(q1)

        # 09:20 - In Consultation
        apt2 = Appointment(
            doctor_id=doctor1.id,
            patient_name="Maria Garcia",
            patient_phone="+1-555-0102",
            reason="Chest tightness after exertion",
            appointment_date=today,
            start_time=time(9, 20),
            end_time=time(9, 40),
            status=AppointmentStatus.IN_CONSULTATION,
            booked_by_user_id=receptionist1.id,
            notes="Fasting blood panel ordered.",
        )
        db.add(apt2)
        await db.flush()

        q2 = QueueTicket(
            appointment_id=apt2.id,
            doctor_id=doctor1.id,
            ticket_number="Q-002",
            status=QueueStatus.IN_CONSULTATION,
            check_in_time=datetime(2026, 11, 21, 9, 10, 0, tzinfo=timezone.utc),
            called_time=datetime(2026, 11, 21, 9, 21, 0, tzinfo=timezone.utc),
            consultation_start_time=datetime(2026, 11, 21, 9, 23, 0, tzinfo=timezone.utc),
        )
        db.add(q2)

        # 09:40 - Called / Waiting in queue
        apt3 = Appointment(
            doctor_id=doctor1.id,
            patient_name="James Wilson",
            patient_phone="+1-555-0103",
            reason="Follow-up on hypertension medication",
            appointment_date=today,
            start_time=time(9, 40),
            end_time=time(10, 0),
            status=AppointmentStatus.CHECKED_IN,
            booked_by_user_id=receptionist2.id,
        )
        db.add(apt3)
        await db.flush()

        q3 = QueueTicket(
            appointment_id=apt3.id,
            doctor_id=doctor1.id,
            ticket_number="Q-003",
            status=QueueStatus.WAITING,
            check_in_time=datetime(2026, 11, 21, 9, 32, 0, tzinfo=timezone.utc),
        )
        db.add(q3)

        # 10:00 - Booked (Patient not yet checked in)
        apt4 = Appointment(
            doctor_id=doctor1.id,
            patient_name="Olivia Davis",
            patient_phone="+1-555-0104",
            reason="Palpitations and dizziness",
            appointment_date=today,
            start_time=time(10, 0),
            end_time=time(10, 20),
            status=AppointmentStatus.BOOKED,
            booked_by_user_id=receptionist1.id,
        )
        db.add(apt4)

        # Doctor 2 (Dr. Patel) appointments today:
        # 09:00 - Checked in, waiting
        apt5 = Appointment(
            doctor_id=doctor2.id,
            patient_name="Lucas Martinez (Child)",
            patient_phone="+1-555-0105",
            reason="High fever and earache",
            appointment_date=today,
            start_time=time(9, 0),
            end_time=time(9, 20),
            status=AppointmentStatus.CHECKED_IN,
            booked_by_user_id=receptionist2.id,
        )
        db.add(apt5)
        await db.flush()

        q5 = QueueTicket(
            appointment_id=apt5.id,
            doctor_id=doctor2.id,
            ticket_number="Q-004",
            status=QueueStatus.WAITING,
            check_in_time=datetime(2026, 11, 21, 8, 55, 0, tzinfo=timezone.utc),
        )
        db.add(q5)

        # 09:20 - Completed
        apt6 = Appointment(
            doctor_id=doctor2.id,
            patient_name="Sophia Brown",
            patient_phone="+1-555-0106",
            reason="Routine childhood vaccination",
            appointment_date=today,
            start_time=time(9, 20),
            end_time=time(9, 40),
            status=AppointmentStatus.COMPLETED,
            booked_by_user_id=receptionist1.id,
        )
        db.add(apt6)
        await db.flush()

        q6 = QueueTicket(
            appointment_id=apt6.id,
            doctor_id=doctor2.id,
            ticket_number="Q-005",
            status=QueueStatus.COMPLETED,
            check_in_time=datetime(2026, 11, 21, 9, 12, 0, tzinfo=timezone.utc),
            called_time=datetime(2026, 11, 21, 9, 21, 0, tzinfo=timezone.utc),
            consultation_start_time=datetime(2026, 11, 21, 9, 22, 0, tzinfo=timezone.utc),
            completed_time=datetime(2026, 11, 21, 9, 38, 0, tzinfo=timezone.utc),
        )
        db.add(q6)

        # 08:40 - No show sample from earlier
        apt7 = Appointment(
            doctor_id=doctor3.id,
            patient_name="Ethan Thomas",
            patient_phone="+1-555-0107",
            reason="Allergy flare-up",
            appointment_date=today,
            start_time=time(8, 40),
            end_time=time(9, 0),
            status=AppointmentStatus.NO_SHOW,
            booked_by_user_id=receptionist1.id,
            notes="Patient did not attend.",
        )
        db.add(apt7)

        # 7. Create Audit Log entries
        audit_entries = [
            AuditLog(
                user_id=receptionist1.id,
                user_name=receptionist1.full_name,
                user_role=receptionist1.role.value,
                action=AuditAction.BOOKING_CREATED,
                entity_type="appointment",
                entity_id=apt1.id,
                details={"doctor": doctor1.user.full_name, "patient": apt1.patient_name, "slot": "09:00 - 09:20"},
                timestamp=now_utc - timedelta(hours=2),
            ),
            AuditLog(
                user_id=receptionist1.id,
                user_name=receptionist1.full_name,
                user_role=receptionist1.role.value,
                action=AuditAction.PATIENT_CHECKED_IN,
                entity_type="queue_ticket",
                entity_id=q1.id,
                details={"ticket_number": "Q-001", "patient": apt1.patient_name},
                timestamp=now_utc - timedelta(minutes=70),
            ),
            AuditLog(
                user_id=doc_user1.id,
                user_name=doc_user1.full_name,
                user_role=doc_user1.role.value,
                action=AuditAction.PATIENT_CALLED,
                entity_type="queue_ticket",
                entity_id=q1.id,
                details={"ticket_number": "Q-001", "room": doctor1.room_number},
                timestamp=now_utc - timedelta(minutes=58),
            ),
            AuditLog(
                user_id=doc_user1.id,
                user_name=doc_user1.full_name,
                user_role=doc_user1.role.value,
                action=AuditAction.CONSULTATION_COMPLETED,
                entity_type="queue_ticket",
                entity_id=q1.id,
                details={"ticket_number": "Q-001", "patient": apt1.patient_name},
                timestamp=now_utc - timedelta(minutes=38),
            ),
        ]
        db.add_all(audit_entries)

        await db.commit()
        print("✅ ClinicQ database seeded successfully!")
        print("Credentials:")
        print(" - Admin: admin@clinicq.com / AdminPass123!")
        print(" - Receptionist: receptionist1@clinicq.com / ReceptPass123!")
        print(" - Doctor: dr.smith@clinicq.com / DocPass123!")
        print(" - Doctor: dr.patel@clinicq.com / DocPass123!")
        print(" - Doctor: dr.chen@clinicq.com / DocPass123!")

if __name__ == "__main__":
    asyncio.run(seed_data())
