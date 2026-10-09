from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):

    username: str
    email: EmailStr
    password: str
    role: str = "Warehouse Staff"
    warehouse_id: int | None = None


class UserLogin(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)

class UserResponse(BaseModel):

    id: int
    username: str
    email: EmailStr
    role: str
    warehouse_id: int | None
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):

    access_token: str
    token_type: str