from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse, DoctorDetailResponse
from app.schemas.schedule import DaySlotsResponse
from app.schemas.common import PaginatedResponse
from app.services import doctor_service, slot_service

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("", response_model=PaginatedResponse[DoctorResponse])
async def list_doctors(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    specialty: str | None = Query(None, description="Filter by specialty"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """List doctors with pagination and optional filtering."""
    items, total = await doctor_service.list_doctors(
        db=db,
        page=page,
        page_size=page_size,
        specialty=specialty,
        is_active=is_active,
    )
    return PaginatedResponse.create(
        items=[DoctorResponse.model_validate(doc) for doc in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{doctor_id}", response_model=DoctorDetailResponse)
async def get_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed doctor profile including weekly schedule."""
    doctor = await doctor_service.get_doctor_by_id(db, doctor_id)
    return DoctorDetailResponse.model_validate(doctor)


@router.get("/{doctor_id}/free-slots", response_model=DaySlotsResponse)
async def get_doctor_free_slots(
    doctor_id: int,
    date: date | None = Query(None, description="Date (YYYY-MM-DD)"),
    target_date: date | None = Query(None, description="Target date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """Get bookable free slots for a doctor on a given date."""
    chosen_date = date or target_date
    if not chosen_date:
        from datetime import date as dt_date
        chosen_date = dt_date.today()
    return await slot_service.get_doctor_slots_for_date(db, doctor_id, chosen_date)


@router.post("", response_model=DoctorDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    doctor_in: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create a new doctor profile and optional user account (Admin only)."""
    doctor = await doctor_service.create_doctor(db, doctor_in)
    return DoctorDetailResponse.model_validate(doctor)


@router.patch("/{doctor_id}", response_model=DoctorDetailResponse)
async def update_doctor(
    doctor_id: int,
    doctor_update: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update doctor profile details (Admin only)."""
    doctor = await doctor_service.update_doctor(db, doctor_id, doctor_update)
    return DoctorDetailResponse.model_validate(doctor)
