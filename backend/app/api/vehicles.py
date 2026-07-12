from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.permissions import ModuleEnum, ActionEnum
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from app.services.vehicle import VehicleService
from app.services.finance import FinanceService

router = APIRouter()


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ModuleEnum.vehicles, ActionEnum.create))]
)
async def create_vehicle(
    obj_in: VehicleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new vehicle. Fleet Manager only."""
    return await VehicleService.create(db, obj_in)


@router.get(
    "",
    response_model=List[VehicleResponse],
    dependencies=[Depends(require_permission(ModuleEnum.vehicles, ActionEnum.read))]
)
async def list_vehicles(
    skip: int = 0,
    limit: int = 100,
    region: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List vehicles. All authenticated roles can view."""
    return await VehicleService.get_multi(db, skip=skip, limit=limit, region=region)


@router.get(
    "/{id}",
    response_model=VehicleResponse,
    dependencies=[Depends(require_permission(ModuleEnum.vehicles, ActionEnum.read))]
)
async def get_vehicle(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get vehicle details. All authenticated roles can view."""
    vehicle = await VehicleService.get(db, id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {id} not found."
        )
    return vehicle


@router.get(
    "/{id}/costs",
    dependencies=[Depends(require_permission(ModuleEnum.expenses, ActionEnum.read))]
)
async def get_vehicle_operational_costs(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve total operational costs for a vehicle (fuel + maintenance + other expenses)."""
    vehicle = await VehicleService.get(db, id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {id} not found."
        )
    return await FinanceService.get_total_operational_cost(db, id)


@router.put(
    "/{id}",
    response_model=VehicleResponse,
    dependencies=[Depends(require_permission(ModuleEnum.vehicles, ActionEnum.update))]
)
async def update_vehicle(
    id: int,
    obj_in: VehicleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update vehicle. Fleet Manager only."""
    vehicle = await VehicleService.get(db, id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {id} not found."
        )
    return await VehicleService.update(db, db_obj=vehicle, obj_in=obj_in)


@router.delete(
    "/{id}",
    response_model=VehicleResponse,
    dependencies=[Depends(require_permission(ModuleEnum.vehicles, ActionEnum.delete))]
)
async def delete_vehicle(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete/remove a vehicle registry. Fleet Manager only."""
    vehicle = await VehicleService.get(db, id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {id} not found."
        )
    return await VehicleService.remove(db, id)
