
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


class StockTransfer(Base):
    __tablename__ = "stock_transfers"

    id = Column(Integer, primary_key=True, index=True)
    source_warehouse_id = Column(
        Integer, ForeignKey("warehouses.id"), nullable=False
    )
    destination_warehouse_id = Column(
        Integer, ForeignKey("warehouses.id"), nullable=False
    )
    status = Column(
        String(20), nullable=False, default="Pending"
    )
    created_by = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    dispatched_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship(
        "StockTransferItem",
        back_populates="transfer",
        cascade="all, delete-orphan",
    )


class StockTransferItem(Base):
    __tablename__ = "stock_transfer_items"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(
        Integer,
        ForeignKey("stock_transfers.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id = Column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    requested_quantity = Column(Integer, nullable=False)
    dispatched_quantity = Column(Integer, nullable=True)
    received_quantity = Column(Integer, nullable=True)
    shortage_quantity = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)

    transfer = relationship(
        "StockTransfer", back_populates="items"
    )