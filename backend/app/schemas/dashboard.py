from decimal import Decimal
from typing import Optional, Union, List
from pydantic import BaseModel


class DashboardKPIsResponse(BaseModel):
    active_vehicles_count: Optional[int] = None
    available_vehicles_count: Optional[int] = None
    vehicles_in_shop_count: Optional[int] = None
    active_trips_count: Optional[int] = None
    pending_trips_count: Optional[int] = None
    drivers_on_duty_count: Optional[int] = None
    fleet_utilization_pct: Optional[Union[float, str]] = None
    fuel_efficiency: Optional[Union[float, str]] = None
    operational_cost: Optional[Union[Decimal, str]] = None
    roi: Optional[Union[float, str]] = None

    class Config:
        from_attributes = True


class TripStatusBreakdownItem(BaseModel):
    status: str
    count: int


class CostTrendItem(BaseModel):
    month: str
    fuel_cost: Decimal
    maintenance_cost: Decimal
    other_expense_cost: Decimal


class UtilizationTrendItem(BaseModel):
    date: str
    utilization_pct: float


class ChartDataResponse(BaseModel):
    trip_status_breakdown: List[TripStatusBreakdownItem]
    cost_trend: List[CostTrendItem]
    utilization_trend: List[UtilizationTrendItem]

    class Config:
        from_attributes = True
