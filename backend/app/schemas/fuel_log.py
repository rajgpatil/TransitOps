from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class FuelLogCreate(BaseModel):
    vehicle_id: int = Field(..., ge=1)
    trip_id: Optional[int] = Field(None, ge=1)
    liters: Decimal = Field(..., gt=Decimal("0"), le=Decimal("10000"))
    cost: Decimal = Field(..., gt=Decimal("0"))
    date: date
    odometer_at_fill: Optional[Decimal] = Field(None, ge=Decimal("0"))


class FuelLogUpdate(BaseModel):
    liters: Optional[Decimal] = Field(None, gt=Decimal("0"), le=Decimal("10000"))
    cost: Optional[Decimal] = Field(None, gt=Decimal("0"))
    date: Optional[date] = None
    odometer_at_fill: Optional[Decimal] = Field(None, ge=Decimal("0"))

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "FuelLogUpdate":
        update_data = self.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("At least one field must be provided for update.")
        return self


class FuelLogResponse(BaseModel):
    id: int
    vehicle_id: int
    trip_id: Optional[int]
    liters: Decimal
    cost: Decimal
    date: date
    odometer_at_fill: Optional[Decimal]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.strftime("%Y-%m-%d"),
        }
