from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.warehouse import Warehouse
from app.models.inventory import Inventory
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
)
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/warehouses",
    tags=["Warehouse Management"],
)


def require_admin(current_user):
    role = getattr(current_user, "role", None)

    if str(role).lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can perform this operation",
        )


def get_warehouse_or_404(warehouse_id: int, db: Session):
    warehouse = (
        db.query(Warehouse)
        .filter(Warehouse.id == warehouse_id)
        .first()
    )

    if not warehouse:
        raise HTTPException(
            status_code=404,
            detail="Warehouse not found",
        )

    return warehouse


def get_total_stock(db: Session, warehouse_id: int) -> int:
    total = (
        db.query(func.coalesce(func.sum(Inventory.quantity), 0))
        .filter(Inventory.warehouse_id == warehouse_id)
        .scalar()
    )
    return int(total)


# POST /warehouses
@router.post(
    "",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_warehouse(
    data: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    existing = (
        db.query(Warehouse)
        .filter(Warehouse.warehouse_code == data.warehouse_code)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Warehouse code already exists",
        )

    warehouse = Warehouse(**data.model_dump())

    try:
        db.add(warehouse)
        db.commit()
        db.refresh(warehouse)
        return warehouse
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create warehouse",
        )


# GET /warehouses
@router.get("", response_model=list[WarehouseResponse])
def get_warehouses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Warehouse).all()


# GET /warehouses/{warehouse_id}
@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_warehouse_or_404(warehouse_id, db)


# PUT /warehouses/{warehouse_id}
@router.put("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    warehouse = get_warehouse_or_404(warehouse_id, db)
    changes = data.model_dump(exclude_unset=True)

    new_code = changes.get("warehouse_code")
    if new_code and new_code != warehouse.warehouse_code:
        duplicate = (
            db.query(Warehouse)
            .filter(
                Warehouse.warehouse_code == new_code,
                Warehouse.id != warehouse_id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="Warehouse code already exists",
            )

    total_stock = get_total_stock(db, warehouse_id)

    # A warehouse with stock cannot be deactivated.
    if changes.get("is_active") is False and total_stock > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate a warehouse that contains stock",
        )

    # Capacity cannot be reduced below current stock.
    new_capacity = changes.get("capacity", warehouse.capacity)
    if new_capacity < total_stock:
        raise HTTPException(
            status_code=400,
            detail=f"Capacity cannot be less than current stock ({total_stock})",
        )

    for field, value in changes.items():
        setattr(warehouse, field, value)

    try:
        db.commit()
        db.refresh(warehouse)
        return warehouse
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update warehouse",
        )


# DELETE /warehouses/{warehouse_id}
@router.delete("/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    warehouse = get_warehouse_or_404(warehouse_id, db)
    total_stock = get_total_stock(db, warehouse_id)

    if total_stock > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a warehouse that contains stock",
        )

    # Remove zero-stock inventory rows first to avoid foreign-key errors.
    db.query(Inventory).filter(
        Inventory.warehouse_id == warehouse_id
    ).delete(synchronize_session=False)

    try:
        db.delete(warehouse)
        db.commit()
        return {"message": "Warehouse deleted successfully"}
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not delete warehouse",
        )


# GET /warehouses/{warehouse_id}/inventory
@router.get("/{warehouse_id}/inventory")
def get_warehouse_inventory(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    warehouse = get_warehouse_or_404(warehouse_id, db)

    inventory_items = (
        db.query(Inventory)
        .filter(Inventory.warehouse_id == warehouse_id)
        .all()
    )

    return {
        "warehouse_id": warehouse.id,
        "warehouse_name": warehouse.name,
        "capacity": warehouse.capacity,
        "total_stock": get_total_stock(db, warehouse_id),
        "inventory": inventory_items,
    }