from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.models.audit import AuditAction


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    user_name: str
    user_role: str
    action: AuditAction
    entity_type: str
    entity_id: int
    details: dict[str, Any] | None
    ip_address: str | None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
