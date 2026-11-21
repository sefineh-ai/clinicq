from datetime import time, date
from pydantic import BaseModel, Field, model_validator


class ScheduleBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time = Field(..., description="Schedule start time, e.g. 09:00:00")
    end_time: time = Field(..., description="Schedule end time, e.g. 17:00:00")
    slot_duration_minutes: int = Field(20, ge=5, le=120, description="Duration of each slot in minutes")
    is_active: bool = True

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    slot_duration_minutes: int | None = Field(None, ge=5, le=120)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class ScheduleBulkUpdateItem(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    slot_duration_minutes: int = 20
    is_active: bool = True


class ScheduleBulkUpdateRequest(BaseModel):
    schedules: list[ScheduleBulkUpdateItem]


class ScheduleResponse(ScheduleBase):
    id: int
    doctor_id: int

    class Config:
        from_attributes = True


class SlotInfo(BaseModel):
    start_time: time
    end_time: time
    is_available: bool
    appointment_id: int | None = None
    patient_name: str | None = None


class DaySlotsResponse(BaseModel):
    doctor_id: int
    doctor_name: str
    date: date
    day_of_week: int
    day_name: str
    is_working: bool
    slot_duration_minutes: int
    slots: list[SlotInfo]


# Aliases for route imports
DoctorScheduleCreate = ScheduleCreate
DoctorScheduleUpdate = ScheduleUpdate
DoctorScheduleResponse = ScheduleResponse
DoctorScheduleBulkUpdate = ScheduleBulkUpdateRequest
FreeSlotResponse = DaySlotsResponse
