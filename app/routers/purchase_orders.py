from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderReceive,
)
from app.services.purchase_order_service import receive_purchase_order

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


def require_role(user, allowed_roles):
    if user.role not in allowed_roles:
        raise HTTPException(403, "You do not have permission to perform this action")


def generate_po_number(db: Session) -> str:
    # Simple daily sequence generator for a beginner project.
    # For production, use a dedicated sequence/table or retry on unique conflicts.
    today = date.today()
    prefix = f"PO-{today:%Y%m%d}-"

    existing_numbers = (
        db.query(PurchaseOrder.po_number)
        .filter(PurchaseOrder.po_number.like(f"{prefix}%"))
        .all()
    )

    sequence = len(existing_numbers) + 1
    return f"{prefix}{sequence:04d}"


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase_order(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager"])

    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == data.supplier_id)
        .first()
    )
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    if not supplier.is_active:
        raise HTTPException(400, "Inactive suppliers cannot receive new orders")

    warehouse = (
        db.query(Warehouse)
        .filter(Warehouse.id == data.warehouse_id)
        .first()
    )
    if not warehouse:
        raise HTTPException(404, "Warehouse not found")
    if not warehouse.is_active:
        raise HTTPException(400, "Cannot create a purchase order for an inactive warehouse")

    product_ids = {item.product_id for item in data.items}
    found_products = {
        product.id
        for product in db.query(Product).filter(Product.id.in_(product_ids)).all()
    }
    missing = product_ids - found_products
    if missing:
        raise HTTPException(400, f"Unknown product IDs: {sorted(missing)}")

    expected_date = data.expected_delivery_date or (
        date.today() + timedelta(days=supplier.lead_time_days)
    )

    po = PurchaseOrder(
        po_number=generate_po_number(db),
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        expected_delivery_date=expected_date,
        total_amount=sum(
            (item.unit_cost * item.quantity_ordered for item in data.items),
            Decimal("0.00"),
        ),
        status="Draft",
    )

    for item in data.items:
        po.items.append(
            PurchaseOrderItem(
                product_id=item.product_id,
                quantity_ordered=item.quantity_ordered,
                quantity_received=0,
                unit_cost=item.unit_cost,
            )
        )

    db.add(po)

    try:
        db.commit()
        db.refresh(po)
        return po
    except Exception:
        db.rollback()
        raise HTTPException(
            409,
            "Could not create purchase order. Check the data and retry.",
        )


@router.get("", response_model=list[PurchaseOrderResponse])
def list_purchase_orders(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager", "Warehouse Staff"])
    return (
        db.query(PurchaseOrder)
        .order_by(PurchaseOrder.id.desc())
        .all()
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager", "Warehouse Staff"])

    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(404, "Purchase order not found")
    return po


@router.put("/{po_id}/approve", response_model=PurchaseOrderResponse)
def approve_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager"])

    po = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.id == po_id)
        .with_for_update()
        .first()
    )
    if not po:
        raise HTTPException(404, "Purchase order not found")
    if po.status != "Draft":
        raise HTTPException(400, "Only Draft purchase orders can be approved")

    supplier = db.query(Supplier).filter(Supplier.id == po.supplier_id).first()
    if not supplier or not supplier.is_active:
        raise HTTPException(400, "Supplier is missing or inactive")

    po.status = "Approved"
    db.commit()
    db.refresh(po)
    return po


@router.post("/{po_id}/receive", response_model=PurchaseOrderResponse)
def receive_order(
    po_id: int,
    data: PurchaseOrderReceive,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager", "Warehouse Staff"])

    # Ensure this attribute matches your actual authenticated User model.
    user_id = user.id

    return receive_purchase_order(
        db=db,
        po_id=po_id,
        received_items=data.items,
        user_id=user_id,
    )


@router.put("/{po_id}/cancel", response_model=PurchaseOrderResponse)
def cancel_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager"])

    po = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.id == po_id)
        .with_for_update()
        .first()
    )
    if not po:
        raise HTTPException(404, "Purchase order not found")

    if po.status not in ("Draft", "Approved"):
        raise HTTPException(
            400,
            "Only Draft or Approved orders can be cancelled",
        )

    if any(item.quantity_received > 0 for item in po.items):
        raise HTTPException(
            400,
            "Orders with received goods cannot be cancelled",
        )

    po.status = "Cancelled"
    db.commit()
    db.refresh(po)
    return po