from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.vehicle import Vehicle, VehicleStatusEnum
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class VehicleService:
    @staticmethod
    async def create(db: AsyncSession, obj_in: VehicleCreate) -> Vehicle:
        # Normalize registration number to uppercase
        reg_num = obj_in.registration_number.strip().upper()
        
        # Check uniqueness
        stmt = select(Vehicle).where(Vehicle.registration_number == reg_num)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vehicle with registration number '{reg_num}' already exists."
            )

        db_obj = Vehicle(
            registration_number=reg_num,
            name=obj_in.name,
            type=obj_in.type,
            max_load_capacity=obj_in.max_load_capacity,
            odometer=obj_in.odometer,
            acquisition_cost=obj_in.acquisition_cost,
            region=obj_in.region,
            status=obj_in.status
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get(db: AsyncSession, id: int) -> Optional[Vehicle]:
        stmt = select(Vehicle).where(Vehicle.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        region: Optional[str] = None
    ) -> List[Vehicle]:
        stmt = select(Vehicle)
        if region:
            stmt = stmt.where(Vehicle.region == region)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, db_obj: Vehicle, obj_in: VehicleUpdate) -> Vehicle:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def remove(db: AsyncSession, id: int) -> Optional[Vehicle]:
        db_obj = await VehicleService.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
