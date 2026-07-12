from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.permissions import ModuleEnum, ActionEnum
from app.schemas.reports import (
    FuelEfficiencyReportItem,
    FleetUtilizationReportItem,
    OperationalCostReportItem,
    VehicleROIReportItem
)
from app.services.reports import ReportsService

router = APIRouter()


@router.get(
    "/fuel-efficiency",
    response_model=List[FuelEfficiencyReportItem],
    dependencies=[Depends(require_permission(ModuleEnum.reports, ActionEnum.read))]
)
async def get_fuel_efficiency(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve fuel efficiency report per vehicle. Fleet Manager / Financial Analyst only."""
    return await ReportsService.get_fuel_efficiency_report(db, start_date, end_date)


@router.get(
    "/utilization",
    response_model=List[FleetUtilizationReportItem],
    dependencies=[Depends(require_permission(ModuleEnum.reports, ActionEnum.read))]
)
async def get_fleet_utilization(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve daily fleet utilization report. Fleet Manager / Financial Analyst only."""
    if not start_date or not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    return await ReportsService.get_fleet_utilization_report(db, start_date, end_date)


@router.get(
    "/operational-cost",
    response_model=List[OperationalCostReportItem],
    dependencies=[Depends(require_permission(ModuleEnum.reports, ActionEnum.read))]
)
async def get_operational_cost(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve operational cost report per vehicle. Fleet Manager / Financial Analyst only."""
    return await ReportsService.get_operational_cost_report(db, start_date, end_date)


@router.get(
    "/vehicle-roi",
    response_model=List[VehicleROIReportItem],
    dependencies=[Depends(require_permission(ModuleEnum.reports, ActionEnum.read))]
)
async def get_vehicle_roi(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve ROI report per vehicle. Fleet Manager / Financial Analyst only."""
    return await ReportsService.get_vehicle_roi_report(db, start_date, end_date)


@router.get(
    "/export",
    dependencies=[Depends(require_permission(ModuleEnum.reports, ActionEnum.read))]
)
async def export_report(
    report_type: str = Query(..., pattern="^(fuel-efficiency|utilization|operational-cost|vehicle-roi)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Export specified report as a CSV file. Fleet Manager / Financial Analyst only."""
    csv_gen = ReportsService.export_to_csv(db, report_type, start_date, end_date)
    return StreamingResponse(
        csv_gen,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"}
    )
