from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.vehicle import VehicleStatusEnum, VehicleTypeEnum
from app.schemas.dashboard import DashboardKPIsResponse, ChartDataResponse
from app.services.dashboard import DashboardService

router = APIRouter()


@router.get("/kpis", response_model=DashboardKPIsResponse)
async def get_kpis(
    vehicle_type: Optional[VehicleTypeEnum] = Query(None),
    vehicle_status: Optional[VehicleStatusEnum] = Query(None),
    region: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve real-time fleet KPIs (automatically role-filtered)."""
    return await DashboardService.get_kpis(
        db=db,
        current_user=current_user,
        vehicle_type=vehicle_type,
        vehicle_status=vehicle_status,
        region=region
    )


@router.get("/charts", response_model=ChartDataResponse)
async def get_charts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve chart/trends data (automatically role-filtered)."""
    return await DashboardService.get_charts(db=db, current_user=current_user)
