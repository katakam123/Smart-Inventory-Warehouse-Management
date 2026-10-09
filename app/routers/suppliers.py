from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.supplier import Supplier
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


def require_role(user, allowed_roles):
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to perform this action",
        )


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager"])

    existing = db.query(Supplier).filter(
        (Supplier.supplier_code == data.supplier_code)
        | (Supplier.email == str(data.email))
    ).first()

    if existing:
        raise HTTPException(409, "Supplier code or email already exists")

    supplier = Supplier(**data.model_dump())
    db.add(supplier)

    try:
        db.commit()
        db.refresh(supplier)
        return supplier
    except Exception:
        db.rollback()
        raise HTTPException(409, "Could not create supplier; check unique fields")


@router.get("", response_model=list[SupplierResponse])
def list_suppliers(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager", "Warehouse Staff"])
    return db.query(Supplier).order_by(Supplier.id.desc()).all()


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager", "Warehouse Staff"])

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin", "Inventory Manager"])

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    changes = data.model_dump(exclude_unset=True)

    if changes.get("is_active") is False and supplier.is_active:
        require_role(user, ["Admin"])

        # Do not deactivate a supplier while an order is awaiting receipt.
        pending = any(
            po.status in ("Approved", "Partially Received")
            for po in supplier.purchase_orders
        )
        if pending:
            raise HTTPException(
                400,
                "Supplier has purchase orders awaiting receipt",
            )

    for key, value in changes.items():
        setattr(supplier, key, value)

    try:
        db.commit()
        db.refresh(supplier)
        return supplier
    except Exception:
        db.rollback()
        raise HTTPException(409, "Could not update supplier; check unique fields")


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["Admin"])

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    if supplier.purchase_orders:
        raise HTTPException(
            400,
            "Supplier has purchase order history; deactivate it instead",
        )

    db.delete(supplier)
    db.commit()
    return None