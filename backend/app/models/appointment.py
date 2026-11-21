import enum
from datetime import datetime, date, time, timezone
from sqlalchemy import (
    String, DateTime, Date, Time, Integer, ForeignKey, Text,
    Enum as SQLEnum, Index, text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AppointmentStatus(str, enum.Enum):
    BOOKED = "booked"
    CHECKED_IN = "checked_in"
    CALLED = "called"
    IN_CONSULTATION = "in_consultation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    patient_phone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False, index=True)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLEnum(AppointmentStatus, name="appointment_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=AppointmentStatus.BOOKED,
        nullable=False,
        index=True
    )
    booked_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        # Partial unique index: A doctor cannot have two active appointments at the exact same date & start time!
        # Cancelled appointments do NOT block re-booking the slot.
        Index(
            "uq_doctor_active_slot",
            "doctor_id",
            "appointment_date",
            "start_time",
            unique=True,
            postgresql_where=text("status != 'cancelled'"),
            sqlite_where=text("status != 'cancelled'"),
        ),
    )

    # Relationships
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="appointments")
    booked_by_user: Mapped["User"] = relationship("User", back_populates="booked_appointments")
    queue_ticket: Mapped["QueueTicket"] = relationship("QueueTicket", back_populates="appointment", uselist=False, cascade="all, delete-orphan")
