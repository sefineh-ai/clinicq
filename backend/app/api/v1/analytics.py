from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.analytics import DailySummaryResponse
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])


@router.get("/daily-summary", response_model=DailySummaryResponse)
async def get_daily_summary(
    target_date: date | None = Query(None, description="Date for summary (defaults to 2026-11-21)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)),
):
    """
    Daily summary showing bookings, completed visits, no-shows,
    and average patient wait times per doctor.
    """
    effective_date = target_date or date(2026, 11, 21)
    return await analytics_service.get_daily_summary(db, effective_date)
