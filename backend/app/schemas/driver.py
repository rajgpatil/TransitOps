from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator, computed_field

from app.models.driver import DriverStatusEnum, LicenseCategoryEnum
from app.core.utils import is_date_expired


class DriverBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    license_number: str = Field(..., min_length=1, max_length=30)
    license_category: LicenseCategoryEnum
    license_expiry: date
    contact_number: str = Field(..., min_length=7, max_length=20, pattern=r"^[+]?[0-9\s\-()]+$")
    safety_score: Decimal = Field(default=Decimal("100.00"), ge=Decimal("0"), le=Decimal("100"))
    status: DriverStatusEnum = DriverStatusEnum.available


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    license_category: Optional[LicenseCategoryEnum] = None
    license_expiry: Optional[date] = None
    contact_number: Optional[str] = Field(None, min_length=7, max_length=20, pattern=r"^[+]?[0-9\s\-()]+$")
    safety_score: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("100"))
    status: Optional[DriverStatusEnum] = None

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "DriverUpdate":
        update_data = self.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("At least one field must be provided for update.")
        return self


class DriverResponse(BaseModel):
    id: int
    name: str
    license_number: str
    license_category: LicenseCategoryEnum
    license_expiry: date
    contact_number: str
    safety_score: Decimal
    status: DriverStatusEnum
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_license_expired(self) -> bool:
        return is_date_expired(self.license_expiry)

    @computed_field
    @property
    def is_assignable(self) -> bool:
        return self.status == DriverStatusEnum.available and not self.is_license_expired

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.strftime("%Y-%m-%d"),
        }
        # In Pydantic v2, date is serialized to ISO YYYY-MM-DD by default.
