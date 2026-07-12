from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.permissions import ModuleEnum, ActionEnum
from app.schemas.trip import (
    TripCreate,
    TripUpdate,
    TripCompleteRequest,
    TripCancelRequest,
    TripResponse
)
from app.services.trip import TripService

router = APIRouter()


@router.post(
    "",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ModuleEnum.trips, ActionEnum.create))]
)
async def create_trip(
    obj_in: TripCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new trip in draft status. Driver only."""
    return await TripService.create(db, obj_in)


@router.get(
    "",
    response_model=List[TripResponse],
    dependencies=[Depends(require_permission(ModuleEnum.trips, ActionEnum.read))]
)
async def list_trips(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all trips. All authenticated roles can view."""
    return await TripService.get_multi(db, skip=skip, limit=limit, status_filter=status_filter)


@router.get(
    "/{id}",
    response_model=TripResponse,
    dependencies=[Depends(require_permission(ModuleEnum.trips, ActionEnum.read))]
)
async def get_trip(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get trip details by ID. All authenticated roles can view."""
    trip = await TripService.get(db, id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip with ID {id} not found."
        )
    return trip


@router.put(
    "/{id}",
    response_model=TripResponse,
    dependencies=[Depends(require_permission(ModuleEnum.trips, ActionEnum.update))]
)
async def update_trip(
    id: int,
    obj_in: TripUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update trip details (only allowed in draft status). Driver only."""
    trip = await TripService.get(db, id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip with ID {id} not found."
        )
    return await TripService.update(db, db_obj=trip, obj_in=obj_in)


@router.post(
    "/{id}/dispatch",
    response_model=TripResponse,
    dependencies=[Depends(require_permission(ModuleEnum.trips, ActionEnum.update))]
)
async def dispatch_trip(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Dispatch a trip. Driver only."""
    return await TripService.dispatch(db, id)


@router.post(
    "/{id}/complete",
    response_model=TripResponse,
    dependencies=[Depends(require_permission(ModuleEnum.trips, ActionEnum.update))]
)
async def complete_trip(
    id: int,
    req: TripCompleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Complete an active dispatched trip. Driver only."""
    return await TripService.complete(db, id, req)


@router.post(
    "/{id}/cancel",
    response_model=TripResponse,
    dependencies=[Depends(require_permission(ModuleEnum.trips, ActionEnum.update))]
)
async def cancel_trip(
    id: int,
    req: TripCancelRequest,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a trip. Driver only."""
    return await TripService.cancel(db, id, req)
