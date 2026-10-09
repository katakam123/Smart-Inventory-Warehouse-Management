from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    warehouse_id: int
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int

    model_config = ConfigDict(from_attributes=True)


class StockMovementResponse(BaseModel):
    id: int
    product_id: int
    warehouse_id: int
    movement_type: str
    quantity: int
    reference_id: Optional[int]
    balance_after: int
    performed_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)