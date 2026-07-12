import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User, RoleEnum

# Test database URL
TEST_DATABASE_URL = settings.DATABASE_URL

# Create engine with NullPool to prevent event loop connection reuse issues
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=pool.NullPool)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    """Create database tables before running tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session for a test, rolled back at completion."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(autouse=True)
def override_db_dependency(db_session: AsyncSession):
    """Override get_db dependency with the testing session."""
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide a test client using ASGITransport."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_users(db_session: AsyncSession) -> dict[str, User]:
    """Create and return a dictionary of seeded test users for each role."""
    users = {}
    roles = [
        RoleEnum.fleet_manager,
        RoleEnum.driver,
        RoleEnum.safety_officer,
        RoleEnum.financial_analyst,
    ]
    password_hash = get_password_hash("password123")
    
    for r in roles:
        email = f"{r.value}_test@transitops.com"
        user = User(
            email=email,
            hashed_password=password_hash,
            full_name=f"{r.value.title()} Test User",
            role=r,
            is_active=True,
        )
        db_session.add(user)
        users[r.value] = user
        
    await db_session.flush()  # Push users to DB to get IDs
    return users


@pytest_asyncio.fixture(autouse=True)
async def clean_database(db_session: AsyncSession):
    """Ensure database tables are cleared after each test run to isolate state."""
    yield
    from sqlalchemy import text
    await db_session.execute(text("DELETE FROM drivers;"))
    await db_session.execute(text("DELETE FROM vehicles;"))
    await db_session.execute(text("DELETE FROM users;"))
    await db_session.commit()

