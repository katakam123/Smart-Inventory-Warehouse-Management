
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.return_request import ReturnRequest
from app.schemas.returns import (
    ReturnCreate,
    ReturnInspection,
    ReturnReject,
    ReturnResponse,
)
from app.services.return_service import (
    create_return,
    inspect_return,
    approve_return,
    reject_return,
)

router = APIRouter(tags=["Returns & Refunds"])


@router.post(
    "/sales-orders/{so_id}/returns",
    response_model=ReturnResponse,
    status_code=201
)
def create_sales_return(
    so_id: int,
    payload: ReturnCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return create_return(db, so_id, payload, user)


@router.get("/returns", response_model=list[ReturnResponse])
def list_returns(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    query = (
        select(ReturnRequest)
        .options(selectinload(ReturnRequest.items))
        .order_by(ReturnRequest.id.desc())
    )

    # Warehouse Staff only see returns belonging to their warehouse.
    if user.role == "Warehouse Staff":
        from app.models.sales_order import SalesOrder

        query = query.join(
            SalesOrder,
            ReturnRequest.so_id == SalesOrder.id
        ).where(SalesOrder.warehouse_id == user.warehouse_id)

    return db.execute(query).scalars().unique().all()


@router.put(
    "/returns/{return_id}/inspect",
    response_model=ReturnResponse
)
def inspect_sales_return(
    return_id: int,
    payload: ReturnInspection,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return inspect_return(db, return_id, payload, user)


@router.put(
    "/returns/{return_id}/approve",
    response_model=ReturnResponse
)
def approve_sales_return(
    return_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return approve_return(db, return_id, user)


@router.put(
    "/returns/{return_id}/reject",
    response_model=ReturnResponse
)
def reject_sales_return(
    return_id: int,
    payload: ReturnReject,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return reject_return(
        db, return_id, payload.rejection_reason, user
    )