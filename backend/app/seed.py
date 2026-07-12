"""
TransitOps — Demo Data Seeder
==========================================================
Run after `docker compose up`:

    docker compose exec web python -m app.seed_demo

Seeds:
  * 4 users (one per role)
  * 7 vehicles (Gujarat fleet — truck, van, bus, pickup)
  * 6 drivers (varied statuses, one with expired license)
  * 12 trips  (all 4 statuses, spread over 6 months)
  * 8  maintenance logs (active + closed, 6-month spread)
  * 10 fuel logs
  * 12 expenses (tolls, insurance, fines, maintenance-related)

Idempotent — safe to run multiple times. Checks by unique key
before inserting so existing data is never duplicated.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.driver import Driver, DriverStatusEnum, LicenseCategoryEnum
from app.models.expense import Expense, ExpenseTypeEnum
from app.models.fuel_log import FuelLog
from app.models.maintenance import MaintenanceLog, MaintenanceStatusEnum, MaintenanceTypeEnum
from app.models.trip import Trip, TripStatusEnum
from app.models.user import RoleEnum, User
from app.models.vehicle import Vehicle, VehicleStatusEnum, VehicleTypeEnum

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    """Return a timezone-aware UTC datetime offset by the given amount."""
    return datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)


def d(days_ago: int = 0) -> date:
    """Return a date offset by the given number of days from today."""
    return date.today() - timedelta(days=days_ago)


def to_dt(val) -> datetime | None:
    """Coerce a date or datetime to an aware datetime, or return None."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    # plain date
    return datetime.combine(val, datetime.min.time()).replace(tzinfo=timezone.utc)


async def get_or_skip(db: AsyncSession, model, **kwargs):
    """Return (obj, already_existed). If found, returns existing record."""
    filters = [getattr(model, k) == v for k, v in kwargs.items()]
    result = await db.execute(select(model).where(*filters))
    existing = result.scalars().first()
    return existing, existing is not None


# ---------------------------------------------------------------------------
# 1. Users
# ---------------------------------------------------------------------------

USERS = [
    {
        "email": "manager@transitops.com",
        "password": "password123",
        "full_name": "Raven Kapoor",
        "role": RoleEnum.fleet_manager,
    },
    {
        "email": "driver@transitops.com",
        "password": "password123",
        "full_name": "Alex Menon",
        "role": RoleEnum.driver,
    },
    {
        "email": "safety@transitops.com",
        "password": "password123",
        "full_name": "Suresh Iyer",
        "role": RoleEnum.safety_officer,
    },
    {
        "email": "financial@transitops.com",
        "password": "password123",
        "full_name": "Priya Sharma",
        "role": RoleEnum.financial_analyst,
    },
]


async def seed_users(db: AsyncSession) -> dict[str, User]:
    users: dict[str, User] = {}
    for u in USERS:
        existing, found = await get_or_skip(db, User, email=u["email"])
        if found:
            log.info(f"  skip  User already exists: {u['email']}")
            users[u["email"]] = existing
        else:
            obj = User(
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                is_active=True,
            )
            db.add(obj)
            await db.flush()
            users[u["email"]] = obj
            log.info(f"  ok    User: {u['email']} [{u['role'].value}]")
    await db.commit()
    return users


# ---------------------------------------------------------------------------
# 2. Vehicles
# ---------------------------------------------------------------------------

VEHICLES_DATA = [
    # (reg, name, type, max_load_kg, odometer, acquisition_cost, region, status)
    ("GJ01AB4521", "VAN-05",   VehicleTypeEnum.van,    Decimal("500"),   Decimal("74200"),  Decimal("620000"),  "Gandhinagar", VehicleStatusEnum.available),
    ("GJ01AB9981", "TRUCK-11", VehicleTypeEnum.truck,  Decimal("8000"),  Decimal("182340"), Decimal("2450000"), "Ahmedabad",   VehicleStatusEnum.on_trip),
    ("GJ01AB1120", "MINI-03",  VehicleTypeEnum.pickup, Decimal("1200"),  Decimal("66100"),  Decimal("410000"),  "Sanand",      VehicleStatusEnum.in_shop),
    ("GJ01CD3388", "BUS-02",   VehicleTypeEnum.bus,    Decimal("4000"),  Decimal("311500"), Decimal("3800000"), "Ahmedabad",   VehicleStatusEnum.available),
    ("GJ06EF7712", "TRUCK-07", VehicleTypeEnum.truck,  Decimal("10000"), Decimal("98200"),  Decimal("3200000"), "Baroda",      VehicleStatusEnum.available),
    ("GJ01KL9900", "VAN-12",   VehicleTypeEnum.van,    Decimal("600"),   Decimal("41050"),  Decimal("580000"),  "Gandhinagar", VehicleStatusEnum.on_trip),
    ("GJ01AB0087", "VAN-09",   VehicleTypeEnum.van,    Decimal("750"),   Decimal("241900"), Decimal("590000"),  "Gandhinagar", VehicleStatusEnum.retired),
]


