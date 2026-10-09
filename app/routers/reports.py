
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/reports",
    tags=["Inventory & Sales Reports"],
)


def check_report_access(current_user):
    if current_user.role not in ["Admin", "Inventory Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only Admin and Inventory Manager can access reports",
        )


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_report_access(current_user)
    # TODO: Add dashboard database queries.
    return {"message": "Dashboard report endpoint is ready"}


@router.get("/stock-valuation")
def stock_valuation(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_report_access(current_user)
    # TODO: Calculate stock value grouped by warehouse.
    return {"message": "Stock valuation endpoint is ready"}


@router.get("/low-stock")
def low_stock(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_report_access(current_user)
    # TODO: Find products below their reorder level.
    return {"message": "Low-stock report endpoint is ready"}


@router.get("/sales")
def sales_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_report_access(current_user)

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date",
        )

    # TODO: Calculate sales count, revenue, and returns.
    return {
        "start_date": start_date,
        "end_date": end_date,
        "message": "Sales report endpoint is ready",
    }


@router.get("/top-products")
def top_products(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_report_access(current_user)
    # TODO: Group sales items by product and return the top 10.
    return {"message": "Top-products endpoint is ready"}


@router.get("/dead-stock")
def dead_stock(
    days: int = Query(default=90, ge=1, le=3650),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_report_access(current_user)
    # TODO: Find products without sales during the selected period.
    return {"days_without_sales": days, "message": "Dead-stock endpoint is ready"}


@router.get("/supplier-performance")
def supplier_performance(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_report_access(current_user)
    # TODO: Calculate on-time deliveries for each supplier.
    return {"message": "Supplier-performance endpoint is ready"}