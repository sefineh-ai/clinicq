from datetime import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.audit import AuditLog, AuditAction
from app.models.user import User


async def create_audit_entry(
    db: AsyncSession,
    action: AuditAction,
    entity_type: str,
    entity_id: int,
    user: User | None = None,
    user_name: str | None = None,
    user_role: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record an audit log entry for booking, cancelling, rescheduling, check-in, queue, or no-show."""
    u_id = user.id if user else None
    u_name = user.full_name if user else (user_name or "System")
    u_role = user.role.value if user else (user_role or "system")

    log_entry = AuditLog(
        user_id=u_id,
        user_name=u_name,
        user_role=u_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
        ip_address=ip_address,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry


async def list_audit_logs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    action: AuditAction | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    user_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> tuple[list[AuditLog], int]:
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if from_date:
        stmt = stmt.where(AuditLog.timestamp >= from_date)
    if to_date:
        stmt = stmt.where(AuditLog.timestamp <= to_date)

    # Count total
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginated ordered query
    stmt = stmt.order_by(desc(AuditLog.timestamp)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total
