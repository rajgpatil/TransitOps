import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, RoleEnum
from app.models.vehicle import Vehicle, VehicleStatusEnum, VehicleTypeEnum


def get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.email, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_vehicle_happy_path_crud(client: AsyncClient, test_users: dict[str, User]):
    """Verify happy path CRUD operations for Vehicles."""
    fm_user = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm_user)

    # 1. Create
    vehicle_data = {
        "registration_number": "ABC-123-XY",
        "name": "Heavy Duty Truck 1",
        "type": "truck",
        "max_load_capacity": 5500.50,
        "odometer": 12000.00,
        "acquisition_cost": 45000.00,
        "region": "North-East",
        "status": "available"
    }
    response = await client.post("/api/vehicles", json=vehicle_data, headers=headers)
    assert response.status_code == 201
    res_json = response.json()
    assert res_json["registration_number"] == "ABC-123-XY"
    assert res_json["name"] == "Heavy Duty Truck 1"
    assert float(res_json["max_load_capacity"]) == 5500.50
    assert float(res_json["odometer"]) == 12000.00
    assert float(res_json["acquisition_cost"]) == 45000.00
    assert res_json["active_maintenance_count"] == 0
    vehicle_id = res_json["id"]

    # 2. Get Detail
    response = await client.get(f"/api/vehicles/{vehicle_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Heavy Duty Truck 1"

    # 3. Update
    update_data = {
        "name": "Heavy Duty Truck 1 Updated",
        "odometer": 12500.00
    }
    response = await client.put(f"/api/vehicles/{vehicle_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Heavy Duty Truck 1 Updated"
    assert float(response.json()["odometer"]) == 12500.00

    # 4. List
    response = await client.get("/api/vehicles", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # 5. Delete (Remove)
    response = await client.delete(f"/api/vehicles/{vehicle_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == vehicle_id

    # 6. Verify Deleted
    response = await client.get(f"/api/vehicles/{vehicle_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_vehicle_duplicate_registration_number(client: AsyncClient, test_users: dict[str, User]):
    """Verify duplicate registration_number returns 409, normalizes case."""
    fm_user = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm_user)

    vehicle_data1 = {
        "registration_number": "xyz-789-gp",
        "name": "Delivery Van A",
        "type": "van",
        "max_load_capacity": 1500.00,
        "odometer": 5000.00,
        "acquisition_cost": 22000.00
    }
    # Create first
    response = await client.post("/api/vehicles", json=vehicle_data1, headers=headers)
    assert response.status_code == 201
    assert response.json()["registration_number"] == "XYZ-789-GP"  # Normalized to uppercase

    # Create second with exact duplicate but uppercase
    vehicle_data2 = {
        "registration_number": "XYZ-789-GP",
        "name": "Delivery Van B",
        "type": "van",
        "max_load_capacity": 1800.00,
        "odometer": 2000.00,
        "acquisition_cost": 25000.00
    }
    response = await client.post("/api/vehicles", json=vehicle_data2, headers=headers)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_vehicle_validation_constraints(client: AsyncClient, test_users: dict[str, User]):
    """Verify that zero/negative capacity or cost, or pattern mismatches trigger 422."""
    fm_user = test_users[RoleEnum.fleet_manager.value]
    headers = get_auth_headers(fm_user)

    # Negative capacity
    bad_data = {
        "registration_number": "ABC-123-XY",
        "name": "Negative Capacity Truck",
        "type": "truck",
        "max_load_capacity": -500.00,
        "odometer": 12000.00,
        "acquisition_cost": 45000.00
    }
    response = await client.post("/api/vehicles", json=bad_data, headers=headers)
    assert response.status_code == 422

    # Zero capacity
    bad_data["max_load_capacity"] = 0.00
    response = await client.post("/api/vehicles", json=bad_data, headers=headers)
    assert response.status_code == 422

    # Negative odometer
    bad_data["max_load_capacity"] = 1000.00
    bad_data["odometer"] = -10.00
    response = await client.post("/api/vehicles", json=bad_data, headers=headers)
    assert response.status_code == 422

    # Invalid plate pattern
    bad_data["odometer"] = 10.00
    bad_data["registration_number"] = "PLATE_WITH_SPECIAL_$"
    response = await client.post("/api/vehicles", json=bad_data, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_vehicle_rbac_restrictions(client: AsyncClient, test_users: dict[str, User]):
    """Verify that non-Fleet-Managers cannot create, update, or delete vehicles."""
    driver_user = test_users[RoleEnum.driver.value]
    headers = get_auth_headers(driver_user)

    # 1. Non-FM Create -> 403
    vehicle_data = {
        "registration_number": "DRV-123-XY",
        "name": "Safety Truck",
        "type": "truck",
        "max_load_capacity": 5500.50,
        "odometer": 12000.00,
        "acquisition_cost": 45000.00
    }
    response = await client.post("/api/vehicles", json=vehicle_data, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to perform this action"
