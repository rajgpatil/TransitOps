from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.maintenance import MaintenanceLog, MaintenanceStatusEnum
from app.models.vehicle import Vehicle, VehicleStatusEnum
from app.schemas.maintenance import MaintenanceLogCreate, MaintenanceLogUpdate, MaintenanceLogCloseRequest


class MaintenanceService:
    @staticmethod
    async def create(db: AsyncSession, obj_in: MaintenanceLogCreate) -> MaintenanceLog:
        # Load vehicle
        v_res = await db.execute(select(Vehicle).where(Vehicle.id == obj_in.vehicle_id))
        vehicle = v_res.scalar_one_or_none()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

        # Block maintenance on on_trip vehicles
        if vehicle.status == VehicleStatusEnum.on_trip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start maintenance on a vehicle that is currently on a trip."
            )

        # Set vehicle status to in_shop
        # Note: If it's already in_shop or retired, it stays as is (or changes retired to in_shop?
        # The prompt says: "retired vehicles stay retired". But creating a record for retired vehicle - does it set in_shop?
        # Typically retired vehicles cannot go back to shop, or if they do they stay retired when closing. Let's make sure if vehicle is retired we still allow log but keep it retired.)
        if vehicle.status != VehicleStatusEnum.retired:
            vehicle.status = VehicleStatusEnum.in_shop

        started_at = obj_in.started_at or datetime.now()

        db_obj = MaintenanceLog(
            vehicle_id=obj_in.vehicle_id,
            maintenance_type=obj_in.maintenance_type,
            description=obj_in.description,
            cost=obj_in.cost,
            started_at=started_at,
            status=MaintenanceStatusEnum.active
        )
        db.add(db_obj)
        db.add(vehicle)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get(db: AsyncSession, id: int) -> Optional[MaintenanceLog]:
        stmt = select(MaintenanceLog).where(MaintenanceLog.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        vehicle_id: Optional[int] = None
    ) -> List[MaintenanceLog]:
        stmt = select(MaintenanceLog)
        if vehicle_id:
            stmt = stmt.where(MaintenanceLog.vehicle_id == vehicle_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, db_obj: MaintenanceLog, obj_in: MaintenanceLogUpdate) -> MaintenanceLog:
        if db_obj.status != MaintenanceStatusEnum.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update a closed maintenance record."
            )

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def close(db: AsyncSession, id: int, req: MaintenanceLogCloseRequest) -> MaintenanceLog:
        db_obj = await MaintenanceService.get(db, id)
        if not db_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance log not found")

        if db_obj.status == MaintenanceStatusEnum.closed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Maintenance record is already closed."
            )

        # Update log details
        db_obj.status = MaintenanceStatusEnum.closed
        db_obj.closed_at = datetime.now()
        if req.cost is not None:
            db_obj.cost = req.cost
        if req.notes is not None:
            db_obj.notes = req.notes

        # Check for other active logs for the same vehicle
        stmt = select(func.count(MaintenanceLog.id)).where(
            and_(
                MaintenanceLog.vehicle_id == db_obj.vehicle_id,
                MaintenanceLog.status == MaintenanceStatusEnum.active,
                MaintenanceLog.id != db_obj.id
            )
        )
        count_res = await db.execute(stmt)
        active_count = count_res.scalar_one()

        # Update vehicle status if no active logs remain
        v_res = await db.execute(select(Vehicle).where(Vehicle.id == db_obj.vehicle_id))
        vehicle = v_res.scalar_one()

        if active_count == 0:
            if vehicle.status != VehicleStatusEnum.retired:
                vehicle.status = VehicleStatusEnum.available
            db.add(vehicle)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
