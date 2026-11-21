from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from app.schemas.user import UserResponse, UserCreate
from app.schemas.schedule import ScheduleResponse


class DoctorBase(BaseModel):
    specialty: str = Field(..., min_length=2, max_length=100)
    room_number: str = Field(..., min_length=1, max_length=50)
    bio: str | None = None
    is_active: bool = True


class DoctorCreate(DoctorBase):
    user_id: int | None = None
    # Or create a user together with doctor profile:
    user: UserCreate | None = None
    # Flat user fields for convenience:
    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None


class DoctorUpdate(BaseModel):
    specialty: str | None = Field(None, min_length=2, max_length=100)
    room_number: str | None = Field(None, min_length=1, max_length=50)
    bio: str | None = None
    is_active: bool | None = None


class DoctorResponse(DoctorBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True


class DoctorWithSchedulesResponse(DoctorResponse):
    schedules: list[ScheduleResponse] = []

    class Config:
        from_attributes = True


DoctorDetailResponse = DoctorWithSchedulesResponse
