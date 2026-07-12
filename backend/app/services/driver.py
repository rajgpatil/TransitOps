from typing import List, Optional
from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.driver import Driver, DriverStatusEnum
from app.schemas.driver import DriverCreate, DriverUpdate


class DriverService:
    @staticmethod
    async def create(db: AsyncSession, obj_in: DriverCreate) -> Driver:
        # Check uniqueness of license_number
        stmt = select(Driver).where(Driver.license_number == obj_in.license_number)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Driver with license number '{obj_in.license_number}' already exists."
            )

        db_obj = Driver(
            name=obj_in.name,
            license_number=obj_in.license_number,
            license_category=obj_in.license_category,
            license_expiry=obj_in.license_expiry,
            contact_number=obj_in.contact_number,
            safety_score=obj_in.safety_score,
            status=obj_in.status
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get(db: AsyncSession, id: int) -> Optional[Driver]:
        stmt = select(Driver).where(Driver.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[DriverStatusEnum] = None
    ) -> List[Driver]:
        stmt = select(Driver)
        if status_filter:
            stmt = stmt.where(Driver.status == status_filter)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_available(db: AsyncSession) -> List[Driver]:
        """Retrieve drivers with available status and non-expired license."""
        today = date.today()
        stmt = select(Driver).where(
            and_(
                Driver.status == DriverStatusEnum.available,
                Driver.license_expiry >= today
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, db_obj: Driver, obj_in: DriverUpdate) -> Driver:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def remove(db: AsyncSession, id: int) -> Optional[Driver]:
        db_obj = await DriverService.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
