from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.permissions import ModuleEnum, ActionEnum
from app.schemas.maintenance import (
    MaintenanceLogCreate,
    MaintenanceLogUpdate,
    MaintenanceLogCloseRequest,
    MaintenanceLogResponse
)
from app.services.maintenance import MaintenanceService

router = APIRouter()


@router.post(
    "",
    response_model=MaintenanceLogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ModuleEnum.maintenance, ActionEnum.create))]
)
async def create_maintenance_log(
    obj_in: MaintenanceLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new active maintenance log. Fleet Manager only."""
    return await MaintenanceService.create(db, obj_in)


@router.get(
    "",
    response_model=List[MaintenanceLogResponse],
    dependencies=[Depends(require_permission(ModuleEnum.maintenance, ActionEnum.read))]
)
async def list_maintenance_logs(
    skip: int = 0,
    limit: int = 100,
    vehicle_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List maintenance logs. Fleet Managers, Safety Officers, and Financial Analysts can view."""
    return await MaintenanceService.get_multi(db, skip=skip, limit=limit, vehicle_id=vehicle_id)


@router.get(
    "/{id}",
    response_model=MaintenanceLogResponse,
    dependencies=[Depends(require_permission(ModuleEnum.maintenance, ActionEnum.read))]
)
async def get_maintenance_log(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get maintenance log details by ID. Fleet Managers, Safety Officers, and Financial Analysts can view."""
    log = await MaintenanceService.get(db, id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance log with ID {id} not found."
        )
    return log


@router.put(
    "/{id}",
    response_model=MaintenanceLogResponse,
    dependencies=[Depends(require_permission(ModuleEnum.maintenance, ActionEnum.update))]
)
async def update_maintenance_log(
    id: int,
    obj_in: MaintenanceLogUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update active maintenance log details. Fleet Manager only."""
    log = await MaintenanceService.get(db, id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance log with ID {id} not found."
        )
    return await MaintenanceService.update(db, db_obj=log, obj_in=obj_in)


@router.post(
    "/{id}/close",
    response_model=MaintenanceLogResponse,
    dependencies=[Depends(require_permission(ModuleEnum.maintenance, ActionEnum.update))]
)
async def close_maintenance_log(
    id: int,
    req: MaintenanceLogCloseRequest,
    db: AsyncSession = Depends(get_db)
):
    """Close an active maintenance log. Fleet Manager only."""
    return await MaintenanceService.close(db, id, req)
