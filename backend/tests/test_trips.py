import pytest
import asyncio
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, RoleEnum
from app.models.vehicle import Vehicle, VehicleStatusEnum, VehicleTypeEnum
from app.models.driver import Driver, DriverStatusEnum, LicenseCategoryEnum
from app.models.trip import Trip, TripStatusEnum


def get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.email, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


async def create_test_vehicle(db: AsyncSession, reg_num: str, status: VehicleStatusEnum = VehicleStatusEnum.available) -> Vehicle:
    vehicle = Vehicle(
        registration_number=reg_num,
        name="Test Truck",
        type=VehicleTypeEnum.truck,
        max_load_capacity=5000.00,
        odometer=10000.00,
        acquisition_cost=40000.00,
        status=status
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def create_test_driver(db: AsyncSession, lic_num: str, status: DriverStatusEnum = DriverStatusEnum.available, expiry: date = None) -> Driver:
    if expiry is None:
        expiry = date.today() + timedelta(days=365)
    driver = Driver(
        name="Test Driver",
        license_number=lic_num,
        license_category=LicenseCategoryEnum.CE,
        license_expiry=expiry,
        contact_number="+1234567890",
        safety_score=95.00,
        status=status
    )
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return driver


@pytest.mark.asyncio
async def test_trip_happy_path_lifecycle(client: AsyncClient, db_session: AsyncSession, test_users: dict[str, User]):
    """Verify create -> dispatch -> complete, and create -> dispatch -> cancel, and draft -> cancel."""
    driver_user = test_users[RoleEnum.driver.value]
    headers = get_auth_headers(driver_user)

    vehicle = await create_test_vehicle(db_session, "REG-LIFE-01")
    driver = await create_test_driver(db_session, "LIC-LIFE-01")

    # 1. Create Draft Trip
    trip_data = {
        "source": "New York",
        "destination": "Boston",
        "vehicle_id": vehicle.id,
        "driver_id": driver.id,
        "cargo_weight": 2000.00,
        "planned_distance": 350.00,
        "revenue": 1200.00
    }
    response = await client.post("/api/trips", json=trip_data, headers=headers)
    assert response.status_code == 201
    trip_id = response.json()["id"]
    assert response.json()["status"] == "draft"

    # 2. Dispatch Trip
    response = await client.post(f"/api/trips/{trip_id}/dispatch", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "dispatched"
    
    # Verify vehicle and driver are on_trip
    await db_session.refresh(vehicle)
    await db_session.refresh(driver)
    assert vehicle.status == VehicleStatusEnum.on_trip
    assert driver.status == DriverStatusEnum.on_trip

    # 3. Complete Trip
    complete_data = {
        "actual_distance": 360.00,
        "fuel_consumed": 120.00,
        "final_odometer": 10360.00,
        "revenue": 1300.00
    }
    response = await client.post(f"/api/trips/{trip_id}/complete", json=complete_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    
    # Verify vehicle/driver released and vehicle odometer updated
    await db_session.refresh(vehicle)
    await db_session.refresh(driver)
    assert vehicle.status == VehicleStatusEnum.available
    assert driver.status == DriverStatusEnum.available
    assert float(vehicle.odometer) == 10360.00

    # 4. Dispatch -> Cancel flow
    trip_data["registration_number"] = "REG-LIFE-02"
    vehicle2 = await create_test_vehicle(db_session, "REG-LIFE-02")
    driver2 = await create_test_driver(db_session, "LIC-LIFE-02")
    trip_data["vehicle_id"] = vehicle2.id
    trip_data["driver_id"] = driver2.id

    response = await client.post("/api/trips", json=trip_data, headers=headers)
    trip_id2 = response.json()["id"]
    await client.post(f"/api/trips/{trip_id2}/dispatch", headers=headers)

    response = await client.post(f"/api/trips/{trip_id2}/cancel", json={"reason": "Mechanical failure"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["cancel_reason"] == "Mechanical failure"
    
    # Verify resources restored
    await db_session.refresh(vehicle2)
    await db_session.refresh(driver2)
    assert vehicle2.status == VehicleStatusEnum.available
    assert driver2.status == DriverStatusEnum.available

    # 5. Draft -> Cancel flow
    response = await client.post("/api/trips", json=trip_data, headers=headers)
    trip_id3 = response.json()["id"]
    response = await client.post(f"/api/trips/{trip_id3}/cancel", json={"reason": "Cancelled in draft"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_trip_validation_edge_cases(client: AsyncClient, db_session: AsyncSession, test_users: dict[str, User]):
    """Verify edge cases: retired/in_shop vehicle, expired/suspended driver, overweight cargo, double complete."""
    driver_user = test_users[RoleEnum.driver.value]
    headers = get_auth_headers(driver_user)

    vehicle = await create_test_vehicle(db_session, "REG-VAL-01")
    driver = await create_test_driver(db_session, "LIC-VAL-01")

    # 1. Overweight cargo
    bad_trip_data = {
        "source": "New York",
        "destination": "Boston",
        "vehicle_id": vehicle.id,
        "driver_id": driver.id,
        "cargo_weight": 6000.00,  # exceeds 5000 max capacity
        "planned_distance": 350.00
    }
    response = await client.post("/api/trips", json=bad_trip_data, headers=headers)
    assert response.status_code == 400
    assert "exceeds vehicle maximum capacity" in response.json()["detail"]

    # 2. Retired vehicle rejected at creation/dispatch
    vehicle.status = VehicleStatusEnum.retired
    await db_session.commit()
    bad_trip_data["cargo_weight"] = 2000.00
    response = await client.post("/api/trips", json=bad_trip_data, headers=headers)
    assert response.status_code == 400
    assert "not available" in response.json()["detail"]

    # Restore vehicle and test suspended driver
    vehicle.status = VehicleStatusEnum.available
    driver.status = DriverStatusEnum.suspended
    await db_session.commit()
    response = await client.post("/api/trips", json=bad_trip_data, headers=headers)
    assert response.status_code == 400
    assert "Driver is not available" in response.json()["detail"]

    # Restore driver and test expired license
    driver.status = DriverStatusEnum.available
    driver.license_expiry = date.today() - timedelta(days=1)
    await db_session.commit()
    response = await client.post("/api/trips", json=bad_trip_data, headers=headers)
    assert response.status_code == 400
    assert "license is expired" in response.json()["detail"]

    # 3. Double complete
    driver.license_expiry = date.today() + timedelta(days=365)
    await db_session.commit()
    # Create valid trip
    response = await client.post("/api/trips", json=bad_trip_data, headers=headers)
    trip_id = response.json()["id"]
    await client.post(f"/api/trips/{trip_id}/dispatch", headers=headers)
    
    # Complete once
    complete_data = {
        "actual_distance": 350.00,
        "fuel_consumed": 100.00,
        "final_odometer": 10350.00
    }
    response = await client.post(f"/api/trips/{trip_id}/complete", json=complete_data, headers=headers)
    assert response.status_code == 200

    # Complete second time -> 409
    response = await client.post(f"/api/trips/{trip_id}/complete", json=complete_data, headers=headers)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_trip_simultaneous_dispatch_concurrency(client: AsyncClient, db_session: AsyncSession, test_users: dict[str, User]):
    """Verify simultaneous dispatch of the same vehicle fails on the second attempt."""
    driver_user = test_users[RoleEnum.driver.value]
    headers = get_auth_headers(driver_user)

    vehicle = await create_test_vehicle(db_session, "REG-CONC-01")
    driver1 = await create_test_driver(db_session, "LIC-CONC-01")
    driver2 = await create_test_driver(db_session, "LIC-CONC-02")

    # Create trip 1 and trip 2 using the SAME vehicle
    trip_data1 = {
        "source": "NYC",
        "destination": "PHL",
        "vehicle_id": vehicle.id,
        "driver_id": driver1.id,
        "cargo_weight": 2000.00,
        "planned_distance": 150.00
    }
    response = await client.post("/api/trips", json=trip_data1, headers=headers)
    trip_id1 = response.json()["id"]

    trip_data2 = {
        "source": "NYC",
        "destination": "DC",
        "vehicle_id": vehicle.id,
        "driver_id": driver2.id,
        "cargo_weight": 2000.00,
        "planned_distance": 250.00
    }
    response = await client.post("/api/trips", json=trip_data2, headers=headers)
    trip_id2 = response.json()["id"]

    # Dispatch trip 1 first (succeeds)
    response = await client.post(f"/api/trips/{trip_id1}/dispatch", headers=headers)
    assert response.status_code == 200

    # Dispatch trip 2 (must fail because the vehicle status is now on_trip)
    response = await client.post(f"/api/trips/{trip_id2}/dispatch", headers=headers)
    assert response.status_code == 400
    assert "Vehicle is not available" in response.json()["detail"]
