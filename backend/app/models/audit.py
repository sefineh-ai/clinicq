import enum
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import (
    String, DateTime, Integer, ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AuditAction(str, enum.Enum):
    BOOKING_CREATED = "booking_created"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_RESCHEDULED = "booking_rescheduled"
    PATIENT_CHECKED_IN = "patient_checked_in"
    PATIENT_CALLED = "patient_called"
    CONSULTATION_STARTED = "consultation_started"
    CONSULTATION_COMPLETED = "consultation_completed"
    APPOINTMENT_NO_SHOW = "appointment_no_show"
    SCHEDULE_UPDATED = "schedule_updated"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_role: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, name="audit_action_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "appointment", "queue_ticket", "schedule"
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
