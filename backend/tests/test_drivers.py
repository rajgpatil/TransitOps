import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, RoleEnum
from app.models.driver import Driver, DriverStatusEnum, LicenseCategoryEnum


def get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.email, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_driver_happy_path_crud(client: AsyncClient, test_users: dict[str, User]):
    """Verify happy path CRUD operations for Drivers."""
    so_user = test_users[RoleEnum.safety_officer.value]
    headers = get_auth_headers(so_user)

    # 1. Create
    future_expiry = (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
    driver_data = {
        "name": "Jane Doe",
        "license_number": "DL-9999988-XY",
        "license_category": "CE",
        "license_expiry": future_expiry,
        "contact_number": "+1234567890",
        "safety_score": 95.50,
        "status": "available"
    }
    response = await client.post("/api/drivers", json=driver_data, headers=headers)
    assert response.status_code == 201
    res_json = response.json()
    assert res_json["name"] == "Jane Doe"
    assert res_json["license_number"] == "DL-9999988-XY"
    assert res_json["is_license_expired"] is False
    assert res_json["is_assignable"] is True
    driver_id = res_json["id"]

    # 2. Get Detail
    response = await client.get(f"/api/drivers/{driver_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Jane Doe"

    # 3. Update (Fleet Manager edit name or safety score)
    fm_user = test_users[RoleEnum.fleet_manager.value]
    fm_headers = get_auth_headers(fm_user)
    update_data = {
        "name": "Jane Doe Updated",
        "safety_score": 90.00
    }
    response = await client.put(f"/api/drivers/{driver_id}", json=update_data, headers=fm_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Jane Doe%s" % " Updated"
    assert float(response.json()["safety_score"]) == 90.00

    # 4. List
    response = await client.get("/api/drivers", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # 5. Delete (Remove)
    response = await client.delete(f"/api/drivers/{driver_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == driver_id

    # 6. Verify Deleted
    response = await client.get(f"/api/drivers/{driver_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_driver_duplicate_license_number(client: AsyncClient, test_users: dict[str, User]):
    """Verify duplicate license_number returns 409."""
    so_user = test_users[RoleEnum.safety_officer.value]
    headers = get_auth_headers(so_user)

    future_expiry = (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
    driver_data = {
        "name": "John Smith",
        "license_number": "DL-11111-DUP",
        "license_category": "C",
        "license_expiry": future_expiry,
        "contact_number": "+1234567890",
        "safety_score": 100.00
    }
    # Create first
    response = await client.post("/api/drivers", json=driver_data, headers=headers)
    assert response.status_code == 201

    # Create second with duplicate license
    driver_data2 = {
        "name": "John Smith Duplicate",
        "license_number": "DL-11111-DUP",
        "license_category": "B",
        "license_expiry": future_expiry,
        "contact_number": "+0987654321",
        "safety_score": 95.00
    }
    response = await client.post("/api/drivers", json=driver_data2, headers=headers)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_driver_safety_score_bounds(client: AsyncClient, test_users: dict[str, User]):
    """Verify safety score limits (0–100) trigger 422 error."""
    so_user = test_users[RoleEnum.safety_officer.value]
    headers = get_auth_headers(so_user)

    future_expiry = (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
    driver_data = {
        "name": "Invalid Score Driver",
        "license_number": "DL-100-VAL",
        "license_category": "B",
        "license_expiry": future_expiry,
        "contact_number": "+1234567890",
        "safety_score": 105.00  # Invalid > 100
    }
    response = await client.post("/api/drivers", json=driver_data, headers=headers)
    assert response.status_code == 422

    driver_data["safety_score"] = -5.00  # Invalid < 0
    response = await client.post("/api/drivers", json=driver_data, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_driver_past_license_expiry(client: AsyncClient, test_users: dict[str, User]):
    """Verify past license expiry date is accepted at creation, but sets is_license_expired=True and is_assignable=False."""
    so_user = test_users[RoleEnum.safety_officer.value]
    headers = get_auth_headers(so_user)

    past_expiry = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    driver_data = {
        "name": "Expired Driver",
        "license_number": "DL-EXPIRED-99",
        "license_category": "B",
        "license_expiry": past_expiry,
        "contact_number": "+1234567890",
        "safety_score": 90.00
    }
    response = await client.post("/api/drivers", json=driver_data, headers=headers)
    assert response.status_code == 201
    res_json = response.json()
    assert res_json["is_license_expired"] is True
    assert res_json["is_assignable"] is False


@pytest.mark.asyncio
async def test_driver_available_filtering(client: AsyncClient, test_users: dict[str, User]):
    """Verify GET /api/drivers/available excludes expired or suspended drivers."""
    so_user = test_users[RoleEnum.safety_officer.value]
    headers = get_auth_headers(so_user)

    # 1. Create a valid available driver
    future_expiry = (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
    d1 = {
        "name": "Assignable Driver",
        "license_number": "DL-ASSIGN-01",
        "license_category": "B",
        "license_expiry": future_expiry,
        "contact_number": "+1234567890",
        "status": "available"
    }
    await client.post("/api/drivers", json=d1, headers=headers)

    # 2. Create an expired driver
    past_expiry = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    d2 = {
        "name": "Expired Driver X",
        "license_number": "DL-ASSIGN-02",
        "license_category": "B",
        "license_expiry": past_expiry,
        "contact_number": "+1234567890",
        "status": "available"
    }
    await client.post("/api/drivers", json=d2, headers=headers)

    # 3. Create a suspended driver
    d3 = {
        "name": "Suspended Driver Y",
        "license_number": "DL-ASSIGN-03",
        "license_category": "B",
        "license_expiry": future_expiry,
        "contact_number": "+1234567890",
        "status": "suspended"
    }
    await client.post("/api/drivers", json=d3, headers=headers)

    # Fetch available drivers
    response = await client.get("/api/drivers/available", headers=headers)
    assert response.status_code == 200
    drivers_list = response.json()
    
    # Excludes expired/suspended drivers
    license_numbers = [d["license_number"] for d in drivers_list]
    assert "DL-ASSIGN-01" in license_numbers
    assert "DL-ASSIGN-02" not in license_numbers
    assert "DL-ASSIGN-03" not in license_numbers


@pytest.mark.asyncio
async def test_driver_rbac_restrictions(client: AsyncClient, test_users: dict[str, User]):
    """Verify that non-Safety-Officers cannot create drivers."""
    driver_user = test_users[RoleEnum.driver.value]
    headers = get_auth_headers(driver_user)

    future_expiry = (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
    driver_data = {
        "name": "Forbid Driver",
        "license_number": "DL-FORBID-00",
        "license_category": "B",
        "license_expiry": future_expiry,
        "contact_number": "+1234567890"
    }
    response = await client.post("/api/drivers", json=driver_data, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to perform this action"