async def seed_vehicles(db: AsyncSession) -> dict[str, Vehicle]:
    vehicles: dict[str, Vehicle] = {}
    for (reg, name, vtype, cap, odo, cost, region, status) in VEHICLES_DATA:
        existing, found = await get_or_skip(db, Vehicle, registration_number=reg)
        if found:
            log.info(f"  skip  Vehicle: {reg}")
            vehicles[reg] = existing
        else:
            obj = Vehicle(
                registration_number=reg,
                name=name,
                type=vtype,
                max_load_capacity=cap,
                odometer=odo,
                acquisition_cost=cost,
                region=region,
                status=status,
            )
            db.add(obj)
            await db.flush()
            vehicles[reg] = obj
            log.info(f"  ok    Vehicle: {reg} ({name}) [{status.value}]")
    await db.commit()
    return vehicles


# ---------------------------------------------------------------------------
# 3. Drivers
# ---------------------------------------------------------------------------

DRIVERS_DATA = [
    # (name, license_number, category, expiry, contact, safety_score, status)
    ("Alex Menon",    "DL-GJ-88213", LicenseCategoryEnum.B,  date(2028, 12, 31), "9876543210", Decimal("96.50"), DriverStatusEnum.on_trip),
    ("John Dsouza",   "DL-GJ-44120", LicenseCategoryEnum.C,  date(2025,  3, 15), "9822011220", Decimal("81.00"), DriverStatusEnum.suspended),
    ("Priya Nair",    "DL-GJ-77031", LicenseCategoryEnum.B,  date(2027,  8, 15), "9911022330", Decimal("99.00"), DriverStatusEnum.available),
    ("Suresh Pillai", "DL-GJ-90045", LicenseCategoryEnum.CE, date(2027,  1, 15), "9744099880", Decimal("88.50"), DriverStatusEnum.available),
    ("Ramesh Patil",  "DL-MH-12311", LicenseCategoryEnum.C,  date(2026, 11, 30), "9900112233", Decimal("91.00"), DriverStatusEnum.on_trip),
    ("Kavita Bhat",   "DL-GJ-55580", LicenseCategoryEnum.B,  date(2029,  6, 30), "9823400011", Decimal("94.00"), DriverStatusEnum.off_duty),
]


async def seed_drivers(db: AsyncSession) -> dict[str, Driver]:
    drivers: dict[str, Driver] = {}
    for (name, lic, cat, expiry, contact, score, status) in DRIVERS_DATA:
        existing, found = await get_or_skip(db, Driver, license_number=lic)
        if found:
            log.info(f"  skip  Driver: {lic}")
            drivers[lic] = existing
        else:
            obj = Driver(
                name=name,
                license_number=lic,
                license_category=cat,
                license_expiry=expiry,
                contact_number=contact,
                safety_score=score,
                status=status,
            )
            db.add(obj)
            await db.flush()
            drivers[lic] = obj
            log.info(f"  ok    Driver: {name} [{status.value}]")
    await db.commit()
    return drivers


# ---------------------------------------------------------------------------
# 4. Trips
# ---------------------------------------------------------------------------

