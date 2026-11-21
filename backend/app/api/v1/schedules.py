from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.schedule import (
    DoctorScheduleCreate,
    DoctorScheduleUpdate,
    DoctorScheduleResponse,
    DoctorScheduleBulkUpdate,
    FreeSlotResponse,
)
from app.services import slot_service

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("/doctors/{doctor_id}", response_model=list[DoctorScheduleResponse])
async def get_doctor_schedules(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get weekly working schedule for a doctor (0=Mon, ..., 6=Sun)."""
    schedules = await slot_service.get_doctor_schedules(db, doctor_id)
    return [DoctorScheduleResponse.model_validate(s) for s in schedules]


@router.post("/doctors/{doctor_id}/bulk", response_model=list[DoctorScheduleResponse])
async def set_doctor_weekly_schedule(
    doctor_id: int,
    bulk_in: DoctorScheduleBulkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Set or replace full weekly working hours and slot duration for a doctor (Admin only)."""
    schedules = await slot_service.set_doctor_weekly_schedule(db, doctor_id, bulk_in.schedules)
    return [DoctorScheduleResponse.model_validate(s) for s in schedules]


@router.get("/doctors/{doctor_id}/free-slots", response_model=list[FreeSlotResponse])
async def get_free_slots_for_doctor(
    doctor_id: int,
    target_date: date = Query(..., description="Target date for booking (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate all bookable slots for a doctor on a specific date.
    Calculates working hours minus already booked active appointments.
    """
    slots = await slot_service.get_free_slots_for_doctor(db, doctor_id, target_date)
    return [FreeSlotResponse.model_validate(s) for s in slots]
