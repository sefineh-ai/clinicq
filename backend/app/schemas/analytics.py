from datetime import date
from pydantic import BaseModel


class DoctorDailyMetric(BaseModel):
    doctor_id: int
    doctor_name: str
    specialty: str
    room_number: str | None = None
    total_bookings: int = 0
    booked_count: int = 0
    checked_in: int = 0
    completed: int = 0
    no_shows: int = 0
    no_show_count: int = 0
    cancelled: int = 0
    average_wait_minutes: float = 0.0
    avg_wait_minutes: float = 0.0
    average_consultation_minutes: float = 0.0
    avg_consultation_minutes: float = 0.0


class DailySummaryResponse(BaseModel):
    date: date
    total_appointments: int = 0
    total_bookings: int = 0
    total_completed: int = 0
    total_no_shows: int = 0
    total_cancelled: int = 0
    average_clinic_wait_minutes: float = 0.0
    clinic_avg_wait_minutes: float = 0.0
    doctor_metrics: list[DoctorDailyMetric] = []
    doctors: list[DoctorDailyMetric] = []


DailySummaryDoctorResponse = DoctorDailyMetric
