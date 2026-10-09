from fastapi import FastAPI

from app.routers import (
    auth,
    categories,
    products,
    warehouses, 
    inventory,
    suppliers,
    purchase_orders,
    customers,
    sales_orders,
    order_fulfillment,
    returns,
    audit_logs,
    reports,
    transfers,
    adjustments,
)


app = FastAPI(
    title="Smart Inventory & Warehouse Management System",
    description=(
        "End-to-end inventory and warehouse "
        "management backend"
    ),
    version="1.0.0"
)


app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(warehouses.router)
app.include_router(inventory.router)
app.include_router(suppliers.router)
app.include_router(purchase_orders.router)
app.include_router(customers.router)
app.include_router(sales_orders.router)
app.include_router(order_fulfillment.router)
app.include_router(returns.router)
app.include_router(audit_logs.router)
app.include_router(reports.router)
app.include_router(transfers.router)
app.include_router(adjustments.router)
@app.get("/")
def root():

    return {
        "message": (
            "Smart Inventory & Warehouse "
            "Management API is running"
        )
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }