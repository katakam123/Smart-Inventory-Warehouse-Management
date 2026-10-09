
from datetime import date

from sqlalchemy import (
    Column, Integer, String, Date, DateTime,
    ForeignKey, Numeric
)
from sqlalchemy.sql import func

from app.database import Base


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    warehouse_id = Column(
        Integer, ForeignKey("warehouses.id"), nullable=False
    )
    batch_number = Column(String(100), nullable=False)
    expiry_date = Column(Date, nullable=True)
    quantity_available = Column(Integer, nullable=False, default=0)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    created_at = Column(
        DateTime, server_default=func.now(), nullable=False
    )