from decimal import Decimal
from typing import Union
from pydantic import BaseModel


class FuelEfficiencyReportItem(BaseModel):
    vehicle_id: int
    registration_number: str
    total_distance: float
    total_fuel_consumed: float
    fuel_efficiency: Union[float, str]

    class Config:
        from_attributes = True


class FleetUtilizationReportItem(BaseModel):
    date: str
    utilization_pct: float

    class Config:
        from_attributes = True


class OperationalCostReportItem(BaseModel):
    vehicle_id: int
    registration_number: str
    fuel_cost: Decimal
    maintenance_cost: Decimal
    other_expense_cost: Decimal
    total_cost: Decimal

    class Config:
        from_attributes = True


class VehicleROIReportItem(BaseModel):
    vehicle_id: int
    registration_number: str
    acquisition_cost: Decimal
    revenue: Union[Decimal, str]
    fuel_cost: Decimal
    maintenance_cost: Decimal
    roi: Union[float, str]

    class Config:
        from_attributes = True
