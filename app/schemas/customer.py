from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    customer_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=500)
    credit_limit: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_active: bool = True


class CustomerUpdate(BaseModel):
    customer_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=500)
    credit_limit: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_code: str
    name: str
    email: EmailStr
    phone: Optional[str]
    address: Optional[str]
    credit_limit: Decimal
    is_active: bool