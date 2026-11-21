import enum
from datetime import datetime, timezone
from sqlalchemy import (
    String, DateTime, Integer, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class QueueStatus(str, enum.Enum):
    WAITING = "waiting"
    CALLED = "called"
    IN_CONSULTATION = "in_consultation"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class QueueTicket(Base):
    __tablename__ = "queue_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticket_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # e.g., "Q-001" or "D1-01"
    status: Mapped[QueueStatus] = mapped_column(
        SQLEnum(QueueStatus, name="queue_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=QueueStatus.WAITING,
        nullable=False,
        index=True
    )
    check_in_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    called_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consultation_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
        Index("ix_queue_doctor_status", "doctor_id", "status"),
    )

    # Relationships
    appointment: Mapped["Appointment"] = relationship("Appointment", back_populates="queue_ticket")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="queue_tickets")
