import csv
import io
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import List, Optional, Generator
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle, VehicleStatusEnum
from app.models.trip import Trip, TripStatusEnum
from app.models.maintenance import MaintenanceLog
from app.models.fuel_log import FuelLog
from app.models.expense import Expense
from app.schemas.reports import (
    FuelEfficiencyReportItem,
    FleetUtilizationReportItem,
    OperationalCostReportItem,
    VehicleROIReportItem
)


class ReportsService:
    @staticmethod
    async def get_fuel_efficiency_report(
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[FuelEfficiencyReportItem]:
        # Get all vehicles
        v_res = await db.execute(select(Vehicle))
        vehicles = v_res.scalars().all()

        report = []
        for v in vehicles:
            # Query completed trips for this vehicle in date range
            stmt = select(
                func.sum(Trip.actual_distance),
                func.sum(Trip.fuel_consumed)
            ).where(
                and_(
                    Trip.vehicle_id == v.id,
                    Trip.status == TripStatusEnum.completed
                )
            )
            if start_date:
                start_dt = datetime.combine(start_date, datetime.min.time())
                stmt = stmt.where(Trip.completed_at >= start_dt)
            if end_date:
                end_dt = datetime.combine(end_date, datetime.max.time())
                stmt = stmt.where(Trip.completed_at <= end_dt)

            res = await db.execute(stmt)
            tot_dist, tot_fuel = res.first()
            tot_dist = tot_dist or Decimal("0.00")
            tot_fuel = tot_fuel or Decimal("0.00")

            fuel_eff = float(tot_dist / tot_fuel) if tot_fuel > 0 else "N/A"

            report.append(
                FuelEfficiencyReportItem(
                    vehicle_id=v.id,
                    registration_number=v.registration_number,
                    total_distance=float(tot_dist),
                    total_fuel_consumed=float(tot_fuel),
                    fuel_efficiency=fuel_eff
                )
            )
        return report

    @staticmethod
    async def get_fleet_utilization_report(
        db: AsyncSession,
        start_date: date,
        end_date: date
    ) -> List[FleetUtilizationReportItem]:
        report = []
        curr = start_date
        while curr <= end_date:
            # Total non-retired vehicles on this day
            total_stmt = select(func.count(Vehicle.id)).where(
                and_(
                    func.date(Vehicle.created_at) <= curr,
                    Vehicle.status != VehicleStatusEnum.retired
                )
            )
            total_res = await db.execute(total_stmt)
            total_vehicles = total_res.scalar_one()

            # Utilized vehicles on this day (vehicles with a trip dispatched/completed overlapping this day)
            curr_dt = datetime.combine(curr, datetime.min.time())
            curr_end_dt = datetime.combine(curr, datetime.max.time())
            util_stmt = select(func.count(func.distinct(Trip.vehicle_id))).where(
                and_(
                    Trip.status.in_([TripStatusEnum.dispatched, TripStatusEnum.completed]),
                    Trip.dispatched_at <= curr_end_dt,
                    or_(
                        Trip.completed_at.is_(None),
                        Trip.completed_at >= curr_dt
                    )
                )
            )
            util_res = await db.execute(util_stmt)
            util_vehicles = util_res.scalar_one()

            util_pct = float(util_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0.0
            report.append(
                FleetUtilizationReportItem(
                    date=curr.strftime("%Y-%m-%d"),
                    utilization_pct=util_pct
                )
            )
            curr += timedelta(days=1)
        return report

    @staticmethod
    async def get_operational_cost_report(
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[OperationalCostReportItem]:
        v_res = await db.execute(select(Vehicle))
        vehicles = v_res.scalars().all()

        report = []
        for v in vehicles:
            # 1. Fuel cost
            fuel_stmt = select(func.sum(FuelLog.cost)).where(FuelLog.vehicle_id == v.id)
            if start_date:
                fuel_stmt = fuel_stmt.where(FuelLog.date >= start_date)
            if end_date:
                fuel_stmt = fuel_stmt.where(FuelLog.date <= end_date)
            fuel_res = await db.execute(fuel_stmt)
            fuel_cost = fuel_res.scalar() or Decimal("0.00")

            # 2. Maintenance cost
            maint_stmt = select(func.sum(MaintenanceLog.cost)).where(MaintenanceLog.vehicle_id == v.id)
            if start_date:
                maint_stmt = maint_stmt.where(func.date(MaintenanceLog.started_at) >= start_date)
            if end_date:
                maint_stmt = maint_stmt.where(func.date(MaintenanceLog.started_at) <= end_date)
            maint_res = await db.execute(maint_stmt)
            maint_cost = maint_res.scalar() or Decimal("0.00")

            # 3. Other expense cost
            exp_stmt = select(func.sum(Expense.cost)).where(Expense.vehicle_id == v.id)
            if start_date:
                exp_stmt = exp_stmt.where(Expense.date >= start_date)
            if end_date:
                exp_stmt = exp_stmt.where(Expense.date <= end_date)
            exp_res = await db.execute(exp_stmt)
            expense_cost = exp_res.scalar() or Decimal("0.00")

            total_cost = fuel_cost + maint_cost + expense_cost
            report.append(
                OperationalCostReportItem(
                    vehicle_id=v.id,
                    registration_number=v.registration_number,
                    fuel_cost=fuel_cost,
                    maintenance_cost=maint_cost,
                    other_expense_cost=expense_cost,
                    total_cost=total_cost
                )
            )
        return report

    @staticmethod
    async def get_vehicle_roi_report(
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[VehicleROIReportItem]:
        v_res = await db.execute(select(Vehicle))
        vehicles = v_res.scalars().all()

        report = []
        for v in vehicles:
            # 1. Fuel cost
            fuel_stmt = select(func.sum(FuelLog.cost)).where(FuelLog.vehicle_id == v.id)
            if start_date:
                fuel_stmt = fuel_stmt.where(FuelLog.date >= start_date)
            if end_date:
                fuel_stmt = fuel_stmt.where(FuelLog.date <= end_date)
            fuel_res = await db.execute(fuel_stmt)
            fuel_cost = fuel_res.scalar() or Decimal("0.00")

            # 2. Maintenance cost
            maint_stmt = select(func.sum(MaintenanceLog.cost)).where(MaintenanceLog.vehicle_id == v.id)
            if start_date:
                maint_stmt = maint_stmt.where(func.date(MaintenanceLog.started_at) >= start_date)
            if end_date:
                maint_stmt = maint_stmt.where(func.date(MaintenanceLog.started_at) <= end_date)
            maint_res = await db.execute(maint_stmt)
            maint_cost = maint_res.scalar() or Decimal("0.00")

            # 3. Revenue from completed trips
            rev_stmt = select(func.sum(Trip.revenue)).where(
                and_(
                    Trip.vehicle_id == v.id,
                    Trip.status == TripStatusEnum.completed
                )
            )
            if start_date:
                start_dt = datetime.combine(start_date, datetime.min.time())
                rev_stmt = rev_stmt.where(Trip.completed_at >= start_dt)
            if end_date:
                end_dt = datetime.combine(end_date, datetime.max.time())
                rev_stmt = rev_stmt.where(Trip.completed_at <= end_dt)
            rev_res = await db.execute(rev_stmt)
            revenue = rev_res.scalar()

            # If no revenue exists (not even a 0.00 completion), it returns "N/A"
            if revenue is None:
                roi = "N/A"
                revenue_display = "N/A"
            elif v.acquisition_cost == 0:
                roi = "N/A"
                revenue_display = revenue
            else:
                roi = float((revenue - maint_cost - fuel_cost) / v.acquisition_cost * 100)
                revenue_display = revenue

            report.append(
                VehicleROIReportItem(
                    vehicle_id=v.id,
                    registration_number=v.registration_number,
                    acquisition_cost=v.acquisition_cost,
                    revenue=revenue_display,
                    fuel_cost=fuel_cost,
                    maintenance_cost=maint_cost,
                    roi=roi
                )
            )
        return report

    @staticmethod
    async def export_to_csv(
        db: AsyncSession,
        report_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Generator[str, None, None]:
        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == "fuel-efficiency":
            headers = ["Vehicle ID", "Registration Number", "Total Distance (km)", "Total Fuel Consumed (L)", "Fuel Efficiency"]
            writer.writerow(headers)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            data = await ReportsService.get_fuel_efficiency_report(db, start_date, end_date)
            for item in data:
                writer.writerow([item.vehicle_id, item.registration_number, item.total_distance, item.total_fuel_consumed, item.fuel_efficiency])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        elif report_type == "utilization":
            headers = ["Date", "Utilization Percentage"]
            writer.writerow(headers)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            if not start_date or not end_date:
                # Default to last 30 days if range is missing
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
            data = await ReportsService.get_fleet_utilization_report(db, start_date, end_date)
            for item in data:
                writer.writerow([item.date, item.utilization_pct])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        elif report_type == "operational-cost":
            headers = ["Vehicle ID", "Registration Number", "Fuel Cost ($)", "Maintenance Cost ($)", "Other Expenses ($)", "Total Cost ($)"]
            writer.writerow(headers)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            data = await ReportsService.get_operational_cost_report(db, start_date, end_date)
            for item in data:
                writer.writerow([item.vehicle_id, item.registration_number, item.fuel_cost, item.maintenance_cost, item.other_expense_cost, item.total_cost])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        elif report_type == "vehicle-roi":
            headers = ["Vehicle ID", "Registration Number", "Acquisition Cost ($)", "Revenue ($)", "Fuel Cost ($)", "Maintenance Cost ($)", "ROI (%)"]
            writer.writerow(headers)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            data = await ReportsService.get_vehicle_roi_report(db, start_date, end_date)
            for item in data:
                writer.writerow([item.vehicle_id, item.registration_number, item.acquisition_cost, item.revenue, item.fuel_cost, item.maintenance_cost, item.roi])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
