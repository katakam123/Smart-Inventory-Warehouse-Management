
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.sales_order import SalesOrder, SalesOrderItem


# GST rate: 18%
GST_RATE = Decimal("0.18")
ZERO = Decimal("0.00")
OPEN_ORDER_STATUSES = (
    "Confirmed",
    "Picked",
    "Packed",
    "Dispatched",
)


def money(value):
    """Round a monetary value to two decimal places."""
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def generate_so_number(db: Session) -> str:
    """
    Generate a sales order number such as SO-20261009-0001.

    The database must have a UNIQUE constraint on so_number.
    For high-concurrency production systems, use a dedicated
    database sequence or another concurrency-safe number generator.
    """
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"SO-{today}-"

    count = db.execute(
        select(func.count(SalesOrder.id)).where(
            SalesOrder.so_number.like(f"{prefix}%")
        )
    ).scalar_one()

    return f"{prefix}{count + 1:04d}"


def create_sales_order(db: Session, payload):
    """
    Create a Draft sales order.

    Expected payload:
        customer_id
        warehouse_id
        items: [{product_id, quantity}, ...]

    The price is read from the Product table and saved as a
    snapshot in SalesOrderItem. Stock is NOT reserved here.
    """
    try:
        if not payload.items:
            raise HTTPException(
                status_code=400,
                detail="A sales order must contain at least one item",
            )

        # Lock the customer row while checking account status.
        customer = db.execute(
            select(Customer)
            .where(Customer.id == payload.customer_id)
            .with_for_update()
        ).scalar_one_or_none()

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=400,
                detail="Inactive customers cannot place orders",
            )

        # Confirm that the warehouse exists and is active.
        from app.models.warehouse import Warehouse

        warehouse = db.execute(
            select(Warehouse).where(
                Warehouse.id == payload.warehouse_id
            )
        ).scalar_one_or_none()

        if warehouse is None:
            raise HTTPException(
                status_code=404,
                detail="Warehouse not found",
            )

        if not warehouse.is_active:
            raise HTTPException(
                status_code=400,
                detail="Cannot create orders for an inactive warehouse",
            )

        # Reject duplicate products in the same request.
        product_ids = [item.product_id for item in payload.items]

        if len(product_ids) != len(set(product_ids)):
            raise HTTPException(
                status_code=400,
                detail="Each product must appear only once in an order",
            )

        subtotal = ZERO
        order_lines = []

        for requested_item in payload.items:
            if requested_item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Product quantity must be greater than zero",
                )

            product = db.execute(
                select(Product).where(
                    Product.id == requested_item.product_id
                )
            ).scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Product {requested_item.product_id} not found"
                    ),
                )

            if not product.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Product {product.id} is inactive"
                    ),
                )

            unit_price = money(product.price)

            if unit_price <= ZERO:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product {product.id} has an invalid price",
                )

            line_total = money(
                unit_price * requested_item.quantity
            )

            subtotal += line_total

            order_lines.append({
                "product_id": product.id,
                "quantity": requested_item.quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            })

        subtotal = money(subtotal)
        tax_amount = money(subtotal * GST_RATE)
        grand_total = money(subtotal + tax_amount)

        order = SalesOrder(
            so_number=generate_so_number(db),
            customer_id=customer.id,
            warehouse_id=warehouse.id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            grand_total=grand_total,
            status="Draft",
        )

        db.add(order)
        db.flush()

        for line in order_lines:
            db.add(
                SalesOrderItem(
                    sales_order_id=order.id,
                    product_id=line["product_id"],
                    quantity=line["quantity"],
                    unit_price=line["unit_price"],
                    line_total=line["line_total"],
                )
            )

        db.commit()
        db.refresh(order)

        return order

    except Exception:
        db.rollback()
        raise


