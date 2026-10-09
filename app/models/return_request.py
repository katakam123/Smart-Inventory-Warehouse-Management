
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Numeric, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True)
    so_id = Column(
        Integer,
        ForeignKey("sales_orders.id"),
        nullable=False,
        index=True
    )
    reason = Column(Text, nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default="Requested",
        index=True
    )
    refund_amount = Column(Numeric(12, 2), nullable=False, default=0)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship(
        "ReturnItem",
        back_populates="return_request",
        cascade="all, delete-orphan"
    )


class ReturnItem(Base):
    __tablename__ = "return_items"

    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(
        Integer,
        ForeignKey("return_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )
    quantity = Column(Integer, nullable=False)
    condition = Column(String(20), nullable=True)
    original_unit_price = Column(Numeric(12, 2), nullable=False)
    refund_amount = Column(Numeric(12, 2), nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_return_item_quantity"),
    )

    return_request = relationship(
        "ReturnRequest",
        back_populates="items"
    )