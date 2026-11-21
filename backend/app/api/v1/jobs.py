from datetime import date
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.services.noshow_job import run_noshow_sweep

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])


class JobRunResponse(BaseModel):
    success: bool = True
    updated_count: int
    message: str


@router.post("/run-noshow-sweep", response_model=JobRunResponse)
async def trigger_noshow_sweep(
    reference_date: date | None = Query(None, description="Reference date for sweep (defaults to 2026-11-21)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Manually trigger the evening no-show background sweep.
    Finds all unattended appointments for today or past days whose status is still 'booked'
    and marks them as 'no_show', recording an audit log entry for each.
    """
    effective_date = reference_date or date(2026, 11, 21)
    count = await run_noshow_sweep(db, reference_date=effective_date)
    return JobRunResponse(
        success=True,
        updated_count=count,
        message=f"No-show sweep completed successfully for {effective_date}. Marked {count} appointments as no-show."
    )
