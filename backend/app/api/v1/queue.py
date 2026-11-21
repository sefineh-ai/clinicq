from datetime import date
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.queue import QueueStatus
from app.schemas.queue import QueueTicketResponse, CheckInRequest
from app.services import queue_service

router = APIRouter(prefix="/queue", tags=["Queue Management"])


@router.post("/check-in/{appointment_id}", response_model=QueueTicketResponse, status_code=status.HTTP_200_OK)
async def check_in_patient(
    appointment_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECEPTIONIST, UserRole.ADMIN)),
):
    """
    Check in a patient on the appointment day.
    Generates a queue ticket and places patient into doctor's live waiting queue.
    Broadcasts real-time WebSocket update to all open screens.
    """
    client_ip = request.client.host if request.client else None
    ticket = await queue_service.check_in_patient(
        db=db,
        appointment_id=appointment_id,
        current_user=current_user,
        ip_address=client_ip,
    )
    return QueueTicketResponse.model_validate(ticket)


@router.get("/doctor/{doctor_id}", response_model=list[QueueTicketResponse])
async def get_doctor_queue(
    doctor_id: int,
    target_date: date | None = Query(None, description="Date (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get active queue for a specific doctor on a given date."""
    effective_date = target_date or date(2026, 11, 21)
    tickets = await queue_service.get_doctor_queue(db, doctor_id, effective_date)
    return [QueueTicketResponse.model_validate(t) for t in tickets]


@router.get("/today", response_model=list[QueueTicketResponse])
async def get_all_active_queue_tickets(
    status_filter: QueueStatus | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get today's clinic-wide queue (used by receptionist and waiting room display)."""
    today = date(2026, 11, 21)
    tickets = await queue_service.get_clinic_queue_for_date(db, today, status_filter)
    return [QueueTicketResponse.model_validate(t) for t in tickets]


@router.post("/{ticket_id}/call", response_model=QueueTicketResponse)
async def call_next_patient(
    ticket_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.DOCTOR, UserRole.ADMIN)),
):
    """
    Doctor calls the next patient.
    Status changes to 'called', broadcast notification alerts waiting room and reception.
    """
    client_ip = request.client.host if request.client else None
    ticket = await queue_service.call_patient(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user,
        ip_address=client_ip,
    )
    return QueueTicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/start", response_model=QueueTicketResponse)
async def start_consultation(
    ticket_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.DOCTOR, UserRole.ADMIN)),
):
    """Mark consultation as started (patient has entered consultation room)."""
    client_ip = request.client.host if request.client else None
    ticket = await queue_service.start_consultation(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user,
        ip_address=client_ip,
    )
    return QueueTicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/complete", response_model=QueueTicketResponse)
async def complete_consultation(
    ticket_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.DOCTOR, UserRole.ADMIN)),
):
    """
    Doctor marks the visit done.
    Calculates completed duration and broadcasts update to all screens.
    """
    client_ip = request.client.host if request.client else None
    ticket = await queue_service.complete_consultation(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user,
        ip_address=client_ip,
    )
    return QueueTicketResponse.model_validate(ticket)
