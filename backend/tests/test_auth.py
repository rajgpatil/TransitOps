import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User, RoleEnum
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_users: dict[str, User]):
    """Verify that logging in with correct credentials returns valid JWT tokens."""
    login_data = {
        "email": "fleet_manager_test@transitops.com",
        "password": "password123"
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_json = response.json()
    assert "access_token" in token_json
    assert "refresh_token" in token_json
    assert token_json["token_type"] == "bearer"
    assert token_json["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_users: dict[str, User]):
    """Verify that logging in with incorrect password returns generic 401 error."""
    login_data = {
        "email": "fleet_manager_test@transitops.com",
        "password": "wrongpassword"
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Verify that logging in with non-existent email returns generic 401 error."""
    login_data = {
        "email": "nobody@transitops.com",
        "password": "password123"
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession, test_users: dict[str, User]):
    """Verify that deactivated users are blocked from logging in."""
    user = test_users["driver"]
    user.is_active = False
    await db_session.flush()
    
    login_data = {
        "email": "driver_test@transitops.com",
        "password": "password123"
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "User account is deactivated"


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient, test_users: dict[str, User]):
    """Verify that /me endpoint returns user details when sent a valid access token."""
    user = test_users["fleet_manager"]
    token = create_access_token(user.email, user.role.value)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == user.email
    assert data["role"] == user.role.value
    assert data["full_name"] == user.full_name
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Verify /me endpoint rejects requests with missing or invalid tokens."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
    
    # Invalid/Malformed token
    headers = {"Authorization": f"Bearer {'invalid' + '_token_pattern'}"}
    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_me_expired_token(client: AsyncClient, test_users: dict[str, User]):
    """Verify that expired tokens return 401."""
    user = test_users["driver"]
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)
    to_encode = {
        "sub": user.email,
        "role": user.role.value,
        "type": "access",
        "exp": expire
    }
    expired_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_users: dict[str, User]):
    """Verify that a valid refresh token generates a new access & refresh token."""
    login_data = {
        "email": "fleet_manager_test@transitops.com",
        "password": "password123"
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    refresh_token = login_response.json()["refresh_token"]
    
    refresh_data = {"refresh_token": refresh_token}
    response = await client.post("/api/auth/refresh", json=refresh_data)
    assert response.status_code == 200
    
    token_json = response.json()
    assert "access_token" in token_json
    assert "refresh_token" in token_json
    assert token_json["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """Verify that invalid refresh token returns 401 error."""
    response = await client.post("/api/auth/refresh", json={"refresh_token": "invalidrefreshtoken"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token"


@pytest.mark.asyncio
async def test_rbac_enforcement(client: AsyncClient, test_users: dict[str, User]):
    """Verify that only users with RoleEnum.fleet_manager can access the /test-rbac endpoint."""
    # 1. Fleet Manager (Allowed)
    fm_user = test_users["fleet_manager"]
    fm_token = create_access_token(fm_user.email, fm_user.role.value)
    fm_headers = {"Authorization": f"Bearer {fm_token}"}
    
    response = await client.get("/api/auth/test-rbac", headers=fm_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Access granted: you can create vehicles"
    
    # 2. Driver (Denied - 403 Forbidden)
    driver_user = test_users["driver"]
    driver_token = create_access_token(driver_user.email, driver_user.role.value)
    driver_headers = {"Authorization": f"Bearer {driver_token}"}
    
    response = await client.get("/api/auth/test-rbac", headers=driver_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to perform this action"
    
    # 3. Safety Officer (Denied - 403 Forbidden)
    so_user = test_users["safety_officer"]
    so_token = create_access_token(so_user.email, so_user.role.value)
    so_headers = {"Authorization": f"Bearer {so_token}"}
    
    response = await client.get("/api/auth/test-rbac", headers=so_headers)
    assert response.status_code == 403
