from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing_extensions import Literal

from app.models.user import RoleEnum


class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    full_name: str = Field(..., min_length=1, max_length=150)
    role: RoleEnum


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, min_length=1, max_length=150)
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "UserUpdate":
        update_data = self.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("At least one field must be provided for update.")
        return self


class UserResponse(BaseModel):
    id: int = Field(..., ge=1)
    email: EmailStr
    full_name: str
    role: RoleEnum
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    refresh_token: str

