from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.inventory import Inventory
from app.models.warehouse import Warehouse
from app.models.stock_movement import StockMovement


def receive_purchase_order(
    db: Session,
    po_id: int,
    received_items: list,
    user_id: int,
):
    try:
        po = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .with_for_update()
            .first()
        )

        if not po:
            raise HTTPException(404, "Purchase order not found")

        if po.status not in ("Approved", "Partially Received"):
            raise HTTPException(
                400,
                "Only approved purchase orders can receive goods",
            )

        warehouse = (
            db.query(Warehouse)
            .filter(Warehouse.id == po.warehouse_id)
            .with_for_update()
            .first()
        )

        if not warehouse or not warehouse.is_active:
            raise HTTPException(400, "Warehouse is missing or inactive")

        # Reject repeated item IDs in the same receiving request.
        item_ids = [item.item_id for item in received_items]
        if len(item_ids) != len(set(item_ids)):
            raise HTTPException(
                400,
                "Each purchase order item can appear only once per request",
            )

        items_by_id = {item.id: item for item in po.items}

        for received in received_items:
            po_item = items_by_id.get(received.item_id)

            if not po_item:
                raise HTTPException(
                    400,
                    f"Item {received.item_id} does not belong to this purchase order",
                )

            if po_item.quantity_received + received.quantity > po_item.quantity_ordered:
                raise HTTPException(
                    400,
                    f"Received quantity exceeds ordered quantity for item {received.item_id}",
                )

        # Lock and load all affected inventory rows.
        inventory_by_product = {}

        for received in received_items:
            po_item = items_by_id[received.item_id]

            inventory = (
                db.query(Inventory)
                .filter(
                    Inventory.product_id == po_item.product_id,
                    Inventory.warehouse_id == po.warehouse_id,
                )
                .with_for_update()
                .first()
            )

            if inventory is None:
                inventory = Inventory(
                    product_id=po_item.product_id,
                    warehouse_id=po.warehouse_id,
                    quantity_on_hand=0,
                    quantity_reserved=0,
                )
                db.add(inventory)
                db.flush()

            inventory_by_product[po_item.product_id] = inventory

        # Check capacity before changing any quantities.
        current_total = (
            db.query(func.coalesce(func.sum(Inventory.quantity_on_hand), 0))
            .filter(Inventory.warehouse_id == po.warehouse_id)
            .scalar()
        )

        incoming_total = sum(item.quantity for item in received_items)

        if warehouse.capacity is not None:
            if current_total + incoming_total > warehouse.capacity:
                raise HTTPException(
                    400,
                    "Receiving this order would exceed warehouse capacity",
                )

        # Apply all quantities and create stock movement ledger entries.
        for received in received_items:
            po_item = items_by_id[received.item_id]
            inventory = inventory_by_product[po_item.product_id]

            inventory.quantity_on_hand += received.quantity
            po_item.quantity_received += received.quantity

            db.add(
                StockMovement(
                    product_id=po_item.product_id,
                    warehouse_id=po.warehouse_id,
                    movement_type="Purchase Receipt",
                    quantity=received.quantity,
                    reference_id=po.id,
                    balance_after=inventory.quantity_on_hand,
                    performed_by=user_id,
                )
            )

        db.flush()

        all_received = all(
            item.quantity_received == item.quantity_ordered
            for item in po.items
        )

        po.status = "Received" if all_received else "Partially Received"

        if all_received:
            po.received_at = datetime.utcnow()

        db.commit()
        db.refresh(po)
        return po

    except Exception:
        db.rollback()
        raise