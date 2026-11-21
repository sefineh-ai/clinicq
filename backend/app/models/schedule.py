from datetime import time
from sqlalchemy import Time, Boolean, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)     # e.g. 09:00:00
    end_time: Mapped[time] = mapped_column(Time, nullable=False)       # e.g. 17:00:00
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=20, nullable=False)  # e.g. 20
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("doctor_id", "day_of_week", name="uq_doctor_day_of_week"),
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="chk_day_of_week_range"),
        CheckConstraint("end_time > start_time", name="chk_schedule_end_after_start"),
        CheckConstraint("slot_duration_minutes > 0", name="chk_slot_duration_positive"),
    )

    # Relationships
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="schedules")
