from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, index=True)
    so_number = Column(String(30), unique=True, nullable=False, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
    )
    warehouse_id = Column(
        Integer,
        ForeignKey("warehouses.id"),
        nullable=False,
    )

    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    grand_total = Column(Numeric(12, 2), nullable=False, default=0)

    status = Column(String(30), nullable=False, default="Draft")

    courier_name = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="sales_orders")
    warehouse = relationship("Warehouse")
    items = relationship(
        "SalesOrderItem",
        back_populates="sales_order",
        cascade="all, delete-orphan",
    )


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(Integer, primary_key=True, index=True)

    sales_order_id = Column(
        Integer,
        ForeignKey("sales_orders.id"),
        nullable=False,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )
    tracking_number = Column(
    String(100),
    unique=True,
    nullable=True,
    )
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    sales_order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product")