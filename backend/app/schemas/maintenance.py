from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from app.models.maintenance import MaintenanceStatusEnum, MaintenanceTypeEnum


class MaintenanceLogCreate(BaseModel):
    vehicle_id: int = Field(..., ge=1)
    maintenance_type: MaintenanceTypeEnum
    description: str = Field(..., min_length=1, max_length=1000)
    cost: Optional[Decimal] = Field(None, ge=Decimal("0"))
    started_at: Optional[datetime] = None


class MaintenanceLogUpdate(BaseModel):
    maintenance_type: Optional[MaintenanceTypeEnum] = None
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    cost: Optional[Decimal] = Field(None, ge=Decimal("0"))

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "MaintenanceLogUpdate":
        update_data = self.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("At least one field must be provided for update.")
        return self


class MaintenanceLogCloseRequest(BaseModel):
    cost: Optional[Decimal] = Field(None, ge=Decimal("0"))
    notes: Optional[str] = Field(None, max_length=1000)


class MaintenanceLogResponse(BaseModel):
    id: int
    vehicle_id: int
    maintenance_type: MaintenanceTypeEnum
    description: str
    cost: Optional[Decimal]
    status: MaintenanceStatusEnum
    started_at: datetime
    closed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
