from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)

router = APIRouter(prefix="/customers", tags=["Customers"])


def require_role(user):
    if user.role not in ["Admin", "Inventory Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only Admin or Inventory Manager can manage customers",
        )


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user)

    duplicate = db.query(Customer).filter(
        (Customer.customer_code == data.customer_code)
        | (Customer.email == str(data.email))
    ).first()

    if duplicate:
        raise HTTPException(409, "Customer code or email already exists")

    customer = Customer(**data.model_dump())
    db.add(customer)

    try:
        db.commit()
        db.refresh(customer)
        return customer
    except Exception:
        db.rollback()
        raise HTTPException(409, "Unable to create customer; check unique fields")


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user)
    return db.query(Customer).order_by(Customer.id.desc()).all()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user)

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(404, "Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user)

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(404, "Customer not found")

    changes = data.model_dump(exclude_unset=True)

    # Check unique fields before updating.
    for field in ("customer_code", "email"):
        value = changes.get(field)
        if value is not None:
            duplicate = db.query(Customer).filter(
                getattr(Customer, field) == str(value),
                Customer.id != customer_id,
            ).first()
            if duplicate:
                raise HTTPException(409, f"{field} already exists")

    for field, value in changes.items():
        setattr(customer, field, value)

    try:
        db.commit()
        db.refresh(customer)
        return customer
    except Exception:
        db.rollback()
        raise HTTPException(409, "Unable to update customer")