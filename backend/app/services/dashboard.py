from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, RoleEnum
from app.models.vehicle import Vehicle, VehicleStatusEnum, VehicleTypeEnum
from app.models.driver import Driver, DriverStatusEnum
from app.models.trip import Trip, TripStatusEnum
from app.models.maintenance import MaintenanceLog, MaintenanceStatusEnum
from app.models.fuel_log import FuelLog
from app.models.expense import Expense
from app.schemas.dashboard import (
    DashboardKPIsResponse,
    ChartDataResponse,
    TripStatusBreakdownItem,
    CostTrendItem,
    UtilizationTrendItem
)


class DashboardService:
    @staticmethod
    async def get_driver_by_name(db: AsyncSession, name: str) -> Optional[Driver]:
        stmt = select(Driver).where(Driver.name == name)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_kpis(
        db: AsyncSession,
        current_user: User,
        vehicle_type: Optional[VehicleTypeEnum] = None,
        vehicle_status: Optional[VehicleStatusEnum] = None,
        region: Optional[str] = None
    ) -> DashboardKPIsResponse:
        # Build base vehicle filter
        v_filters = []
        if vehicle_type:
            v_filters.append(Vehicle.type == vehicle_type)
        if vehicle_status:
            v_filters.append(Vehicle.status == vehicle_status)
        if region:
            v_filters.append(Vehicle.region == region)

        # Build base trip filter based on vehicle filter
        t_filters = []
        if vehicle_type or vehicle_status or region:
            # We filter trips associated with vehicles matching the criteria
            v_subquery = select(Vehicle.id)
            if vehicle_type:
                v_subquery = v_subquery.where(Vehicle.type == vehicle_type)
            if vehicle_status:
                v_subquery = v_subquery.where(Vehicle.status == vehicle_status)
            if region:
                v_subquery = v_subquery.where(Vehicle.region == region)
            t_filters.append(Trip.vehicle_id.in_(v_subquery))

        # Check role-specific constraints
        if current_user.role == RoleEnum.driver:
            # Driver sees own trips only
            driver = await DashboardService.get_driver_by_name(db, current_user.full_name)
            if not driver:
                return DashboardKPIsResponse(
                    active_trips_count=0,
                    pending_trips_count=0,
                    fuel_efficiency=0.0
                )
            
            # Active trips count (dispatched)
            active_trips_stmt = select(func.count(Trip.id)).where(
                and_(Trip.driver_id == driver.id, Trip.status == TripStatusEnum.dispatched, *t_filters)
            )
            active_trips_res = await db.execute(active_trips_stmt)
            active_trips_count = active_trips_res.scalar_one()

            # Pending trips count (draft)
            pending_trips_stmt = select(func.count(Trip.id)).where(
                and_(Trip.driver_id == driver.id, Trip.status == TripStatusEnum.draft, *t_filters)
            )
            pending_trips_res = await db.execute(pending_trips_stmt)
            pending_trips_count = pending_trips_res.scalar_one()

            # Own fuel efficiency (total distance / total fuel consumed of own completed trips)
            fuel_stmt = select(
                func.sum(Trip.actual_distance),
                func.sum(Trip.fuel_consumed)
            ).where(
                and_(Trip.driver_id == driver.id, Trip.status == TripStatusEnum.completed, *t_filters)
            )
            fuel_res = await db.execute(fuel_stmt)
            tot_dist, tot_fuel = fuel_res.first()
            tot_dist = tot_dist or Decimal("0.00")
            tot_fuel = tot_fuel or Decimal("0.00")
            fuel_eff = float(tot_dist / tot_fuel) if tot_fuel > 0 else 0.0

            return DashboardKPIsResponse(
                active_trips_count=active_trips_count,
                pending_trips_count=pending_trips_count,
                fuel_efficiency=fuel_eff
            )

        # Non-driver overall fleet queries
        # 1. Vehicles metrics
        veh_stmt_all = select(Vehicle)
        if v_filters:
            veh_stmt_all = veh_stmt_all.where(and_(*v_filters))
        veh_res = await db.execute(veh_stmt_all)
        vehicles = list(veh_res.scalars().all())

        total_non_retired = sum(1 for v in vehicles if v.status != VehicleStatusEnum.retired)
        active_vehicles_count = sum(1 for v in vehicles if v.status in [VehicleStatusEnum.available, VehicleStatusEnum.on_trip])
        available_vehicles_count = sum(1 for v in vehicles if v.status == VehicleStatusEnum.available)
        vehicles_in_shop_count = sum(1 for v in vehicles if v.status == VehicleStatusEnum.in_shop)

        # 2. Trips metrics
        active_trips_stmt = select(func.count(Trip.id)).where(and_(Trip.status == TripStatusEnum.dispatched, *t_filters))
        active_trips_res = await db.execute(active_trips_stmt)
        active_trips_count = active_trips_res.scalar_one()

        pending_trips_stmt = select(func.count(Trip.id)).where(and_(Trip.status == TripStatusEnum.draft, *t_filters))
        pending_trips_res = await db.execute(pending_trips_stmt)
        pending_trips_count = pending_trips_res.scalar_one()

        # 3. Drivers metrics
        drivers_stmt = select(func.count(Driver.id)).where(
            Driver.status.in_([DriverStatusEnum.available, DriverStatusEnum.on_trip])
        )
        if region:
            drivers_stmt = drivers_stmt.join(Trip, Trip.driver_id == Driver.id).join(
                Vehicle, Vehicle.id == Trip.vehicle_id
            ).where(Vehicle.region == region)
        drivers_res = await db.execute(drivers_stmt)
        drivers_on_duty_count = drivers_res.scalar_one()

        # 4. Fleet utilization % (on_trip / total non-retired * 100)
        on_trip_count = sum(1 for v in vehicles if v.status == VehicleStatusEnum.on_trip)
        fleet_utilization = float(on_trip_count / total_non_retired * 100) if total_non_retired > 0 else 0.0

        # 5. Fuel efficiency (total distance / total fuel consumed of completed trips)
        fuel_stmt = select(
            func.sum(Trip.actual_distance),
            func.sum(Trip.fuel_consumed)
        ).where(and_(Trip.status == TripStatusEnum.completed, *t_filters))
        fuel_res = await db.execute(fuel_stmt)
        tot_dist, tot_fuel = fuel_res.first()
        tot_dist = tot_dist or Decimal("0.00")
        tot_fuel = tot_fuel or Decimal("0.00")
        fuel_eff = float(tot_dist / tot_fuel) if tot_fuel > 0 else 0.0

        if current_user.role == RoleEnum.safety_officer:
            # Safety officer does NOT see cost/financial metrics
            return DashboardKPIsResponse(
                active_vehicles_count=active_vehicles_count,
                available_vehicles_count=available_vehicles_count,
                vehicles_in_shop_count=vehicles_in_shop_count,
                active_trips_count=active_trips_count,
                pending_trips_count=pending_trips_count,
                drivers_on_duty_count=drivers_on_duty_count,
                fleet_utilization_pct=fleet_utilization,
                fuel_efficiency=fuel_eff
            )

        # Financial analyst & Fleet manager see cost/financial metrics
        # 6. Operational cost (sum of fuel log costs + sum of closed maintenance costs)
        v_sub = select(Vehicle.id)
        if v_filters:
            v_sub = v_sub.where(and_(*v_filters))
            
        fuel_cost_stmt = select(func.sum(FuelLog.cost)).where(FuelLog.vehicle_id.in_(v_sub))
        fuel_cost_res = await db.execute(fuel_cost_stmt)
        total_fuel_cost = fuel_cost_res.scalar() or Decimal("0.00")

        maint_cost_stmt = select(func.sum(MaintenanceLog.cost)).where(MaintenanceLog.vehicle_id.in_(v_sub))
        maint_cost_res = await db.execute(maint_cost_stmt)
        total_maint_cost = maint_cost_res.scalar() or Decimal("0.00")

        operational_cost = total_fuel_cost + total_maint_cost

        # 7. ROI = (sum(revenue) - total_maint - total_fuel) / sum(acquisition_cost) * 100
        rev_stmt = select(func.sum(Trip.revenue)).where(and_(Trip.status == TripStatusEnum.completed, *t_filters))
        rev_res = await db.execute(rev_stmt)
        total_revenue = rev_res.scalar() or Decimal("0.00")

        acq_cost_stmt = select(func.sum(Vehicle.acquisition_cost))
        if v_filters:
            acq_cost_stmt = acq_cost_stmt.where(and_(*v_filters))
        acq_res = await db.execute(acq_cost_stmt)
        total_acq_cost = acq_res.scalar() or Decimal("0.00")

        if total_acq_cost == 0:
            roi = "N/A"
        elif total_revenue == 0:
            # We return "N/A" if no revenue exists (as per stakeholder comment: ROI with no revenue returns "N/A")
            roi = "N/A"
        else:
            roi = float((total_revenue - total_maint_cost - total_fuel_cost) / total_acq_cost * 100)

        return DashboardKPIsResponse(
            active_vehicles_count=active_vehicles_count,
            available_vehicles_count=available_vehicles_count,
            vehicles_in_shop_count=vehicles_in_shop_count,
            active_trips_count=active_trips_count,
            pending_trips_count=pending_trips_count,
            drivers_on_duty_count=drivers_on_duty_count,
            fleet_utilization_pct=fleet_utilization,
            fuel_efficiency=fuel_eff,
            operational_cost=operational_cost,
            roi=roi
        )

    @staticmethod
    async def get_charts(db: AsyncSession, current_user: User) -> ChartDataResponse:
        # 1. Trip status breakdown
        t_stmt = select(Trip.status, func.count(Trip.id)).group_by(Trip.status)
        if current_user.role == RoleEnum.driver:
            driver = await DashboardService.get_driver_by_name(db, current_user.full_name)
            if driver:
                t_stmt = t_stmt.where(Trip.driver_id == driver.id)
        t_res = await db.execute(t_stmt)
        status_items = [
            TripStatusBreakdownItem(status=status.value, count=cnt)
            for status, cnt in t_res.all()
        ]

        # 2. Cost trend by month (last 6 months)
        cost_trend: List[CostTrendItem] = []
        # Find unique months in past 6 months
        today = date.today()
        months = []
        for i in range(5, -1, -1):
            d = today - timedelta(days=i * 30)
            months.append(d.strftime("%Y-%m"))

        for m in months:
            # Sum costs for this month
            # Note: We filter FuelLog and Expense by their date field matching the month prefix
            start_date = date(int(m.split("-")[0]), int(m.split("-")[1]), 1)
            if start_date.month == 12:
                end_date = date(start_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(start_date.year, start_date.month + 1, 1) - timedelta(days=1)

            fuel_stmt = select(func.sum(FuelLog.cost)).where(FuelLog.date.between(start_date, end_date))
            fuel_res = await db.execute(fuel_stmt)
            fuel_cost = fuel_res.scalar() or Decimal("0.00")

            maint_stmt = select(func.sum(MaintenanceLog.cost)).where(
                func.date(MaintenanceLog.started_at).between(start_date, end_date)
            )
            maint_res = await db.execute(maint_stmt)
            maint_cost = maint_res.scalar() or Decimal("0.00")

            exp_stmt = select(func.sum(Expense.cost)).where(Expense.date.between(start_date, end_date))
            exp_res = await db.execute(exp_stmt)
            exp_cost = exp_res.scalar() or Decimal("0.00")

            cost_trend.append(
                CostTrendItem(
                    month=m,
                    fuel_cost=fuel_cost,
                    maintenance_cost=maint_cost,
                    other_expense_cost=exp_cost
                )
            )

        # 3. Utilization trend (last 7 days)
        utilization_trend: List[UtilizationTrendItem] = []
        for i in range(6, -1, -1):
            day = date.today() - timedelta(days=i)
            # Count non-retired vehicles on this day
            total_stmt = select(func.count(Vehicle.id)).where(
                and_(
                    func.date(Vehicle.created_at) <= day,
                    Vehicle.status != VehicleStatusEnum.retired
                )
            )
            total_res = await db.execute(total_stmt)
            total_vehicles = total_res.scalar_one()

            # Count utilized vehicles on this day (vehicles with a trip dispatched/completed overlapping this day)
            day_dt = datetime.combine(day, datetime.min.time())
            day_end_dt = datetime.combine(day, datetime.max.time())
            util_stmt = select(func.count(func.distinct(Trip.vehicle_id))).where(
                and_(
                    Trip.status.in_([TripStatusEnum.dispatched, TripStatusEnum.completed]),
                    Trip.dispatched_at <= day_end_dt,
                    or_(
                        Trip.completed_at.is_(None),
                        Trip.completed_at >= day_dt
                    )
                )
            )
            util_res = await db.execute(util_stmt)
            util_vehicles = util_res.scalar_one()

            util_pct = float(util_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0.0
            utilization_trend.append(
                UtilizationTrendItem(
                    date=day.strftime("%Y-%m-%d"),
                    utilization_pct=util_pct
                )
            )

        return ChartDataResponse(
            trip_status_breakdown=status_items,
            cost_trend=cost_trend,
            utilization_trend=utilization_trend
        )
