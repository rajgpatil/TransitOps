from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.core.permissions import ModuleEnum, ActionEnum, has_permission
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    token: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate JWT access token and return the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
        
    try:
        payload = decode_token(token.credentials)
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "access":
            raise credentials_exception
    except (JWTError, AttributeError):
        raise credentials_exception

    # Query the user in the database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_permission(module: ModuleEnum, action: ActionEnum):
    """Factory dependency to enforce Role-Based Access Control on endpoints."""
    async def permission_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not has_permission(current_user.role, module, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user
    return permission_dependency