async def seed_trips(
    db: AsyncSession,
    V: dict[str, Vehicle],
    D: dict[str, Driver],
) -> list[Trip]:
    """
    12 trips covering all statuses:
    - 5 completed  (historical, 1-5 months ago — fuel/revenue for reports)
    - 2 dispatched (currently active — vehicles/drivers are on_trip)
    - 3 draft      (planned, not yet dispatched)
    - 3 cancelled  (historical)
    """
    check = await db.execute(select(Trip))
    if check.scalars().first():
        log.info("  skip  Trips already exist.")
        result = await db.execute(select(Trip))
        return list(result.scalars().all())

    trips_raw = [
        # ── COMPLETED ────────────────────────────────────────────────────────
        dict(
            source="Vatva Industrial Area", destination="Sanand GIDC Warehouse",
            vreg="GJ01AB9981", dlic="DL-GJ-88213",
            cargo=Decimal("4800"), planned=Decimal("52"), actual=Decimal("54"),
            fuel=Decimal("16.20"), odo=Decimal("182054"), revenue=Decimal("14500"),
            status=TripStatusEnum.completed,
            created=d(150), dispatched=d(150), completed=d(149),
        ),
        dict(
            source="Ahmedabad Depot", destination="Surat Logistics Hub",
            vreg="GJ06EF7712", dlic="DL-GJ-77031",
            cargo=Decimal("7500"), planned=Decimal("265"), actual=Decimal("270"),
            fuel=Decimal("81.00"), odo=Decimal("97600"), revenue=Decimal("32000"),
            status=TripStatusEnum.completed,
            created=d(120), dispatched=d(120), completed=d(119),
        ),
        dict(
            source="Sanand Industrial Estate", destination="Rajkot Distribution Centre",
            vreg="GJ01CD3388", dlic="DL-GJ-90045",
            cargo=Decimal("3200"), planned=Decimal("190"), actual=Decimal("196"),
            fuel=Decimal("62.40"), odo=Decimal("311120"), revenue=Decimal("22000"),
            status=TripStatusEnum.completed,
            created=d(90), dispatched=d(90), completed=d(89),
        ),
        dict(
            source="Gandhinagar Depot", destination="Mehsana Cold Storage",
            vreg="GJ01AB4521", dlic="DL-GJ-77031",
            cargo=Decimal("420"), planned=Decimal("75"), actual=Decimal("77"),
            fuel=Decimal("9.60"), odo=Decimal("73950"), revenue=Decimal("7800"),
            status=TripStatusEnum.completed,
            created=d(60), dispatched=d(60), completed=d(60),
        ),
        dict(
            source="Baroda Fuel Depot", destination="Anand Agro Hub",
            vreg="GJ06EF7712", dlic="DL-GJ-90045",
            cargo=Decimal("9200"), planned=Decimal("80"), actual=Decimal("83"),
            fuel=Decimal("28.50"), odo=Decimal("98200"), revenue=Decimal("18500"),
            status=TripStatusEnum.completed,
            created=d(30), dispatched=d(30), completed=d(29),
        ),

        # ── DISPATCHED ───────────────────────────────────────────────────────
        dict(
            source="Gandhinagar Depot", destination="Ahmedabad Hub (Naroda)",
            vreg="GJ01AB9981", dlic="DL-GJ-88213",
            cargo=Decimal("5200"), planned=Decimal("38"), revenue=Decimal("9500"),
            status=TripStatusEnum.dispatched,
            created=d(0), dispatched=utc(hours_ago=2),
        ),
        dict(
            source="Kalol Industrial Zone", destination="Kadi Export Hub",
            vreg="GJ01KL9900", dlic="DL-MH-12311",
            cargo=Decimal("540"), planned=Decimal("28"), revenue=Decimal("4200"),
            status=TripStatusEnum.dispatched,
            created=d(0), dispatched=utc(hours_ago=1),
        ),

        # ── DRAFT ────────────────────────────────────────────────────────────
        dict(
            source="Ahmedabad Depot", destination="Baroda Express Hub",
            vreg="GJ01CD3388", dlic="DL-GJ-90045",
            cargo=Decimal("3000"), planned=Decimal("110"), revenue=Decimal("15000"),
            status=TripStatusEnum.draft, created=d(1),
        ),
        dict(
            source="Sanand Depot", destination="Nadiad Textile Park",
            vreg="GJ01AB4521", dlic="DL-GJ-77031",
            cargo=Decimal("480"), planned=Decimal("62"), revenue=Decimal("5500"),
            status=TripStatusEnum.draft, created=d(0),
        ),
        dict(
            source="Gandhinagar Cold Hub", destination="Palanpur Distribution Centre",
            vreg="GJ06EF7712", dlic="DL-GJ-55580",
            cargo=Decimal("8800"), planned=Decimal("175"), revenue=Decimal("26000"),
            status=TripStatusEnum.draft, created=d(0),
        ),

        # ── CANCELLED ────────────────────────────────────────────────────────
        dict(
            source="Mansa", destination="Kalol Depot",
            vreg="GJ01AB1120", dlic="DL-GJ-90045",
            cargo=Decimal("800"), planned=Decimal("25"), revenue=Decimal("3500"),
            status=TripStatusEnum.cancelled,
            cancel_reason="Vehicle mechanical failure — sent to shop for tyre replacement",
            created=d(5), cancelled=d(5),
        ),
        dict(
            source="Ahmedabad Main Depot", destination="Palanpur Warehouse",
            vreg="GJ01AB9981", dlic="DL-GJ-88213",
            cargo=Decimal("6000"), planned=Decimal("180"), revenue=Decimal("21000"),
            status=TripStatusEnum.cancelled,
            cancel_reason="Consignment postponed by client — rescheduled next week",
            created=d(12), cancelled=d(12),
        ),
        dict(
            source="Baroda Depot", destination="Ankleshwar Chemical Zone",
            vreg="GJ01KL9900", dlic="DL-MH-12311",
            cargo=Decimal("520"), planned=Decimal("95"), revenue=Decimal("8900"),
            status=TripStatusEnum.cancelled,
            cancel_reason="Driver unavailable due to personal emergency",
            created=d(20), cancelled=d(20),
        ),
    ]

    created_trips: list[Trip] = []
    for r in trips_raw:
        vehicle = V[r["vreg"]]
        driver = D[r["dlic"]]

        trip = Trip(
            source=r["source"],
            destination=r["destination"],
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            cargo_weight=r["cargo"],
            planned_distance=r["planned"],
            actual_distance=r.get("actual"),
            fuel_consumed=r.get("fuel"),
            final_odometer=r.get("odo"),
            revenue=r.get("revenue"),
            status=r["status"],
            dispatched_at=to_dt(r.get("dispatched")),
            completed_at=to_dt(r.get("completed")),
            cancelled_at=to_dt(r.get("cancelled")),
            cancel_reason=r.get("cancel_reason"),
            created_at=to_dt(r.get("created", d(0))),
            updated_at=to_dt(r.get("created", d(0))),
        )
        db.add(trip)
        await db.flush()
        created_trips.append(trip)
        log.info(f"  ok    Trip: {r['source']} -> {r['destination']} [{r['status'].value}]")

    await db.commit()
    return created_trips


