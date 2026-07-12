import pytest
from decimal import Decimal
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, RoleEnum
from app.models.vehicle import Vehicle, VehicleStatusEnum, VehicleTypeEnum
from app.models.driver import Driver, DriverStatusEnum, LicenseCategoryEnum
from app.models.trip import Trip, TripStatusEnum


def get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.email, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


async def _seed_fleet(db: AsyncSession):
    """Seed one vehicle, one driver, and one completed trip for KPI testing."""
    vehicle = Vehicle(
        registration_number="KPI-001",
        name="KPI Truck",
        type=VehicleTypeEnum.truck,
        max_load_capacity=Decimal("5000.00"),
        odometer=Decimal("10000.00"),
        acquisition_cost=Decimal("50000.00"),
        region="Central",
        status=VehicleStatusEnum.on_trip,
    )
    driver = Driver(
        name="Driver KPI",
        license_number="LKPI001",
        license_category=LicenseCategoryEnum.C,
        license_expiry=date.today() + timedelta(days=365),
        contact_number="+1-555-0100",
        status=DriverStatusEnum.on_trip,
    )
    db.add(vehicle)
    db.add(driver)
    await db.flush()

    trip = Trip(
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        source="City A",
        destination="City B",
        cargo_weight=Decimal("1000.00"),
        planned_distance=Decimal("250.00"),
        status=TripStatusEnum.completed,
        actual_distance=Decimal("250.00"),
        fuel_consumed=Decimal("50.00"),
        revenue=Decimal("5000.00"),
        final_odometer=Decimal("10250.00"),
    )
    db.add(trip)
    await db.flush()
    return vehicle, driver, trip


@pytest.mark.asyncio
async def test_dashboard_kpis_fleet_manager(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Fleet Manager sees all KPI fields including cost and ROI."""
    await _seed_fleet(db_session)
    fm = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm)

    response = await client.get("/api/dashboard/kpis", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # All vehicle/trip counts should be non-None
    assert data["active_vehicles_count"] is not None
    assert data["available_vehicles_count"] is not None
    assert data["active_trips_count"] is not None
    assert data["fleet_utilization_pct"] is not None
    assert data["fuel_efficiency"] is not None
    # Cost fields accessible to FM
    assert data["operational_cost"] is not None


@pytest.mark.asyncio
async def test_dashboard_kpis_safety_officer_no_cost(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Safety Officer sees fleet metrics but NOT cost/ROI fields."""
    await _seed_fleet(db_session)
    so = test_users[RoleEnum.safety_officer.value]
    headers = get_auth_headers(so)

    response = await client.get("/api/dashboard/kpis", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Operational fields visible
    assert data["active_vehicles_count"] is not None
    assert data["fleet_utilization_pct"] is not None
    # Cost/ROI fields should NOT be returned (None)
    assert data["operational_cost"] is None
    assert data["roi"] is None


@pytest.mark.asyncio
async def test_dashboard_kpis_driver_own_trips_only(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Driver sees only own trip counts and fuel efficiency; fleet/cost fields are None."""
    await _seed_fleet(db_session)
    driver_user = test_users[RoleEnum.driver.value]
    headers = get_auth_headers(driver_user)

    response = await client.get("/api/dashboard/kpis", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Fleet-level fields must be None
    assert data["active_vehicles_count"] is None
    assert data["drivers_on_duty_count"] is None
    assert data["operational_cost"] is None
    assert data["roi"] is None
    # Per-driver fields present (even if 0 since driver name won't match)
    assert data["active_trips_count"] is not None
    assert data["fuel_efficiency"] is not None


@pytest.mark.asyncio
async def test_dashboard_kpis_filter_by_vehicle_type(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """KPI filter by vehicle_type returns subset of fleet."""
    await _seed_fleet(db_session)
    fm = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm)

    # Filter for a non-existent type — counts should be 0
    response = await client.get("/api/dashboard/kpis?vehicle_type=van", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["active_vehicles_count"] == 0


@pytest.mark.asyncio
async def test_dashboard_charts(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """Charts endpoint returns all three chart data sections."""
    await _seed_fleet(db_session)
    fm = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm)

    response = await client.get("/api/dashboard/charts", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "trip_status_breakdown" in data
    assert "cost_trend" in data
    assert "utilization_trend" in data

    # cost_trend always returns 6 months
    assert len(data["cost_trend"]) == 6
    # utilization_trend always returns 7 days
    assert len(data["utilization_trend"]) == 7


@pytest.mark.asyncio
async def test_dashboard_kpis_empty_fleet(
    client: AsyncClient, test_users: dict[str, User], db_session: AsyncSession
):
    """KPIs on an empty fleet return zero counts (no errors)."""
    fm = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm)

    response = await client.get("/api/dashboard/kpis", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["active_vehicles_count"] == 0
    assert data["fleet_utilization_pct"] == 0.0
    assert data["fuel_efficiency"] == 0.0


@pytest.mark.asyncio
async def test_dashboard_unauthenticated(client: AsyncClient):
    """Unauthenticated requests return 401."""
    response = await client.get("/api/dashboard/kpis")
    assert response.status_code == 401
