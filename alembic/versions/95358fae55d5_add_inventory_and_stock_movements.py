"""add inventory and stock movements

Revision ID: 95358fae55d5
Revises: 6ca16787a810
Create Date: 2026-10-09 13:17:59.867759
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# Revision identifiers
revision: str = "95358fae55d5"
down_revision: Union[str, Sequence[str], None] = "6ca16787a810"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep the existing uq_product_warehouse index.
    # It already enforces uniqueness for product_id + warehouse_id.
    # Do not drop it or create a duplicate unique constraint.

    # Make performed_by mandatory.
    # Existing rows must have valid user IDs before this can succeed.
    op.alter_column(
        "stock_movements",
        "performed_by",
        existing_type=mysql.INTEGER(),
        nullable=False,
    )

    # Add indexes only if they do not already exist.
    op.create_index(
        "ix_stock_movements_created_at",
        "stock_movements",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_stock_movements_movement_type",
        "stock_movements",
        ["movement_type"],
        unique=False,
    )
    op.create_index(
        "ix_stock_movements_product_id",
        "stock_movements",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_stock_movements_warehouse_id",
        "stock_movements",
        ["warehouse_id"],
        unique=False,
    )

    # Give the foreign key a stable name.
    op.create_foreign_key(
        "fk_stock_movements_performed_by_users",
        "stock_movements",
        "users",
        ["performed_by"],
        ["id"],
    )


def downgrade() -> None:
    # Remove only objects added by this migration.
    op.drop_constraint(
        "fk_stock_movements_performed_by_users",
        "stock_movements",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_stock_movements_warehouse_id",
        table_name="stock_movements",
    )
    op.drop_index(
        "ix_stock_movements_product_id",
        table_name="stock_movements",
    )
    op.drop_index(
        "ix_stock_movements_movement_type",
        table_name="stock_movements",
    )
    op.drop_index(
        "ix_stock_movements_created_at",
        table_name="stock_movements",
    )

    op.alter_column(
        "stock_movements",
        "performed_by",
        existing_type=mysql.INTEGER(),
        nullable=True,
    )

