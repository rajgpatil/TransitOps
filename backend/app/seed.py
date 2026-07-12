import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.user import User, RoleEnum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User credentials definitions
SEED_USERS = [
    {
        "email": "manager@transitops.com",
        "password": "password123",
        "full_name": "Fleet Manager User",
        "role": RoleEnum.fleet_manager,
    },
    {
        "email": "driver@transitops.com",
        "password": "password123",
        "full_name": "Driver User",
        "role": RoleEnum.driver,
    },
    {
        "email": "safety@transitops.com",
        "password": "password123",
        "full_name": "Safety Officer User",
        "role": RoleEnum.safety_officer,
    },
    {
        "email": "financial@transitops.com",
        "password": "password123",
        "full_name": "Financial Analyst User",
        "role": RoleEnum.financial_analyst,
    },
]


async def seed_users(db: AsyncSession) -> None:
    """Seed one user per role into the database if they do not exist."""
    for user_data in SEED_USERS:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        existing_user = result.scalars().first()

        if not existing_user:
            logger.info(f"Seeding user: {user_data['email']} with role: {user_data['role']}")
            hashed_password = get_password_hash(user_data["password"])
            new_user = User(
                email=user_data["email"],
                hashed_password=hashed_password,
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=True,
            )
            db.add(new_user)
        else:
            logger.info(f"User {user_data['email']} already exists. Skipping.")
            
    await db.commit()


async def main() -> None:
    logger.info("Initializing database seeding...")
    async with async_session_maker() as session:
        await seed_users(session)
    logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
