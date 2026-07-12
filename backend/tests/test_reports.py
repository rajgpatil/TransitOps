import pytest
import io
from decimal import Decimal
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, RoleEnum
from app.models.vehicle import Vehicle, VehicleStatusEnum, VehicleTypeEnum
from app.models.driver import Driver, DriverStatusEnum, LicenseCategoryEnum
from app.models.trip import Trip, TripStatusEnum
from app.models.fuel_log import FuelLog
from app.models.maintenance import MaintenanceLog, MaintenanceStatusEnum


def get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.email, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


async def _seed_vehicle_with_data(db: AsyncSession, fm_user) -> Vehicle:
    """Seed a vehicle with a completed trip and fuel log for reporting."""
    vehicle = Vehicle(
        registration_number="RPT-001",
        name="Report Truck",
        type=VehicleTypeEnum.truck,
        max_load_capacity=Decimal("8000.00"),
        odometer=Decimal("20000.00"),
        acquisition_cost=Decimal("80000.00"),
        region="West",
        status=VehicleStatusEnum.available,
    )
    driver = Driver(
        name="Report Driver",
        license_number="LRPT001",
        license_category=LicenseCategoryEnum.C,
        license_expiry=date.today() + timedelta(days=365),
        contact_number="+1-555-0200",
        status=DriverStatusEnum.available,
    )
    db.add(vehicle)
    db.add(driver)
    await db.flush()

    trip = Trip(
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        source="Port A",
        destination="Port B",
        cargo_weight=Decimal("3000.00"),
        planned_distance=Decimal("400.00"),
        status=TripStatusEnum.completed,
        actual_distance=Decimal("400.00"),
        fuel_consumed=Decimal("80.00"),
        revenue=Decimal("8000.00"),
        final_odometer=Decimal("20400.00"),
    )
    db.add(trip)

    fuel_log = FuelLog(
        vehicle_id=vehicle.id,
        date=date.today(),
        liters=Decimal("80.00"),
        cost=Decimal("160.00"),
        created_by=fm_user.id,
    )
    db.add(fuel_log)
    await db.flush()
    return vehicle



@pytest.mark.asyncio
async def test_reports_fuel_efficiency(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Fuel efficiency report returns per-vehicle efficiency data."""
    fm = test_users[RoleEnum.fleet_manager.value]
    await _seed_vehicle_with_data(db_session, fm)
    headers = get_auth_headers(fm)

    response = await client.get("/api/reports/fuel-efficiency", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    item = next((d for d in data if d["registration_number"] == "RPT-001"), None)
    assert item is not None
    assert item["total_distance"] == 400.0
    assert item["total_fuel_consumed"] == 80.0
    # 400 / 80 = 5.0 km/L
    assert item["fuel_efficiency"] == 5.0


@pytest.mark.asyncio
async def test_reports_fuel_efficiency_empty(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Fuel efficiency returns N/A when vehicle has no completed trips."""
    # Seed vehicle with no trips
    vehicle = Vehicle(
        registration_number="NORPT-001",
        name="No-trip Truck",
        type=VehicleTypeEnum.van,
        max_load_capacity=Decimal("2000.00"),
        odometer=Decimal("0.00"),
        acquisition_cost=Decimal("20000.00"),
        region="East",
        status=VehicleStatusEnum.available,
    )
    db_session.add(vehicle)
    await db_session.flush()

    fm = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm)

    response = await client.get("/api/reports/fuel-efficiency", headers=headers)
    assert response.status_code == 200
    data = response.json()
    item = next((d for d in data if d["registration_number"] == "NORPT-001"), None)
    assert item is not None
    assert item["fuel_efficiency"] == "N/A"


