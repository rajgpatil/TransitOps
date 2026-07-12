from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator, field_validator

from app.models.vehicle import VehicleStatusEnum, VehicleTypeEnum


class VehicleBase(BaseModel):
    registration_number: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Z0-9\-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    type: VehicleTypeEnum
    max_load_capacity: Decimal = Field(..., gt=Decimal("0"), le=Decimal("100000"))
    odometer: Decimal = Field(..., ge=Decimal("0"))
    acquisition_cost: Decimal = Field(..., ge=Decimal("0"))
    region: Optional[str] = Field(None, max_length=100)
    status: VehicleStatusEnum = VehicleStatusEnum.available

    @field_validator("registration_number", mode="before")
    @classmethod
    def normalize_reg_number(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return v


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[VehicleTypeEnum] = None
    max_load_capacity: Optional[Decimal] = Field(None, gt=Decimal("0"), le=Decimal("100000"))
    odometer: Optional[Decimal] = Field(None, ge=Decimal("0"))
    acquisition_cost: Optional[Decimal] = Field(None, ge=Decimal("0"))
    region: Optional[str] = Field(None, max_length=100)
    status: Optional[VehicleStatusEnum] = None

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "VehicleUpdate":
        update_data = self.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("At least one field must be provided for update.")
        return self


class VehicleResponse(BaseModel):
    id: int
    registration_number: str
    name: str
    type: VehicleTypeEnum
    max_load_capacity: Decimal
    odometer: Decimal
    acquisition_cost: Decimal
    region: Optional[str]
    status: VehicleStatusEnum
    active_maintenance_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