def confirm_sales_order(db: Session, so_id: int):
    """
    Confirm a Draft order after checking the customer's credit limit
    and available stock.

    Available stock = quantity_on_hand - quantity_reserved.

    Confirmation increases quantity_reserved; it does not reduce
    quantity_on_hand.
    """
    try:
        order = db.execute(
            select(SalesOrder)
            .where(SalesOrder.id == so_id)
            .with_for_update()
        ).scalar_one_or_none()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Sales order not found",
            )

        if order.status != "Draft":
            raise HTTPException(
                status_code=400,
                detail="Only Draft orders can be confirmed",
            )

        # Lock customer so concurrent confirmations for this customer
        # can serialize their credit-limit checks.
        customer = db.execute(
            select(Customer)
            .where(Customer.id == order.customer_id)
            .with_for_update()
        ).scalar_one_or_none()

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=400,
                detail="Inactive customers cannot confirm orders",
            )

        # Calculate outstanding order value. Draft, Cancelled and
        # Delivered orders do not count toward this open-order total.
        open_total = db.execute(
            select(
                func.coalesce(func.sum(SalesOrder.grand_total), 0)
            ).where(
                SalesOrder.customer_id == customer.id,
                SalesOrder.status.in_(OPEN_ORDER_STATUSES),
            )
        ).scalar_one()

        credit_used = money(open_total)
        order_total = money(order.grand_total)
        credit_limit = money(customer.credit_limit)

        if credit_used + order_total > credit_limit:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Customer credit limit exceeded. "
                    f"Credit limit: {credit_limit}; "
                    f"open orders: {credit_used}; "
                    f"new order: {order_total}"
                ),
            )

        items = db.execute(
            select(SalesOrderItem)
            .where(SalesOrderItem.sales_order_id == order.id)
            .order_by(SalesOrderItem.product_id)
        ).scalars().all()

        if not items:
            raise HTTPException(
                status_code=400,
                detail="Cannot confirm an order with no items",
            )

        inventory_rows = {}

        # Lock and validate every inventory row before making changes.
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
                    status_code=409,
                    detail=(
                        f"No inventory record for product "
                        f"{item.product_id} in this warehouse"
                    ),
                )

            available = (
                inventory.quantity_on_hand
                - inventory.quantity_reserved
            )

            if available < item.quantity:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Insufficient available stock for product "
                        f"{item.product_id}. Available: {available}; "
                        f"requested: {item.quantity}"
                    ),
                )

            inventory_rows[item.product_id] = inventory

        # Reserve stock only after all validations pass.
        for item in items:
            inventory_rows[item.product_id].quantity_reserved += (
                item.quantity
            )

        order.status = "Confirmed"

        # Order status and all stock reservations commit together.
        db.commit()
        db.refresh(order)

        return order

    except Exception:
        db.rollback()
        raise


def cancel_sales_order(db: Session, so_id: int):
    """
    Cancel a Draft or Confirmed order.

    If the order is Confirmed, release its reserved quantities.
    Picked, Packed, Dispatched and Delivered orders cannot be cancelled.
    """
    try:
        order = db.execute(
            select(SalesOrder)
            .where(SalesOrder.id == so_id)
            .with_for_update()
        ).scalar_one_or_none()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Sales order not found",
            )

        if order.status not in ("Draft", "Confirmed"):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only Draft or Confirmed orders can be cancelled"
                ),
            )

        if order.status == "Confirmed":
            items = db.execute(
                select(SalesOrderItem)
                .where(SalesOrderItem.sales_order_id == order.id)
                .order_by(SalesOrderItem.product_id)
            ).scalars().all()

            inventory_rows = {}

            # Validate all reservations before releasing any.
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
                        status_code=409,
                        detail=(
                            f"Inventory missing for product "
                            f"{item.product_id}"
                        ),
                    )

                if inventory.quantity_reserved < item.quantity:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"Reserved stock is inconsistent for product "
                            f"{item.product_id}"
                        ),
                    )

                inventory_rows[item.product_id] = inventory

            for item in items:
                inventory_rows[item.product_id].quantity_reserved -= (
                    item.quantity
                )

        order.status = "Cancelled"

        # Cancellation and reservation release commit together.
        db.commit()
        db.refresh(order)

        return order

    except Exception:
        db.rollback()
        raise