@pytest.mark.asyncio
async def test_reports_utilization(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Utilization report returns daily records for requested date range."""
    fm = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm)

    start = (date.today() - timedelta(days=6)).isoformat()
    end = date.today().isoformat()
    response = await client.get(
        f"/api/reports/utilization?start_date={start}&end_date={end}", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7  # 7 days


@pytest.mark.asyncio
async def test_reports_operational_cost(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Operational cost report sums fuel + maintenance + other expenses per vehicle."""
    fm = test_users[RoleEnum.fleet_manager.value]
    await _seed_vehicle_with_data(db_session, fm)
    headers = get_auth_headers(fm)

    response = await client.get("/api/reports/operational-cost", headers=headers)
    assert response.status_code == 200
    data = response.json()
    item = next((d for d in data if d["registration_number"] == "RPT-001"), None)
    assert item is not None
    assert float(item["fuel_cost"]) == 160.0
    assert float(item["total_cost"]) >= 160.0


@pytest.mark.asyncio
async def test_reports_vehicle_roi(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Vehicle ROI report computes ROI from revenue and costs."""
    fm = test_users[RoleEnum.fleet_manager.value]
    await _seed_vehicle_with_data(db_session, fm)
    headers = get_auth_headers(fm)

    response = await client.get("/api/reports/vehicle-roi", headers=headers)
    assert response.status_code == 200
    data = response.json()
    item = next((d for d in data if d["registration_number"] == "RPT-001"), None)
    assert item is not None
    # ROI = (8000 - 0 - 160) / 80000 * 100 = 9.8%
    assert item["roi"] != "N/A"
    assert float(item["roi"]) > 0


@pytest.mark.asyncio
async def test_reports_vehicle_roi_no_acquisition_cost(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Vehicle with acquisition_cost=0 returns 'N/A' for ROI."""
    vehicle = Vehicle(
        registration_number="ROI-ZERO",
        name="Free Truck",
        type=VehicleTypeEnum.truck,
        max_load_capacity=Decimal("5000.00"),
        odometer=Decimal("0.00"),
        acquisition_cost=Decimal("0.00"),
        region="East",
        status=VehicleStatusEnum.available,
    )
    db_session.add(vehicle)
    await db_session.flush()

    fm = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm)

    response = await client.get("/api/reports/vehicle-roi", headers=headers)
    assert response.status_code == 200
    data = response.json()
    item = next((d for d in data if d["registration_number"] == "ROI-ZERO"), None)
    assert item is not None
    assert item["roi"] == "N/A"


@pytest.mark.asyncio
async def test_reports_csv_export_fuel_efficiency(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """CSV export returns text/csv content with expected headers."""
    fm = test_users[RoleEnum.fleet_manager.value]
    await _seed_vehicle_with_data(db_session, fm)
    headers = get_auth_headers(fm)

    response = await client.get(
        "/api/reports/export?report_type=fuel-efficiency", headers=headers
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    content = response.text
    # First line should be CSV headers
    first_line = content.split("\n")[0]
    assert "Registration Number" in first_line


@pytest.mark.asyncio
async def test_reports_csv_export_operational_cost(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """CSV export for operational-cost includes correct headers."""
    fm = test_users[RoleEnum.fleet_manager.value]
    await _seed_vehicle_with_data(db_session, fm)
    headers = get_auth_headers(fm)

    response = await client.get(
        "/api/reports/export?report_type=operational-cost", headers=headers
    )
    assert response.status_code == 200
    content = response.text
    first_line = content.split("\n")[0]
    assert "Total Cost" in first_line


@pytest.mark.asyncio
async def test_reports_safety_officer_forbidden(
    client: AsyncClient, test_users: dict[str, User]
):
    """Safety Officer cannot access reports endpoints (403)."""
    so = test_users[RoleEnum.safety_officer.value]
    headers = get_auth_headers(so)

    response = await client.get("/api/reports/fuel-efficiency", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reports_driver_forbidden(
    client: AsyncClient, test_users: dict[str, User]
):
    """Driver cannot access reports endpoints (403)."""
    driver_user = test_users[RoleEnum.driver.value]
    headers = get_auth_headers(driver_user)

    response = await client.get("/api/reports/vehicle-roi", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reports_unauthenticated(client: AsyncClient):
    """Unauthenticated requests return 401."""
    response = await client.get("/api/reports/fuel-efficiency")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_reports_csv_invalid_report_type(
    client: AsyncClient, test_users: dict[str, User]
):
    """Invalid report_type query param returns 422 validation error."""
    fm = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm)

    response = await client.get(
        "/api/reports/export?report_type=invalid-type", headers=headers
    )
    assert response.status_code == 422
