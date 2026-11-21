from datetime import datetime
from pydantic import BaseModel, Field
from app.models.queue import QueueStatus
from app.schemas.appointment import AppointmentResponse
from app.schemas.doctor import DoctorResponse


class CheckInRequest(BaseModel):
    appointment_id: int = Field(..., description="ID of the booked appointment to check in")


class QueueTicketResponse(BaseModel):
    id: int
    appointment_id: int
    doctor_id: int
    ticket_number: str
    status: QueueStatus
    check_in_time: datetime
    called_time: datetime | None = None
    consultation_start_time: datetime | None = None
    completed_time: datetime | None = None
    created_at: datetime
    updated_at: datetime
    appointment: AppointmentResponse | None = None
    doctor: DoctorResponse | None = None

    class Config:
        from_attributes = True


class QueueListResponse(BaseModel):
    items: list[QueueTicketResponse]
    waiting_count: int
    in_progress_count: int
    completed_count: int


class CallNextResponse(BaseModel):
    ticket: QueueTicketResponse | None
    message: str
