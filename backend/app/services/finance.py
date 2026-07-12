from typing import List, Optional
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fuel_log import FuelLog
from app.models.expense import Expense
from app.models.maintenance import MaintenanceLog
from app.schemas.fuel_log import FuelLogCreate
from app.schemas.expense import ExpenseCreate


class FinanceService:
    @staticmethod
    async def create_fuel_log(db: AsyncSession, obj_in: FuelLogCreate, created_by: int) -> FuelLog:
        db_obj = FuelLog(
            vehicle_id=obj_in.vehicle_id,
            trip_id=obj_in.trip_id,
            liters=obj_in.liters,
            cost=obj_in.cost,
            date=obj_in.date,
            odometer_at_fill=obj_in.odometer_at_fill,
            created_by=created_by
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_fuel_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        vehicle_id: Optional[int] = None
    ) -> List[FuelLog]:
        stmt = select(FuelLog)
        if vehicle_id:
            stmt = stmt.where(FuelLog.vehicle_id == vehicle_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_expense(db: AsyncSession, obj_in: ExpenseCreate, created_by: int) -> Expense:
        db_obj = Expense(
            vehicle_id=obj_in.vehicle_id,
            trip_id=obj_in.trip_id,
            expense_type=obj_in.expense_type,
            description=obj_in.description,
            cost=obj_in.cost,
            date=obj_in.date,
            created_by=created_by
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_expenses(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        vehicle_id: Optional[int] = None
    ) -> List[Expense]:
        stmt = select(Expense)
        if vehicle_id:
            stmt = stmt.where(Expense.vehicle_id == vehicle_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_total_operational_cost(db: AsyncSession, vehicle_id: int) -> dict:
        # Sum fuel costs
        fuel_stmt = select(func.sum(FuelLog.cost)).where(FuelLog.vehicle_id == vehicle_id)
        fuel_res = await db.execute(fuel_stmt)
        fuel_cost = fuel_res.scalar() or Decimal("0.00")

        # Sum maintenance costs
        maint_stmt = select(func.sum(MaintenanceLog.cost)).where(MaintenanceLog.vehicle_id == vehicle_id)
        maint_res = await db.execute(maint_stmt)
        maint_cost = maint_res.scalar() or Decimal("0.00")

        # Sum expense costs (other costs)
        exp_stmt = select(func.sum(Expense.cost)).where(Expense.vehicle_id == vehicle_id)
        exp_res = await db.execute(exp_stmt)
        expense_cost = exp_res.scalar() or Decimal("0.00")

        total_cost = fuel_cost + maint_cost + expense_cost

        return {
            "vehicle_id": vehicle_id,
            "fuel_cost": fuel_cost,
            "maintenance_cost": maint_cost,
            "other_expense_cost": expense_cost,
            "total_cost": total_cost
        }
