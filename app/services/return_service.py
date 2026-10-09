
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.return_request import ReturnRequest, ReturnItem
from app.models.sales_order import SalesOrder, SalesOrderItem
from app.models.inventory import Inventory


CENT = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(
        CENT, rounding=ROUND_HALF_UP
    )


def get_return(db: Session, return_id: int):
    result = db.execute(
        select(ReturnRequest)
        .options(selectinload(ReturnRequest.items))
        .where(ReturnRequest.id == return_id)
    )
    request = result.scalar_one_or_none()

    if request is None:
        raise HTTPException(404, "Return request not found")

    return request


def create_return(db: Session, so_id: int, payload, user):
    if user.role != "Inventory Manager":
        raise HTTPException(
            403, "Only Inventory Manager can create return requests"
        )

    try:
        order = db.execute(
            select(SalesOrder)
            .options(selectinload(SalesOrder.items))
            .where(SalesOrder.id == so_id)
            .with_for_update()
        ).scalar_one_or_none()

        if order is None:
            raise HTTPException(404, "Sales order not found")

        if order.status != "Delivered" or not order.delivered_at:
            raise HTTPException(
                400, "Returns are allowed only for Delivered orders"
            )

        delivered_at = order.delivered_at
        if delivered_at.tzinfo is None:
            delivered_at = delivered_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if now > delivered_at + timedelta(days=7):
            raise HTTPException(
                400, "The 7-day return window has expired"
            )

        if not payload.items:
            raise HTTPException(400, "At least one return item is required")

        requested_quantities = {}
        for item in payload.items:
            if item.product_id in requested_quantities:
                raise HTTPException(
                    400, "Do not repeat a product in the same return request"
                )
            requested_quantities[item.product_id] = item.quantity

        order_items = {
            item.product_id: item for item in order.items
        }

        # Count quantities already requested or processed.
        existing_returns = db.execute(
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.so_id == so_id)
            .with_for_update()
        ).scalars().all()

        already_returned = {}
        for old_return in existing_returns:
            if old_return.status == "Rejected":
                continue

            for old_item in old_return.items:
                already_returned[old_item.product_id] = (
                    already_returned.get(old_item.product_id, 0)
                    + old_item.quantity
                )

        return_request = ReturnRequest(
            so_id=so_id,
            reason=payload.reason.strip(),
            status="Requested",
            refund_amount=Decimal("0.00")
        )
        db.add(return_request)
        db.flush()

        for product_id, quantity in requested_quantities.items():
            order_item = order_items.get(product_id)

            if order_item is None:
                raise HTTPException(
                    400, f"Product {product_id} is not in this order"
                )

            previous_qty = already_returned.get(product_id, 0)
            if previous_qty + quantity > order_item.quantity:
                raise HTTPException(
                    400,
                    f"Return quantity exceeds delivered quantity "
                    f"for product {product_id}"
                )

            db.add(ReturnItem(
                return_id=return_request.id,
                product_id=product_id,
                quantity=quantity,
                original_unit_price=money(order_item.unit_price),
                condition=None,
                refund_amount=Decimal("0.00")
            ))

        db.commit()
        return get_return(db, return_request.id)

    except Exception:
        db.rollback()
        raise


def inspect_return(db: Session, return_id: int, payload, user):
    if user.role not in ["Warehouse Staff", "Admin"]:
        raise HTTPException(
            403, "Only Warehouse Staff or Admin can inspect returns"
        )

    try:
        request = get_return(db, return_id)

        if request.status != "Requested":
            raise HTTPException(
                400, "Only Requested returns can be inspected"
            )

        order = db.get(SalesOrder, request.so_id)

        # Warehouse staff may inspect returns for their assigned warehouse.
        if user.role == "Warehouse Staff":
            if getattr(user, "warehouse_id", None) != order.warehouse_id:
                raise HTTPException(
                    403, "You are not assigned to this order's warehouse"
                )

        item_by_id = {item.id: item for item in request.items}
        submitted = {}

        for inspected in payload.items:
            if inspected.item_id in submitted:
                raise HTTPException(400, "Duplicate item in inspection")
            submitted[inspected.item_id] = inspected.condition

        if set(submitted) != set(item_by_id):
            raise HTTPException(
                400, "Inspect every item in the return request exactly once"
            )

        for item_id, condition in submitted.items():
            item_by_id[item_id].condition = condition

        request.status = "Inspected"
        db.commit()
        return get_return(db, return_id)

    except Exception:
        db.rollback()
        raise


def approve_return(db: Session, return_id: int, user):
    if user.role not in ["Admin", "Inventory Manager"]:
        raise HTTPException(
            403, "Only Admin or Inventory Manager can approve returns"
        )

    try:
        request = db.execute(
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.id == return_id)
            .with_for_update()
        ).scalar_one_or_none()

        if request is None:
            raise HTTPException(404, "Return request not found")

        if request.status != "Inspected":
            raise HTTPException(
                400, "Only Inspected returns can be approved"
            )

        if any(item.condition not in ["Good", "Damaged"]
               for item in request.items):
            raise HTTPException(
                400, "Every returned item must have an inspection condition"
            )

        order = db.get(SalesOrder, request.so_id)

        # Compute proportional order tax from the original order totals.
        subtotal = money(order.subtotal)
        tax_amount = money(order.tax_amount)

        total_refund = Decimal("0.00")
        for item in request.items:
            item_subtotal = money(
                item.original_unit_price * item.quantity
            )

            if subtotal > 0:
                item_tax = money(item_subtotal * tax_amount / subtotal)
            else:
                item_tax = Decimal("0.00")

            item.refund_amount = money(item_subtotal + item_tax)
            total_refund += item.refund_amount

            # Good items return to sellable stock; damaged items do not.
            if item.condition == "Good":
                inventory = db.execute(
                    select(Inventory)
                    .where(
                        Inventory.product_id == item.product_id,
                        Inventory.warehouse_id == order.warehouse_id
                    )
                    .with_for_update()
                ).scalar_one_or_none()

                if inventory is None:
                    inventory = Inventory(
                        product_id=item.product_id,
                        warehouse_id=order.warehouse_id,
                        quantity_on_hand=0,
                        quantity_reserved=0
                    )
                    db.add(inventory)
                    db.flush()

                inventory.quantity_on_hand += item.quantity

            # Each item retains its condition and quantity in return_items.
            # A stock movement audit record should also be written here
            # using your project's actual StockMovement column names.

        request.refund_amount = money(total_refund)
        request.status = "Refunded"
        request.rejection_reason = None

        # This records the refund in the database. It does not call a
        # payment gateway or send money to the customer's payment method.
        db.commit()
        return get_return(db, return_id)

    except Exception:
        db.rollback()
        raise


def reject_return(
    db: Session, return_id: int, rejection_reason: str, user
):
    if user.role not in ["Admin", "Inventory Manager"]:
        raise HTTPException(
            403, "Only Admin or Inventory Manager can reject returns"
        )

    reason = rejection_reason.strip()
    if len(reason) < 3:
        raise HTTPException(400, "A rejection reason is required")

    try:
        request = db.execute(
            select(ReturnRequest)
            .where(ReturnRequest.id == return_id)
            .with_for_update()
        ).scalar_one_or_none()

        if request is None:
            raise HTTPException(404, "Return request not found")

        if request.status != "Inspected":
            raise HTTPException(
                400, "Only Inspected returns can be rejected"
            )

        request.status = "Rejected"
        request.rejection_reason = reason
        db.commit()
        return get_return(db, return_id)

    except Exception:
        db.rollback()
        raise