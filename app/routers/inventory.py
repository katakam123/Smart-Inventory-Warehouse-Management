from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.inventory import Inventory
from app.models.stock_movement import StockMovement
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.schemas.inventory import (
    InventoryResponse,
    StockMovementResponse,
)

router = APIRouter(tags=["Inventory & Stock Management"])


# GET /inventory
@router.get("/inventory", response_model=list[InventoryResponse])
def get_inventory(
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    low_stock: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Inventory)

    if product_id is not None:
        query = query.filter(Inventory.product_id == product_id)

    if warehouse_id is not None:
        query = query.filter(Inventory.warehouse_id == warehouse_id)

    if low_stock:
        query = query.join(
    Product,
    Inventory.product_id == Product.id,
).filter(
    (Inventory.quantity_on_hand - Inventory.quantity_reserved)
    <= Product.reorder_level
)

    return query.all()


# GET /inventory/{product_id}/{warehouse_id}
@router.get(
    "/inventory/{product_id}/{warehouse_id}",
    response_model=InventoryResponse,
)
def get_inventory_item(
    product_id: int,
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = (
        db.query(Inventory)
        .filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
        )
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found",
        )

    return item


# GET /stock-movements
@router.get(
    "/stock-movements",
    response_model=list[StockMovementResponse],
)
def get_stock_movements(
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    query = db.query(StockMovement)

    if product_id is not None:
        query = query.filter(
            StockMovement.product_id == product_id
        )

    if warehouse_id is not None:
        query = query.filter(
            StockMovement.warehouse_id == warehouse_id
        )

    if movement_type is not None:
        allowed_types = {
            "Purchase Receipt",
            "Sale Dispatch",
            "Customer Return",
        }

        if movement_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Invalid movement type",
            )

        query = query.filter(
            StockMovement.movement_type == movement_type
        )

    if start_date is not None:
        query = query.filter(
            StockMovement.created_at >= start_date
        )

    if end_date is not None:
        query = query.filter(
            StockMovement.created_at <= end_date
        )

    return query.order_by(StockMovement.created_at.desc()).all()