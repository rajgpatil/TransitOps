from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user, require_permission
from app.core.permissions import ModuleEnum, ActionEnum
from app.core.config import settings
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, UserResponse, TokenRefreshRequest

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Authenticate user by email and password. Returns Access & Refresh JWTs."""
    generic_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Fetch user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalars().first()

    # 2. Check user and password (no email enumeration)
    if user is None:
        # Run password verification dummy to protect against timing attacks
        verify_password(login_data.password, "")
        raise generic_exception

    if not verify_password(login_data.password, user.hashed_password):
        raise generic_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generate tokens
    access_token = create_access_token(subject=user.email, role=user.role.value)
    refresh_token = create_refresh_token(subject=user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Verifies refresh token and issues a new access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(refresh_data.refresh_token)
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Query the user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user is None or not user.is_active:
        raise credentials_exception

    # Generate a new access token and fresh refresh token (refresh token rotation)
    access_token = create_access_token(subject=user.email, role=user.role.value)
    new_refresh_token = create_refresh_token(subject=user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> User:
    """Return current authenticated user's profile info."""
    return current_user


# Verification/test endpoint to validate RBAC behavior (dev/test only)
@router.get("/test-rbac", response_model=dict)
async def test_rbac(
    current_user: User = Depends(require_permission(ModuleEnum.vehicles, ActionEnum.create))
):
    """Enforce vehicle creation permission for testing RBAC."""
    return {"message": "Access granted: you can create vehicles"}
