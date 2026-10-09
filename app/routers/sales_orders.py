from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.sales_order import SalesOrder
from app.schemas.sales_order import (
    SalesOrderCreate,
    SalesOrderResponse,
)
from app.services.sales_order_service import (
    create_sales_order,
    confirm_sales_order,
    cancel_sales_order,
)

router = APIRouter(prefix="/sales-orders", tags=["Sales Orders"])


def require_role(user):
    if user.role not in ["Admin", "Inventory Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only Admin or Inventory Manager can manage sales orders",
        )


@router.post(
    "",
    response_model=SalesOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    data: SalesOrderCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user)
    return create_sales_order(db, data)


@router.get("", response_model=list[SalesOrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user)
    return db.query(SalesOrder).order_by(SalesOrder.id.desc()).all()


@router.get("/{so_id}", response_model=SalesOrderResponse)
def get_order(
    so_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user)

    order = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not order:
        raise HTTPException(404, "Sales order not found")
    return order


@router.put("/{so_id}/confirm", response_model=SalesOrderResponse)
def confirm_order(
    so_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user)
    from app.services.sales_order_service import confirm_sales_order

    return confirm_sales_order(db, so_id)


@router.put("/{so_id}/cancel", response_model=SalesOrderResponse)
def cancel_order(
    so_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user)
    from app.services.sales_order_service import cancel_sales_order

    return cancel_sales_order(db, so_id)