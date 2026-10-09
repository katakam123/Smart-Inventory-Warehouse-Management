
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text
)

from app.database import Base


class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(
        Integer, ForeignKey("warehouses.id"), nullable=False
    )
    product_id = Column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    requested_by = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    reviewed_by = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    adjustment_type = Column(String(20), nullable=False)
    reason = Column(String(30), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String(20), default="Pending", nullable=False)
    request_notes = Column(Text, nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)