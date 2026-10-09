
from decimal import Decimal
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ReturnItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class ReturnCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)
    items: List[ReturnItemCreate] = Field(min_length=1)


class ReturnItemInspection(BaseModel):
    item_id: int = Field(gt=0)
    condition: Literal["Good", "Damaged"]


class ReturnInspection(BaseModel):
    items: List[ReturnItemInspection] = Field(min_length=1)


class ReturnReject(BaseModel):
    rejection_reason: str = Field(min_length=3, max_length=2000)


class ReturnItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    condition: Optional[str]
    original_unit_price: Decimal
    refund_amount: Decimal


class ReturnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    so_id: int
    reason: str
    status: str
    refund_amount: Decimal
    rejection_reason: Optional[str]
    created_at: Optional[datetime] = None
    items: List[ReturnItemResponse]