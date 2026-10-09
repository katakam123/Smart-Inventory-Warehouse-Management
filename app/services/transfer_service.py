
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.stock_transfer import StockTransfer, StockTransferItem
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.stock_movement import StockMovement


def create_transfer_service(
    db: Session,
    payload,
    user_id: int,
):
    """Create a pending stock transfer without changing inventory."""

    try:
        if (
            payload.source_warehouse_id
            == payload.destination_warehouse_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Source and destination warehouses must differ",
            )

        transfer = StockTransfer(
            source_warehouse_id=payload.source_warehouse_id,
            destination_warehouse_id=payload.destination_warehouse_id,
            created_by=user_id,
            status="Pending",
        )

        for item in payload.items:
            product = db.get(Product, item.product_id)

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.product_id} not found",
                )

            transfer.items.append(
                StockTransferItem(
                    product_id=item.product_id,
                    requested_quantity=item.quantity,
                    dispatched_quantity=0,
                    received_quantity=0,
                    shortage_quantity=0,
                )
            )

        db.add(transfer)
        db.commit()
        db.refresh(transfer)
        return transfer

    except Exception:
        db.rollback()
        raise


def list_transfers_service(db: Session, user):
    """List transfers with their items."""

    statement = (
        select(StockTransfer)
        .options(selectinload(StockTransfer.items))
        .order_by(StockTransfer.created_at.desc())
    )

    # If Warehouse Staff have a warehouse_id, restrict results
    # to transfers involving their warehouse.
    if user.role == "Warehouse Staff":
        if not getattr(user, "warehouse_id", None):
            return []

        statement = statement.where(
            (StockTransfer.source_warehouse_id == user.warehouse_id)
            | (
                StockTransfer.destination_warehouse_id
                == user.warehouse_id
            )
        )

    return db.scalars(statement).all()


def dispatch_transfer_service(
    db: Session,
    transfer_id: int,
    user,
):
    """Deduct source stock and mark a transfer In Transit."""

    try:
        transfer = db.scalar(
            select(StockTransfer)
            .where(StockTransfer.id == transfer_id)
            .options(selectinload(StockTransfer.items))
            .with_for_update()
        )

        if transfer is None:
            raise HTTPException(
                status_code=404,
                detail="Transfer not found",
            )

        if transfer.status != "Pending":
            raise HTTPException(
                status_code=400,
                detail="Only Pending transfers can be dispatched",
            )

        if user.role == "Warehouse Staff":
            if user.warehouse_id != transfer.source_warehouse_id:
                raise HTTPException(
                    status_code=403,
                    detail="You cannot dispatch from this warehouse",
                )

        # Lock and validate every source inventory row before
        # changing any stock.
        locked_rows = {}

        for item in transfer.items:
            inventory = db.scalar(
                select(Inventory)
                .where(
                    Inventory.product_id == item.product_id,
                    Inventory.warehouse_id
                    == transfer.source_warehouse_id,
                )
                .with_for_update()
            )

            if inventory is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"No source inventory for product "
                        f"{item.product_id}"
                    ),
                )

            if inventory.quantity_on_hand < item.requested_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Insufficient stock for product "
                        f"{item.product_id}"
                    ),
                )

            locked_rows[item.id] = inventory

        # Apply all stock changes after validation.
        for item in transfer.items:
            inventory = locked_rows[item.id]
            inventory.quantity_on_hand -= item.requested_quantity
            item.dispatched_quantity = item.requested_quantity

            movement = StockMovement(
                product_id=item.product_id,
                warehouse_id=transfer.source_warehouse_id,
                movement_type="Transfer Out",
                quantity=item.requested_quantity,
                reference_id=transfer.id,
                user_id=user.id,
            )
            db.add(movement)

        transfer.status = "In Transit"
        transfer.dispatched_at = datetime.utcnow()

        db.commit()
        db.refresh(transfer)
        return transfer

    except Exception:
        db.rollback()
        raise


def receive_transfer_service(
    db: Session,
    transfer_id: int,
    payload,
    user,
):
    """Receive goods, record shortages, and update destination stock."""

    try:
        transfer = db.scalar(
            select(StockTransfer)
            .where(StockTransfer.id == transfer_id)
            .options(selectinload(StockTransfer.items))
            .with_for_update()
        )

        if transfer is None:
            raise HTTPException(
                status_code=404,
                detail="Transfer not found",
            )

        if transfer.status != "In Transit":
            raise HTTPException(
                status_code=400,
                detail="Only In Transit transfers can be received",
            )

        if user.role == "Warehouse Staff":
            if user.warehouse_id != transfer.destination_warehouse_id:
                raise HTTPException(
                    status_code=403,
                    detail="You cannot receive into this warehouse",
                )

        requested_items = {
            item.id: item for item in transfer.items
        }

        received_items = {}
        for received in payload.items:
            if received.item_id in received_items:
                raise HTTPException(
                    status_code=422,
                    detail="Duplicate transfer item in receipt",
                )

            if received.item_id not in requested_items:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Item {received.item_id} does not belong "
                        "to this transfer"
                    ),
                )

            received_items[received.item_id] = received

        if set(received_items) != set(requested_items):
            raise HTTPException(
                status_code=422,
                detail="Provide a received quantity for every transfer item",
            )

        # Validate every quantity before changing inventory.
        for item_id, received in received_items.items():
            item = requested_items[item_id]

            if received.received_quantity > item.dispatched_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Received quantity cannot exceed dispatched "
                        f"quantity for item {item_id}"
                    ),
                )

        for item_id, received in received_items.items():
            item = requested_items[item_id]
            quantity_received = received.received_quantity

            inventory = db.scalar(
                select(Inventory)
                .where(
                    Inventory.product_id == item.product_id,
                    Inventory.warehouse_id
                    == transfer.destination_warehouse_id,
                )
                .with_for_update()
            )

            if inventory is None:
                inventory = Inventory(
                    product_id=item.product_id,
                    warehouse_id=transfer.destination_warehouse_id,
                    quantity_on_hand=0,
                )
                db.add(inventory)
                db.flush()

            inventory.quantity_on_hand += quantity_received

            item.received_quantity = quantity_received
            item.shortage_quantity = (
                item.dispatched_quantity - quantity_received
            )

            if quantity_received > 0:
                db.add(
                    StockMovement(
                        product_id=item.product_id,
                        warehouse_id=transfer.destination_warehouse_id,
                        movement_type="Transfer In",
                        quantity=quantity_received,
                        reference_id=transfer.id,
                        user_id=user.id,
                    )
                )

        transfer.status = "Received"
        transfer.received_at = datetime.utcnow()

        db.commit()
        db.refresh(transfer)
        return transfer

    except Exception:
        db.rollback()
        raise


def cancel_transfer_service(
    db: Session,
    transfer_id: int,
    user,
):
    """Cancel a transfer only before dispatch."""

    try:
        transfer = db.scalar(
            select(StockTransfer)
            .where(StockTransfer.id == transfer_id)
            .with_for_update()
        )

        if transfer is None:
            raise HTTPException(
                status_code=404,
                detail="Transfer not found",
            )

        if transfer.status != "Pending":
            raise HTTPException(
                status_code=400,
                detail="Only Pending transfers can be cancelled",
            )

        transfer.status = "Cancelled"

        db.commit()
        db.refresh(transfer)
        return transfer

    except Exception:
        db.rollback()
        raise