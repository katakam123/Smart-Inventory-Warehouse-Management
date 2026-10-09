from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.sql import func

from app.database import Base


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    warehouse_id = Column(
        Integer,
        ForeignKey("warehouses.id"),
        nullable=False,
        index=True,
    )

    movement_type = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    reference_id = Column(Integer, nullable=True)
    balance_after = Column(Integer, nullable=False)
    performed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_stock_movement_quantity_positive",
        ),
        CheckConstraint(
            "balance_after >= 0",
            name="ck_stock_movement_balance_nonnegative",
        ),
    )