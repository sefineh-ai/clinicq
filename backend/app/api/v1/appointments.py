from datetime import date
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.appointment import AppointmentStatus
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentCancel,
    AppointmentResponse,
)
from app.schemas.common import PaginatedResponse
from app.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("", response_model=PaginatedResponse[AppointmentResponse])
async def list_appointments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    doctor_id: int | None = Query(None, description="Filter by doctor ID"),
    appointment_date: date | None = Query(None, description="Filter by date (YYYY-MM-DD)"),
    status: AppointmentStatus | None = Query(None, description="Filter by appointment status"),
    search: str | None = Query(None, description="Search patient name, phone, or reason"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List appointments with pagination and filters."""
    items, total = await appointment_service.list_appointments(
        db=db,
        page=page,
        page_size=page_size,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        status=status,
        search=search,
    )
    return PaginatedResponse.create(
        items=[AppointmentResponse.model_validate(app) for app in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single appointment details."""
    app = await appointment_service.get_appointment_by_id(db, appointment_id)
    return AppointmentResponse.model_validate(app)


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    app_in: AppointmentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECEPTIONIST, UserRole.ADMIN)),
):
    """
    Book a patient into a doctor's slot.
    Concurrency safe: Even if two receptionists book at the exact same moment,
    only one succeeds and the other receives a 409 Conflict error.
    """
    client_ip = request.client.host if request.client else None
    app = await appointment_service.book_appointment(
        db=db,
        app_in=app_in,
        current_user=current_user,
        ip_address=client_ip,
    )
    return AppointmentResponse.model_validate(app)


@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: int,
    reschedule_in: AppointmentReschedule,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECEPTIONIST, UserRole.ADMIN)),
):
    """Reschedule an existing appointment to a new date and time slot."""
    client_ip = request.client.host if request.client else None
    app = await appointment_service.reschedule_appointment(
        db=db,
        appointment_id=appointment_id,
        reschedule_in=reschedule_in,
        current_user=current_user,
        ip_address=client_ip,
    )
    return AppointmentResponse.model_validate(app)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    cancel_in: AppointmentCancel,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECEPTIONIST, UserRole.ADMIN)),
):
    """Cancel an appointment and free up the slot immediately."""
    client_ip = request.client.host if request.client else None
    app = await appointment_service.cancel_appointment(
        db=db,
        appointment_id=appointment_id,
        cancel_in=cancel_in,
        current_user=current_user,
        ip_address=client_ip,
    )
    return AppointmentResponse.model_validate(app)
