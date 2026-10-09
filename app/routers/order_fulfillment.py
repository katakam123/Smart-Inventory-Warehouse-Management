from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.sales_order import SalesOrder, SalesOrderItem
from app.models.inventory import Inventory
from app.models.stock_movement import StockMovement

router = APIRouter(
    prefix="/sales-orders",
    tags=["Stock Reservation and Dispatch"],
)


class DispatchRequest(BaseModel):
    courier_name: str = Field(min_length=1, max_length=100)
    tracking_number: str = Field(min_length=1, max_length=100)


def load_order(db: Session, so_id: int):
    order = db.execute(
        select(SalesOrder)
        .where(SalesOrder.id == so_id)
        .with_for_update()
    ).scalar_one_or_none()

    if order is None:
        raise HTTPException(404, "Sales order not found")

    return order


def check_warehouse_permission(user, order):
    if user.role == "Admin":
        return

    if (
        user.role != "Warehouse Staff"
        or user.warehouse_id != order.warehouse_id
    ):
        raise HTTPException(
            403,
            "Only Admin or staff assigned to this warehouse can perform this action",
        )


def check_status(order, expected_status):
    if order.status != expected_status:
        raise HTTPException(
            400,
            f"Expected status {expected_status}; current status is {order.status}",
        )


@router.put("/{so_id}/pick")
def pick_order(
    so_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        order = load_order(db, so_id)
        check_warehouse_permission(user, order)
        check_status(order, "Confirmed")

        order.status = "Picked"
        db.commit()
        db.refresh(order)

        return {"message": "Order picked", "status": order.status}
    except Exception:
        db.rollback()
        raise


@router.put("/{so_id}/pack")
def pack_order(
    so_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        order = load_order(db, so_id)
        check_warehouse_permission(user, order)
        check_status(order, "Picked")

        order.status = "Packed"
        db.commit()
        db.refresh(order)

        return {"message": "Order packed", "status": order.status}
    except Exception:
        db.rollback()
        raise


@router.put("/{so_id}/dispatch")
def dispatch_order(
    so_id: int,
    payload: DispatchRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        order = load_order(db, so_id)
        check_warehouse_permission(user, order)
        check_status(order, "Packed")

        courier = payload.courier_name.strip()
        tracking = payload.tracking_number.strip()

        if not courier or not tracking:
            raise HTTPException(
                422, "Courier name and tracking number are required"
            )

        # The database must also enforce UNIQUE(tracking_number).
        duplicate = db.execute(
            select(SalesOrder.id).where(
                SalesOrder.tracking_number == tracking,
                SalesOrder.id != so_id,
            )
        ).first()

        if duplicate:
            raise HTTPException(
                409, "Tracking number is already in use"
            )

        items = db.execute(
            select(SalesOrderItem)
            .where(SalesOrderItem.sales_order_id == so_id)
            .order_by(SalesOrderItem.product_id)
        ).scalars().all()

        if not items:
            raise HTTPException(400, "Order has no items")

        inventory_rows = {}

        # Validate all stock before changing any quantities.
        for item in items:
            inventory = db.execute(
                select(Inventory)
                .where(
                    Inventory.product_id == item.product_id,
                    Inventory.warehouse_id == order.warehouse_id,
                )
                .with_for_update()
            ).scalar_one_or_none()

            if inventory is None:
                raise HTTPException(
                    409, f"Inventory missing for product {item.product_id}"
                )

            if (
                inventory.quantity_on_hand < item.quantity
                or inventory.quantity_reserved < item.quantity
            ):
                raise HTTPException(
                    409,
                    f"Insufficient on-hand or reserved stock for product {item.product_id}",
                )

            inventory_rows[item.product_id] = inventory

        for item in items:
            inventory = inventory_rows[item.product_id]

            inventory.quantity_on_hand -= item.quantity
            inventory.quantity_reserved -= item.quantity

            db.add(StockMovement(
                product_id=item.product_id,
                warehouse_id=order.warehouse_id,
                movement_type="Sale Dispatch",
                quantity=item.quantity,
                reference_id=order.id,
                balance_after=inventory.quantity_on_hand,
                performed_by=user.id,
            ))

        order.courier_name = courier
        order.tracking_number = tracking
        order.dispatched_at = datetime.utcnow()
        order.status = "Dispatched"

        # Order, inventory and ledger changes commit together.
        db.commit()
        db.refresh(order)

        return {
            "message": "Order dispatched successfully",
            "status": order.status,
            "courier_name": order.courier_name,
            "tracking_number": order.tracking_number,
        }

    except Exception:
        db.rollback()
        raise


@router.put("/{so_id}/deliver")
def deliver_order(
    so_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        order = load_order(db, so_id)
        check_warehouse_permission(user, order)
        check_status(order, "Dispatched")

        order.status = "Delivered"
        order.delivered_at = datetime.utcnow()

        db.commit()
        db.refresh(order)

        return {
            "message": "Order delivered successfully",
            "status": order.status,
            "delivered_at": order.delivered_at,
        }
    except Exception:
        db.rollback()
        raise