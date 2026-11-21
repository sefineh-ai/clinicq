from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.audit import AuditAction
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PaginatedResponse
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    action: AuditAction | None = Query(None, description="Filter by audit action"),
    entity_type: str | None = Query(None, description="Filter by entity type (e.g. appointment)"),
    entity_id: int | None = Query(None, description="Filter by entity ID"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    from_date: datetime | None = Query(None, description="From timestamp"),
    to_date: datetime | None = Query(None, description="To timestamp"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECEPTIONIST)),
):
    """
    List audit trail entries recording who, what, and when
    for bookings, cancellations, reschedules, check-ins, and visits.
    """
    items, total = await audit_service.list_audit_logs(
        db=db,
        page=page,
        page_size=page_size,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        from_date=from_date,
        to_date=to_date,
    )
    return PaginatedResponse.create(
        items=[AuditLogResponse.model_validate(log) for log in items],
        total=total,
        page=page,
        page_size=page_size,
    )