# ---------------------------------------------------------------------------
# 5. Maintenance Logs
# ---------------------------------------------------------------------------

async def seed_maintenance(db: AsyncSession, V: dict[str, Vehicle]) -> None:
    check = await db.execute(select(MaintenanceLog))
    if check.scalars().first():
        log.info("  skip  Maintenance logs already exist.")
        return

    records = [
        # Active (vehicles currently in shop or scheduled)
        dict(vehicle="GJ01AB1120", mtype=MaintenanceTypeEnum.tire_replacement,
             desc="Front tyre replacement — both front tyres worn below 3 mm tread",
             cost=None, status=MaintenanceStatusEnum.active,
             started=utc(days_ago=3), closed=None, notes=None),
        dict(vehicle="GJ01AB4521", mtype=MaintenanceTypeEnum.oil_change,
             desc="Scheduled 10,000 km oil change — 10W-40 full synthetic",
             cost=Decimal("2800"), status=MaintenanceStatusEnum.active,
             started=utc(days_ago=1), closed=None, notes=None),

        # Closed (historical)
        dict(vehicle="GJ01AB9981", mtype=MaintenanceTypeEnum.engine_repair,
             desc="Engine overheating — radiator leak, coolant system flush + OEM radiator replacement",
             cost=Decimal("18500"), status=MaintenanceStatusEnum.closed,
             started=utc(days_ago=30), closed=utc(days_ago=28),
             notes="Replaced OEM radiator. 50 km test run — no overheating. Cleared for service."),
        dict(vehicle="GJ06EF7712", mtype=MaintenanceTypeEnum.brake_service,
             desc="Full brake pad replacement — front and rear axles. Brake fluid bled.",
             cost=Decimal("9200"), status=MaintenanceStatusEnum.closed,
             started=utc(days_ago=45), closed=utc(days_ago=44),
             notes="All four corners done. Disc thickness within spec. Test drive cleared."),
        dict(vehicle="GJ01CD3388", mtype=MaintenanceTypeEnum.inspection,
             desc="Annual government fitness certificate inspection — full vehicle roadworthy check",
             cost=Decimal("3500"), status=MaintenanceStatusEnum.closed,
             started=utc(days_ago=90), closed=utc(days_ago=89),
             notes="Passed. New FC valid 12 months. Minor wiper blade replacement noted."),
        dict(vehicle="GJ01AB4521", mtype=MaintenanceTypeEnum.electrical,
             desc="Alternator belt failure — belt replaced, battery terminal cleaning and greasing",
             cost=Decimal("4100"), status=MaintenanceStatusEnum.closed,
             started=utc(days_ago=120), closed=utc(days_ago=119),
             notes="New Gates belt fitted. Charging voltage confirmed at 14.2 V idle."),
        dict(vehicle="GJ01AB1120", mtype=MaintenanceTypeEnum.body_work,
             desc="Dent repair — left rear quarter panel + repaint to body colour match",
             cost=Decimal("6800"), status=MaintenanceStatusEnum.closed,
             started=utc(days_ago=60), closed=utc(days_ago=58),
             notes="Colour-matched finish. Customer sign-off obtained."),
        dict(vehicle="GJ01KL9900", mtype=MaintenanceTypeEnum.transmission,
             desc="Gearbox oil change — manual 5-speed, flush + refill GL-4 80W-90",
             cost=Decimal("1800"), status=MaintenanceStatusEnum.closed,
             started=utc(days_ago=75), closed=utc(days_ago=75),
             notes="Routine interval. No metal particles in old oil. Gearbox healthy."),
    ]

    for r in records:
        obj = MaintenanceLog(
            vehicle_id=V[r["vehicle"]].id,
            maintenance_type=r["mtype"],
            description=r["desc"],
            cost=r["cost"],
            status=r["status"],
            started_at=r["started"],
            closed_at=r.get("closed"),
            notes=r.get("notes"),
        )
        db.add(obj)

    await db.flush()
    await db.commit()
    log.info(f"  ok    Created {len(records)} maintenance logs")


