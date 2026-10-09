
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.schemas.stock_adjustment import (
    AdjustmentCreate,
    AdjustmentReview,
)

router = APIRouter(prefix="/adjustments", tags=["Stock Adjustments"])


def require_roles(user, allowed_roles):
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission for this operation",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_adjustment(
    payload: AdjustmentCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_roles(user, ["Warehouse Staff"])

    from app.services.adjustment_service import create_adjustment_service
    return create_adjustment_service(db, payload, user.id)


@router.get("/")
def list_adjustments(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_roles(user, ["Admin", "Inventory Manager", "Warehouse Staff"])

    from app.services.adjustment_service import list_adjustments_service
    return list_adjustments_service(db, user)


@router.put("/{adjustment_id}/approve")
def approve_adjustment(
    adjustment_id: int,
    payload: AdjustmentReview,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_roles(user, ["Admin", "Inventory Manager"])

    from app.services.adjustment_service import approve_adjustment_service
    return approve_adjustment_service(db, adjustment_id, payload, user.id)


@router.put("/{adjustment_id}/reject")
def reject_adjustment(
    adjustment_id: int,
    payload: AdjustmentReview,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_roles(user, ["Admin", "Inventory Manager"])

    if not payload.review_notes or not payload.review_notes.strip():
        raise HTTPException(
            status_code=422,
            detail="A rejection reason is required",
        )

    from app.services.adjustment_service import reject_adjustment_service
    return reject_adjustment_service(db, adjustment_id, payload, user.id)