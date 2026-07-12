from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.trip import Trip, TripStatusEnum
from app.models.vehicle import Vehicle, VehicleStatusEnum
from app.models.driver import Driver, DriverStatusEnum
from app.schemas.trip import TripCreate, TripUpdate, TripCompleteRequest, TripCancelRequest
from app.core.utils import is_date_expired


class TripService:
    @staticmethod
    async def validate_resources(
        db: AsyncSession,
        vehicle_id: int,
        driver_id: int,
        cargo_weight: float,
        is_dispatch: bool = False
    ) -> tuple[Vehicle, Driver]:
        # Lock rows if this is a dispatch check to avoid race conditions
        if is_dispatch:
            v_stmt = select(Vehicle).where(Vehicle.id == vehicle_id).with_for_update()
            d_stmt = select(Driver).where(Driver.id == driver_id).with_for_update()
        else:
            v_stmt = select(Vehicle).where(Vehicle.id == vehicle_id)
            d_stmt = select(Driver).where(Driver.id == driver_id)

        v_res = await db.execute(v_stmt)
        vehicle = v_res.scalar_one_or_none()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

        d_res = await db.execute(d_stmt)
        driver = d_res.scalar_one_or_none()
        if not driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

        # 1. Cargo weight check
        if cargo_weight > vehicle.max_load_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cargo weight ({cargo_weight} kg) exceeds vehicle maximum capacity ({vehicle.max_load_capacity} kg)."
            )

        # 2. Vehicle availability check
        if vehicle.status != VehicleStatusEnum.available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle is not available (current status: {vehicle.status.value})."
            )

        # 3. Driver availability check
        if driver.status != DriverStatusEnum.available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Driver is not available (current status: {driver.status.value})."
            )
        if is_date_expired(driver.license_expiry):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver's license is expired."
            )

        return vehicle, driver

    @staticmethod
    async def create(db: AsyncSession, obj_in: TripCreate) -> Trip:
        # Validate vehicle and driver are available
        await TripService.validate_resources(
            db=db,
            vehicle_id=obj_in.vehicle_id,
            driver_id=obj_in.driver_id,
            cargo_weight=float(obj_in.cargo_weight)
        )

        db_obj = Trip(
            source=obj_in.source,
            destination=obj_in.destination,
            vehicle_id=obj_in.vehicle_id,
            driver_id=obj_in.driver_id,
            cargo_weight=obj_in.cargo_weight,
            planned_distance=obj_in.planned_distance,
            revenue=obj_in.revenue,
            status=TripStatusEnum.draft
        )
        db.add(db_obj)
        await db.commit()
        
        # Return fully loaded Trip object
        trip = await TripService.get(db, db_obj.id)
        return trip

    @staticmethod
    async def get(db: AsyncSession, id: int) -> Optional[Trip]:
        stmt = select(Trip).options(
            selectinload(Trip.vehicle),
            selectinload(Trip.driver)
        ).where(Trip.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[TripStatusEnum] = None
    ) -> List[Trip]:
        stmt = select(Trip).options(
            selectinload(Trip.vehicle),
            selectinload(Trip.driver)
        )
        if status_filter:
            stmt = stmt.where(Trip.status == status_filter)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, db_obj: Trip, obj_in: TripUpdate) -> Trip:
        if db_obj.status != TripStatusEnum.draft:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trips can only be updated while in draft status."
            )

        update_data = obj_in.model_dump(exclude_unset=True)
        
        # If resources are being changed, re-validate
        vehicle_id = update_data.get("vehicle_id", db_obj.vehicle_id)
        driver_id = update_data.get("driver_id", db_obj.driver_id)
        cargo_weight = update_data.get("cargo_weight", db_obj.cargo_weight)
        
        if any(k in update_data for k in ["vehicle_id", "driver_id", "cargo_weight"]):
            await TripService.validate_resources(
                db=db,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                cargo_weight=float(cargo_weight)
            )

        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        
        # Return fully loaded Trip object
        trip = await TripService.get(db, db_obj.id)
        return trip

    @staticmethod
    async def dispatch(db: AsyncSession, trip_id: int) -> Trip:
        # Load trip
        trip = await TripService.get(db, trip_id)
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
        
        # State transition validation
        if trip.status == TripStatusEnum.dispatched:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trip is already dispatched.")
        if trip.status != TripStatusEnum.draft:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot dispatch trip in '{trip.status.value}' status."
            )

        # Atomic row locking & re-validation at dispatch time
        vehicle, driver = await TripService.validate_resources(
            db=db,
            vehicle_id=trip.vehicle_id,
            driver_id=trip.driver_id,
            cargo_weight=float(trip.cargo_weight),
            is_dispatch=True
        )

        # Transition status
        trip.status = TripStatusEnum.dispatched
        trip.dispatched_at = datetime.now()
        vehicle.status = VehicleStatusEnum.on_trip
        driver.status = DriverStatusEnum.on_trip

        db.add(trip)
        db.add(vehicle)
        db.add(driver)
        await db.commit()
        
        # Return fully loaded Trip object
        return await TripService.get(db, trip_id)

    @staticmethod
    async def complete(db: AsyncSession, trip_id: int, req: TripCompleteRequest) -> Trip:
        trip = await TripService.get(db, trip_id)
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        # Double complete check
        if trip.status == TripStatusEnum.completed:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trip is already completed.")
        if trip.status != TripStatusEnum.dispatched:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete trip in '{trip.status.value}' status."
            )

        # Load vehicle and driver
        vehicle_res = await db.execute(select(Vehicle).where(Vehicle.id == trip.vehicle_id))
        vehicle = vehicle_res.scalar_one_or_none()
        
        driver_res = await db.execute(select(Driver).where(Driver.id == trip.driver_id))
        driver = driver_res.scalar_one_or_none()

        # Odometer validation
        if req.final_odometer < vehicle.odometer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Final odometer ({req.final_odometer}) cannot be less than current vehicle odometer ({vehicle.odometer})."
            )

        # Complete trip & release resources
        trip.status = TripStatusEnum.completed
        trip.completed_at = datetime.now()
        trip.actual_distance = req.actual_distance
        trip.fuel_consumed = req.fuel_consumed
        trip.final_odometer = req.final_odometer
        if req.revenue is not None:
            trip.revenue = req.revenue

        vehicle.odometer = req.final_odometer
        vehicle.status = VehicleStatusEnum.available
        driver.status = DriverStatusEnum.available

        db.add(trip)
        db.add(vehicle)
        db.add(driver)
        await db.commit()
        
        # Return fully loaded Trip object
        return await TripService.get(db, trip_id)

    @staticmethod
    async def cancel(db: AsyncSession, trip_id: int, req: TripCancelRequest) -> Trip:
        trip = await TripService.get(db, trip_id)
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        if trip.status == TripStatusEnum.cancelled:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trip is already cancelled.")
        if trip.status == TripStatusEnum.completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a completed trip."
            )

        # Load vehicle and driver
        vehicle_res = await db.execute(select(Vehicle).where(Vehicle.id == trip.vehicle_id))
        vehicle = vehicle_res.scalar_one_or_none()
        
        driver_res = await db.execute(select(Driver).where(Driver.id == trip.driver_id))
        driver = driver_res.scalar_one_or_none()

        # Release resources if already dispatched
        if trip.status == TripStatusEnum.dispatched:
            vehicle.status = VehicleStatusEnum.available
            driver.status = DriverStatusEnum.available
            db.add(vehicle)
            db.add(driver)

        trip.status = TripStatusEnum.cancelled
        trip.cancelled_at = datetime.now()
        trip.cancel_reason = req.reason

        db.add(trip)
        await db.commit()
        
        # Return fully loaded Trip object
        return await TripService.get(db, trip_id)
