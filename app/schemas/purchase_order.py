from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity_ordered: int = Field(gt=0)
    unit_cost: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class PurchaseOrderCreate(BaseModel):
    supplier_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    expected_delivery_date: Optional[date] = None
    items: List[PurchaseOrderItemCreate] = Field(min_length=1)


class PurchaseOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity_ordered: int
    quantity_received: int
    unit_cost: Decimal


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    po_number: str
    supplier_id: int
    warehouse_id: int
    expected_delivery_date: date
    received_at: Optional[datetime]
    total_amount: Decimal
    status: str
    items: List[PurchaseOrderItemResponse]


class ReceiveItem(BaseModel):
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class PurchaseOrderReceive(BaseModel):
    items: List[ReceiveItem] = Field(min_length=1)