from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from app.models.expense import ExpenseTypeEnum


class ExpenseCreate(BaseModel):
    vehicle_id: int = Field(..., ge=1)
    trip_id: Optional[int] = Field(None, ge=1)
    expense_type: ExpenseTypeEnum
    description: Optional[str] = Field(None, max_length=500)
    cost: Decimal = Field(..., gt=Decimal("0"))
    date: date


class ExpenseUpdate(BaseModel):
    expense_type: Optional[ExpenseTypeEnum] = None
    description: Optional[str] = Field(None, max_length=500)
    cost: Optional[Decimal] = Field(None, gt=Decimal("0"))
    date: Optional[date] = None

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "ExpenseUpdate":
        update_data = self.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("At least one field must be provided for update.")
        return self


class ExpenseResponse(BaseModel):
    id: int
    vehicle_id: int
    trip_id: Optional[int]
    expense_type: ExpenseTypeEnum
    description: Optional[str]
    cost: Decimal
    date: date
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.strftime("%Y-%m-%d"),
        }
