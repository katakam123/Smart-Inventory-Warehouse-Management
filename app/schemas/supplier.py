from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SupplierCreate(BaseModel):
    supplier_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    gst_number: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = None
    lead_time_days: int = Field(default=7, ge=0, le=365)
    is_active: bool = True


class SupplierUpdate(BaseModel):
    supplier_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    gst_number: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = None
    lead_time_days: Optional[int] = Field(default=None, ge=0, le=365)
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_code: str
    name: str
    email: EmailStr
    phone: Optional[str]
    gst_number: Optional[str]
    address: Optional[str]
    lead_time_days: int
    is_active: bool