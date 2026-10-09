from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    __table_args__ = (
        Index(
            "uq_product_warehouse",
            "product_id",
            "warehouse_id",
            unique=True,
        ),
        CheckConstraint(
            "quantity_on_hand >= 0",
            name="ck_inventory_on_hand_nonnegative",
        ),
        CheckConstraint(
            "quantity_reserved >= 0",
            name="ck_inventory_reserved_nonnegative",
        ),
        CheckConstraint(
            "quantity_reserved <= quantity_on_hand",
            name="ck_inventory_reserved_lte_on_hand",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )

    warehouse_id = Column(
        Integer,
        ForeignKey("warehouses.id"),
        nullable=False,
    )

    quantity_on_hand = Column(
        Integer,
        nullable=False,
        default=0,
    )

    quantity_reserved = Column(
        Integer,
        nullable=False,
        default=0,
    )

    product = relationship("Product", back_populates="inventory")
    warehouse = relationship("Warehouse", back_populates="inventory")

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

