import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, RoleEnum
from app.models.vehicle import Vehicle, VehicleStatusEnum, VehicleTypeEnum


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
async def test_finance_happy_path(client: AsyncClient, db_session: AsyncSession, test_users: dict[str, User]):
    """Verify fuel log and expense creations, and correct cost summing via GET /api/vehicles/{id}/costs."""
    fa_user = test_users[RoleEnum.financial_analyst.value]
    headers = get_auth_headers(fa_user)

    vehicle = await create_test_vehicle(db_session, "REG-FIN-01")

    # 1. Create Fuel Log
    fuel_data = {
        "vehicle_id": vehicle.id,
        "liters": 80.00,
        "cost": 120.00,
        "date": "2026-07-12",
        "odometer_at_fill": 10100.00
    }
    res_fuel = await client.post("/api/fuel-logs", json=fuel_data, headers=headers)
    assert res_fuel.status_code == 201

    # 2. Create Expense Log
    expense_data = {
        "vehicle_id": vehicle.id,
        "expense_type": "toll",
        "cost": 45.00,
        "date": "2026-07-12",
        "description": "Bridge toll"
    }
    res_expense = await client.post("/api/expenses", json=expense_data, headers=headers)
    assert res_expense.status_code == 201

    # Add a maintenance cost by creating and closing a maintenance log (we can use Fleet Manager for this)
    fm_user = test_users[RoleEnum.fleet_manager.value]
    fm_headers = get_auth_headers(fm_user)
    res_maint = await client.post("/api/maintenance", json={
        "vehicle_id": vehicle.id,
        "maintenance_type": "inspection",
        "description": "Annual vehicle inspection",
        "cost": 150.00
    }, headers=fm_headers)
    maint_id = res_maint.json()["id"]
    await client.post(f"/api/maintenance/{maint_id}/close", json={"cost": 150.00}, headers=fm_headers)

    # 3. Retrieve operational costs via vehicles costs endpoint
    response = await client.get(f"/api/vehicles/{vehicle.id}/costs", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert float(res_data["fuel_cost"]) == 120.00
    assert float(res_data["maintenance_cost"]) == 150.00
    assert float(res_data["other_expense_cost"]) == 45.00
    assert float(res_data["total_cost"]) == 315.00  # 120 + 150 + 45


@pytest.mark.asyncio
async def test_finance_validation_errors(client: AsyncClient, db_session: AsyncSession, test_users: dict[str, User]):
    """Verify negative cost/liters are rejected, future dates are accepted."""
    fa_user = test_users[RoleEnum.financial_analyst.value]
    headers = get_auth_headers(fa_user)

    vehicle = await create_test_vehicle(db_session, "REG-FIN-02")

    # 1. Negative liters/cost in fuel log -> validation error (422)
    bad_fuel = {
        "vehicle_id": vehicle.id,
        "liters": -50.00,
        "cost": 100.00,
        "date": "2026-07-12"
    }
    response = await client.post("/api/fuel-logs", json=bad_fuel, headers=headers)
    assert response.status_code == 422

    bad_fuel["liters"] = 50.00
    bad_fuel["cost"] = -10.00
    response = await client.post("/api/fuel-logs", json=bad_fuel, headers=headers)
    assert response.status_code == 422

    # 2. Negative cost in expense -> validation error (422)
    bad_expense = {
        "vehicle_id": vehicle.id,
        "expense_type": "parking",
        "cost": -15.00,
        "date": "2026-07-12"
    }
    response = await client.post("/api/expenses", json=bad_expense, headers=headers)
    assert response.status_code == 422

    # 3. Future-dated entry -> accepted
    future_date = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    good_fuel = {
        "vehicle_id": vehicle.id,
        "liters": 50.00,
        "cost": 100.00,
        "date": future_date
    }
    response = await client.post("/api/fuel-logs", json=good_fuel, headers=headers)
    assert response.status_code == 201
    assert response.json()["date"] == future_date
