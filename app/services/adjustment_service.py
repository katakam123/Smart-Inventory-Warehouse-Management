from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.stock_adjustment import StockAdjustment


def reject_adjustment_service(
    db: Session,
    adjustment_id: int,
    rejection_reason: str,
    user
):
    """
    Reject a pending stock adjustment.
    Only an Admin or Inventory Manager should be allowed
    to call this service.
    """

    try:
        # Find the adjustment
        adjustment = (
            db.query(StockAdjustment)
            .filter(StockAdjustment.id == adjustment_id)
            .with_for_update()
            .first()
        )

        # Check whether it exists
        if adjustment is None:
            raise HTTPException(
                status_code=404,
                detail="Stock adjustment not found"
            )

        # Only pending adjustments can be rejected
        if adjustment.status != "Pending":
            raise HTTPException(
                status_code=400,
                detail="Only pending adjustments can be rejected"
            )

        # Validate the rejection reason
        if not rejection_reason or not rejection_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required"
            )

        # Update the adjustment
        adjustment.status = "Rejected"
        adjustment.reviewed_by = user.id
        adjustment.notes = (
            f"{adjustment.notes or ''}\n"
            f"Rejection reason: {rejection_reason.strip()}"
        ).strip()
        adjustment.updated_at = datetime.utcnow()

        # Save changes
        db.commit()
        db.refresh(adjustment)

        return adjustment

    except Exception:
        db.rollback()
        raise