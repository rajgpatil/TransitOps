from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from app.models.trip import TripStatusEnum
from app.schemas.vehicle import VehicleResponse
from app.schemas.driver import DriverResponse


class TripBase(BaseModel):
    source: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    vehicle_id: int = Field(..., ge=1)
    driver_id: int = Field(..., ge=1)
    cargo_weight: Decimal = Field(..., ge=Decimal("0"), le=Decimal("100000"))
    planned_distance: Decimal = Field(..., gt=Decimal("0"))
    revenue: Optional[Decimal] = Field(None, ge=Decimal("0"))


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    source: Optional[str] = Field(None, min_length=1, max_length=255)
    destination: Optional[str] = Field(None, min_length=1, max_length=255)
    vehicle_id: Optional[int] = Field(None, ge=1)
    driver_id: Optional[int] = Field(None, ge=1)
    cargo_weight: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("100000"))
    planned_distance: Optional[Decimal] = Field(None, gt=Decimal("0"))
    revenue: Optional[Decimal] = Field(None, ge=Decimal("0"))

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "TripUpdate":
        update_data = self.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("At least one field must be provided for update.")
        return self


class TripCompleteRequest(BaseModel):
    actual_distance: Decimal = Field(..., gt=Decimal("0"))
    fuel_consumed: Decimal = Field(..., gt=Decimal("0"))
    final_odometer: Decimal = Field(..., ge=Decimal("0"))
    revenue: Optional[Decimal] = Field(None, ge=Decimal("0"))


class TripCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class TripResponse(BaseModel):
    id: int
    source: str
    destination: str
    vehicle_id: int
    driver_id: int
    cargo_weight: Decimal
    planned_distance: Decimal
    actual_distance: Optional[Decimal]
    fuel_consumed: Optional[Decimal]
    final_odometer: Optional[Decimal]
    revenue: Optional[Decimal]
    status: TripStatusEnum
    dispatched_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancel_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Embedded summary objects
    vehicle: Optional[VehicleResponse] = None
    driver: Optional[DriverResponse] = None

    class Config:
        from_attributes = True
