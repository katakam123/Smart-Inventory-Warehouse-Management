
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.schemas.stock_transfer import (
    TransferCreate,
    TransferReceive,
)

router = APIRouter(prefix="/transfers", tags=["Stock Transfers"])


def require_roles(user, allowed_roles):
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission for this operation",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_transfer(
    payload: TransferCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_roles(user, ["Admin", "Inventory Manager"])

    from app.services.transfer_service import create_transfer_service
    return create_transfer_service(db, payload, user.id)


@router.get("/")
def list_transfers(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_roles(user, ["Admin", "Inventory Manager", "Warehouse Staff"])

    from app.services.transfer_service import list_transfers_service
    return list_transfers_service(db, user)


@router.put("/{transfer_id}/dispatch")
def dispatch_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_roles(user, ["Admin", "Inventory Manager", "Warehouse Staff"])

    from app.services.transfer_service import dispatch_transfer_service
    return dispatch_transfer_service(db, transfer_id, user)


@router.put("/{transfer_id}/receive")
def receive_transfer(
    transfer_id: int,
    payload: TransferReceive,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_roles(user, ["Admin", "Inventory Manager", "Warehouse Staff"])

    from app.services.transfer_service import receive_transfer_service
    return receive_transfer_service(db, transfer_id, payload, user)


@router.put("/{transfer_id}/cancel")
def cancel_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_roles(user, ["Admin", "Inventory Manager"])

    from app.services.transfer_service import cancel_transfer_service
    return cancel_transfer_service(db, transfer_id, user)