# ---------------------------------------------------------------------------
# 6. Fuel Logs
# ---------------------------------------------------------------------------

async def seed_fuel_logs(
    db: AsyncSession,
    V: dict[str, Vehicle],
    trips: list[Trip],
    fm: User,
) -> None:
    check = await db.execute(select(FuelLog))
    if check.scalars().first():
        log.info("  skip  Fuel logs already exist.")
        return

    # Quick lookup: source -> trip
    tmap = {t.source: t for t in trips}

    def fl(vreg, liters, cost, log_date, odo=None, trip_source=None):
        return FuelLog(
            vehicle_id=V[vreg].id,
            trip_id=tmap[trip_source].id if trip_source and trip_source in tmap else None,
            liters=Decimal(str(liters)),
            cost=Decimal(str(cost)),
            date=log_date,
            odometer_at_fill=Decimal(str(odo)) if odo else None,
            created_by=fm.id,
        )

    logs = [
        # Linked to completed trips
        fl("GJ01AB9981", 16.20,  1296,  d(149), 182054, "Vatva Industrial Area"),
        fl("GJ06EF7712", 81.00,  6480,  d(119), 97600,  "Ahmedabad Depot"),
        fl("GJ01CD3388", 62.40,  4992,  d(89),  311120, "Sanand Industrial Estate"),
        fl("GJ01AB4521",  9.60,   768,  d(60),  73950,  "Gandhinagar Depot"),
        fl("GJ06EF7712", 28.50,  2280,  d(29),  98200,  "Baroda Fuel Depot"),
        # Standalone fill-ups (no trip)
        fl("GJ01AB9981", 80.00,  6400,  d(100), 181900),
        fl("GJ01CD3388", 55.00,  4400,  d(70),  311000),
        fl("GJ01AB1120", 28.00,  2240,  d(20),  66000),
        fl("GJ01KL9900", 32.00,  2560,  d(15),  41000),
        fl("GJ06EF7712", 60.00,  4800,  d(7),   98100),
    ]

    for obj in logs:
        db.add(obj)
    await db.flush()
    await db.commit()
    log.info(f"  ok    Created {len(logs)} fuel logs")


