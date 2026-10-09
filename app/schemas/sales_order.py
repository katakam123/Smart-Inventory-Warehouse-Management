from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SalesOrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class SalesOrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    items: List[SalesOrderItemCreate] = Field(min_length=1)


class SalesOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class SalesOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    so_number: str
    customer_id: int
    warehouse_id: int
    subtotal: Decimal
    tax_amount: Decimal
    grand_total: Decimal
    status: str
    courier_name: Optional[str]
    tracking_number: Optional[str]
    dispatched_at: Optional[datetime]
    delivered_at: Optional[datetime]
    items: List[SalesOrderItemResponse]


class DispatchDetails(BaseModel):
    courier_name: str = Field(min_length=1, max_length=100)
    tracking_number: str = Field(min_length=1, max_length=100)