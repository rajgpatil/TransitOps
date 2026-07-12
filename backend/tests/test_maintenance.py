import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, RoleEnum
from app.models.vehicle import Vehicle, VehicleStatusEnum, VehicleTypeEnum
from app.models.maintenance import MaintenanceLog, MaintenanceStatusEnum, MaintenanceTypeEnum


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


@pytest.mark.asyncio
async def test_maintenance_happy_path(client: AsyncClient, db_session: AsyncSession, test_users: dict[str, User]):
    """Verify active maintenance log -> vehicle status in_shop -> close -> vehicle status available."""
    fm_user = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm_user)

    vehicle = await create_test_vehicle(db_session, "REG-MAINT-01")

    # 1. Create Maintenance Log
    log_data = {
        "vehicle_id": vehicle.id,
        "maintenance_type": "oil_change",
        "description": "Routine 10k oil change",
        "cost": 150.00
    }
    response = await client.post("/api/maintenance", json=log_data, headers=headers)
    assert response.status_code == 201
    log_id = response.json()["id"]
    assert response.json()["status"] == "active"

    # Verify vehicle status is in_shop
    await db_session.refresh(vehicle)
    assert vehicle.status == VehicleStatusEnum.in_shop

    # 2. Close Maintenance Log
    close_data = {
        "cost": 160.00,
        "notes": "Completed oil change and checked fluid levels"
    }
    response = await client.post(f"/api/maintenance/{log_id}/close", json=close_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "closed"
    assert float(response.json()["cost"]) == 160.00

    # Verify vehicle status is available
    await db_session.refresh(vehicle)
    assert vehicle.status == VehicleStatusEnum.available


@pytest.mark.asyncio
async def test_maintenance_concurrency_and_retirement(client: AsyncClient, db_session: AsyncSession, test_users: dict[str, User]):
    """Verify concurrent active logs keep vehicle in_shop, and retired vehicles stay retired."""
    fm_user = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm_user)

    vehicle = await create_test_vehicle(db_session, "REG-MAINT-02")

    # 1. Open two maintenance logs for the same vehicle
    log_data1 = {
        "vehicle_id": vehicle.id,
        "maintenance_type": "tire_replacement",
        "description": "Replacing front tires"
    }
    log_data2 = {
        "vehicle_id": vehicle.id,
        "maintenance_type": "brake_service",
        "description": "Replacing rear brake pads"
    }

    res1 = await client.post("/api/maintenance", json=log_data1, headers=headers)
    res2 = await client.post("/api/maintenance", json=log_data2, headers=headers)
    assert res1.status_code == 201
    assert res2.status_code == 201
    log1_id = res1.json()["id"]
    log2_id = res2.json()["id"]

    await db_session.refresh(vehicle)
    assert vehicle.status == VehicleStatusEnum.in_shop

    # 2. Close the first log
    await client.post(f"/api/maintenance/{log1_id}/close", json={"cost": 400.00}, headers=headers)
    
    # Vehicle must still be in_shop because the second log is active
    await db_session.refresh(vehicle)
    assert vehicle.status == VehicleStatusEnum.in_shop

    # 3. Close the second log
    await client.post(f"/api/maintenance/{log2_id}/close", json={"cost": 250.00}, headers=headers)

    # Vehicle is now available
    await db_session.refresh(vehicle)
    assert vehicle.status == VehicleStatusEnum.available

    # 4. Retired preservation
    vehicle.status = VehicleStatusEnum.retired
    await db_session.commit()

    res3 = await client.post("/api/maintenance", json=log_data1, headers=headers)
    log3_id = res3.json()["id"]
    
    # Must remain retired even when in maintenance
    await db_session.refresh(vehicle)
    assert vehicle.status == VehicleStatusEnum.retired

    # Close log
    await client.post(f"/api/maintenance/{log3_id}/close", json={"cost": 100.00}, headers=headers)
    await db_session.refresh(vehicle)
    assert vehicle.status == VehicleStatusEnum.retired


@pytest.mark.asyncio
async def test_maintenance_on_trip_vehicle_blocked(client: AsyncClient, db_session: AsyncSession, test_users: dict[str, User]):
    """Verify we cannot start maintenance on a vehicle that is currently on_trip."""
    fm_user = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm_user)

    vehicle = await create_test_vehicle(db_session, "REG-MAINT-03", status=VehicleStatusEnum.on_trip)

    log_data = {
        "vehicle_id": vehicle.id,
        "maintenance_type": "body_work",
        "description": "Repair scratch on driver door"
    }
    response = await client.post("/api/maintenance", json=log_data, headers=headers)
    assert response.status_code == 400
    assert "currently on a trip" in response.json()["detail"]
