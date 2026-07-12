from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission, get_current_user
from app.core.permissions import ModuleEnum, ActionEnum
from app.models.user import User
from app.schemas.fuel_log import FuelLogCreate, FuelLogResponse
from app.services.finance import FinanceService

router = APIRouter()


@router.post(
    "",
    response_model=FuelLogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ModuleEnum.expenses, ActionEnum.create))]
)
async def create_fuel_log(
    obj_in: FuelLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new fuel log. Driver, Fleet Manager, and Financial Analyst can create."""
    return await FinanceService.create_fuel_log(db, obj_in=obj_in, created_by=current_user.id)


@router.get(
    "",
    response_model=List[FuelLogResponse],
    dependencies=[Depends(require_permission(ModuleEnum.expenses, ActionEnum.read))]
)
async def list_fuel_logs(
    skip: int = 0,
    limit: int = 100,
    vehicle_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List fuel logs. All authenticated roles can view."""
    return await FinanceService.get_fuel_logs(db, skip=skip, limit=limit, vehicle_id=vehicle_id)
