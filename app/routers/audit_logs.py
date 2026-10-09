
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse
from fastapi import BackgroundTasks
from app.services.email_service import send_email
router = APIRouter(tags=["Audit Logs"])


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    user_id: int | None = Query(default=None, gt=0),
    action: str | None = Query(default=None, min_length=1),
    entity_type: str | None = Query(default=None, min_length=1),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Only Admin can view audit logs",
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    query = select(AuditLog)

    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)

    if action:
        query = query.where(AuditLog.action == action)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)

    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)

    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)

    query = (
        query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        .limit(limit)
        .offset(offset)
    )

    return db.execute(query).scalars().all()