from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.stock_movement import StockMovement
from app.models.warehouse import Warehouse


ALLOWED_MOVEMENTS = {
    "Purchase Receipt",
    "Sale Dispatch",
    "Customer Return",
}


def apply_stock_movement(
    db: Session,
    *,
    product_id: int,
    warehouse_id: int,
    movement_type: str,
    quantity: int,
    performed_by: int,
    reference_id: int | None = None,
):
    if movement_type not in ALLOWED_MOVEMENTS:
        raise HTTPException(
            status_code=400,
            detail="Invalid stock movement type",
        )

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero",
        )

    # Lock the warehouse row while checking capacity and activity.
    warehouse = (
        db.query(Warehouse)
        .filter(Warehouse.id == warehouse_id)
        .with_for_update()
        .first()
    )

    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    # Lock the product/warehouse inventory row.
    inventory = (
        db.query(Inventory)
        .filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
        )
        .with_for_update()
        .first()
    )

    # New inventory rows must also be created inside this transaction.
    if inventory is None:
        if movement_type == "Sale Dispatch":
            raise HTTPException(
                status_code=400,
                detail="No inventory record exists for this product and warehouse",
            )

        inventory = Inventory(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity_on_hand=0,
            quantity_reserved=0,
        )
        db.add(inventory)
        db.flush()

    if movement_type in {"Purchase Receipt", "Customer Return"}:
        if not warehouse.is_active:
            raise HTTPException(
                status_code=400,
                detail="Inactive warehouses cannot receive stock",
            )

        # Check total warehouse stock against its capacity.
        total_stock = (
            db.query(
                __import__("sqlalchemy").func.coalesce(
                    __import__("sqlalchemy").func.sum(
                        Inventory.quantity_on_hand
                    ),
                    0,
                )
            )
            .filter(Inventory.warehouse_id == warehouse_id)
            .scalar()
        )

        if int(total_stock) + quantity > warehouse.capacity:
            raise HTTPException(
                status_code=400,
                detail="Warehouse capacity would be exceeded",
            )

        inventory.quantity_on_hand += quantity

    elif movement_type == "Sale Dispatch":
        if inventory.quantity_on_hand < quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock on hand",
            )

        # Dispatch reserved stock first, then available stock.
        reserved_to_release = min(
            inventory.quantity_reserved,
            quantity,
        )

        inventory.quantity_reserved -= reserved_to_release

        if inventory.quantity_on_hand - quantity < inventory.quantity_reserved:
            raise HTTPException(
                status_code=400,
                detail="Dispatch would consume stock reserved for other orders",
            )

        inventory.quantity_on_hand -= quantity

    movement = StockMovement(
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=movement_type,
        quantity=quantity,
        reference_id=reference_id,
        balance_after=inventory.quantity_on_hand,
        performed_by=performed_by,
    )

    db.add(movement)

    # The caller commits the transaction so the stock and ledger
    # are saved together or rolled back together.
    db.flush()

    return inventory, movement