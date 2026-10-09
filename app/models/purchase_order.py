from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(30), unique=True, nullable=False, index=True)

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=False,
    )
    warehouse_id = Column(
        Integer,
        ForeignKey("warehouses.id"),
        nullable=False,
    )

    expected_delivery_date = Column(Date, nullable=False)
    received_at = Column(DateTime, nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(30), nullable=False, default="Draft")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    supplier = relationship("Supplier", back_populates="purchase_orders")
    warehouse = relationship("Warehouse")
    items = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)

    purchase_order_id = Column(
        Integer,
        ForeignKey("purchase_orders.id"),
        nullable=False,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )

    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, nullable=False, default=0)
    unit_cost = Column(Numeric(12, 2), nullable=False)

    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="items",
    )
    product = relationship("Product")