from datetime import datetime, date, time
from pydantic import BaseModel, Field, field_validator
import re
from app.models.appointment import AppointmentStatus
from app.schemas.doctor import DoctorResponse
from app.schemas.user import UserResponse


class AppointmentBase(BaseModel):
    doctor_id: int
    patient_name: str = Field(..., min_length=2, max_length=255, description="Full name of patient")
    patient_phone: str = Field(..., min_length=7, max_length=50, description="Contact phone number")
    reason: str = Field(..., min_length=3, max_length=500, description="Reason for visit")
    appointment_date: date
    start_time: time
    notes: str | None = None

    @field_validator("patient_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Allow +, digits, spaces, hyphens, parentheses
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\+?[0-9]{7,15}$", cleaned):
            raise ValueError("Invalid phone number format. Must contain 7-15 digits.")
        return v.strip()

    @field_validator("patient_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Patient name cannot be blank")
        return v.strip()


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentReschedule(BaseModel):
    new_date: date
    new_start_time: time
    reason: str | None = Field(None, description="Reason for rescheduling")


class AppointmentCancel(BaseModel):
    reason: str | None = Field(None, description="Reason for cancellation")


class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    patient_name: str
    patient_phone: str
    reason: str
    appointment_date: date
    start_time: time
    end_time: time
    status: AppointmentStatus
    booked_by_user_id: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    doctor: DoctorResponse | None = None

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    items: list[AppointmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