# ---------------------------------------------------------------------------
# 7. Expenses
# ---------------------------------------------------------------------------

async def seed_expenses(
    db: AsyncSession,
    V: dict[str, Vehicle],
    trips: list[Trip],
    fm: User,
) -> None:
    check = await db.execute(select(Expense))
    if check.scalars().first():
        log.info("  skip  Expenses already exist.")
        return

    tmap = {t.source: t for t in trips}

    def ex(vreg, trip_source, etype, desc, cost, exp_date):
        return Expense(
            vehicle_id=V[vreg].id,
            trip_id=tmap[trip_source].id if trip_source and trip_source in tmap else None,
            expense_type=etype,
            description=desc,
            cost=Decimal(str(cost)),
            date=exp_date,
            created_by=fm.id,
        )

    T = ExpenseTypeEnum
    records = [
        # Tolls on completed trips
        ex("GJ01AB9981", "Vatva Industrial Area",    T.toll,               "NH-48 Nadiad Toll Plaza (both ways)",              340,   d(149)),
        ex("GJ06EF7712", "Ahmedabad Depot",          T.toll,               "Surat Expressway Toll — 2 axle",                   820,   d(119)),
        ex("GJ01CD3388", "Sanand Industrial Estate", T.toll,               "Rajkot Ring Road Toll — heavy vehicle",            420,   d(89)),
        ex("GJ01AB4521", "Gandhinagar Depot",        T.toll,               "SH-17 Mehsana Toll Plaza",                         120,   d(60)),
        ex("GJ06EF7712", "Baroda Fuel Depot",        T.toll,               "Vadodara–Anand Expressway Toll",                   280,   d(29)),
        # Maintenance-related
        ex("GJ01AB9981", None,                       T.maintenance_related,"Radiator replacement — TRUCK-11",                18500,   d(28)),
        ex("GJ06EF7712", None,                       T.maintenance_related,"Brake overhaul — TRUCK-07",                      9200,   d(44)),
        ex("GJ01AB1120", None,                       T.maintenance_related,"Body repair — MINI-03",                          6800,   d(58)),
        # Insurance (annual)
        ex("GJ01AB9981", None,                       T.insurance,          "Annual commercial vehicle insurance — TRUCK-11",  28500,  d(180)),
        ex("GJ06EF7712", None,                       T.insurance,          "Annual commercial vehicle insurance — TRUCK-07",  34000,  d(180)),
        ex("GJ01CD3388", None,                       T.insurance,          "Annual commercial vehicle insurance — BUS-02",    42000,  d(180)),
        # RTO registration
        ex("GJ01CD3388", None,                       T.registration_fee,   "Annual RTO road tax — BUS-02",                   12000,  d(90)),
    ]

    for obj in records:
        db.add(obj)
    await db.flush()
    await db.commit()
    log.info(f"  ok    Created {len(records)} expense records")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    log.info("=" * 62)
    log.info("  TransitOps — Demo Data Seeder")
    log.info("=" * 62)

    async with async_session_maker() as db:
        log.info("\n[1/7] Users")
        users = await seed_users(db)
        fm = users["manager@transitops.com"]

        log.info("\n[2/7] Vehicles")
        vehicles = await seed_vehicles(db)

        log.info("\n[3/7] Drivers")
        drivers = await seed_drivers(db)

        log.info("\n[4/7] Trips")
        trips = await seed_trips(db, vehicles, drivers)

        log.info("\n[5/7] Maintenance Logs")
        await seed_maintenance(db, vehicles)

        log.info("\n[6/7] Fuel Logs")
        await seed_fuel_logs(db, vehicles, trips, fm)

        log.info("\n[7/7] Expenses")
        await seed_expenses(db, vehicles, trips, fm)

    log.info("\n" + "=" * 62)
    log.info("  Demo seed complete!")
    log.info("=" * 62)
    log.info("\n  Login credentials (password: password123)")
    log.info("  Fleet Manager     ->  manager@transitops.com")
    log.info("  Driver            ->  driver@transitops.com")
    log.info("  Safety Officer    ->  safety@transitops.com")
    log.info("  Financial Analyst ->  financial@transitops.com\n")


if __name__ == "__main__":
    asyncio.run(main())
