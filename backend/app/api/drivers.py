from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.permissions import ModuleEnum, ActionEnum
from app.models.driver import DriverStatusEnum
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from app.services.driver import DriverService

router = APIRouter()


@router.post(
    "",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ModuleEnum.drivers, ActionEnum.create))]
)
async def create_driver(
    obj_in: DriverCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new driver registry. Safety Officer only."""
    return await DriverService.create(db, obj_in)


@router.get(
    "/available",
    response_model=List[DriverResponse],
    dependencies=[Depends(require_permission(ModuleEnum.drivers, ActionEnum.read))]
)
async def list_available_drivers(
    db: AsyncSession = Depends(get_db)
):
    """List all available and assignable drivers (status available, license unexpired). All roles can view."""
    return await DriverService.get_available(db)


@router.get(
    "",
    response_model=List[DriverResponse],
    dependencies=[Depends(require_permission(ModuleEnum.drivers, ActionEnum.read))]
)
async def list_drivers(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[DriverStatusEnum] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all drivers. All authenticated roles can view."""
    return await DriverService.get_multi(db, skip=skip, limit=limit, status_filter=status_filter)


@router.get(
    "/{id}",
    response_model=DriverResponse,
    dependencies=[Depends(require_permission(ModuleEnum.drivers, ActionEnum.read))]
)
async def get_driver(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get driver details. All authenticated roles can view."""
    driver = await DriverService.get(db, id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {id} not found."
        )
    return driver


@router.put(
    "/{id}",
    response_model=DriverResponse,
    dependencies=[Depends(require_permission(ModuleEnum.drivers, ActionEnum.update))]
)
async def update_driver(
    id: int,
    obj_in: DriverUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update driver registry. Safety Officer and Fleet Manager only."""
    driver = await DriverService.get(db, id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {id} not found."
        )
    return await DriverService.update(db, db_obj=driver, obj_in=obj_in)


@router.delete(
    "/{id}",
    response_model=DriverResponse,
    dependencies=[Depends(require_permission(ModuleEnum.drivers, ActionEnum.delete))]
)
async def delete_driver(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a driver registry. Safety Officer only."""
    driver = await DriverService.get(db, id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {id} not found."
        )
    return await DriverService.remove(db, id)
