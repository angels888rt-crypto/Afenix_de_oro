import asyncio
import os
import sys

# aiomysql + SSL requires the selector event loop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.repositories import UserRepository
from app.infrastructure.security.jwt_handler import hash_password
from app.domain.entities import User
from app.shared.constants.enums import UserRole

async def main():
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        existing = await user_repo.get_by_username("admin")
        if existing:
            print("admin already exists:", existing.username)
            return
        admin = User(
            username="admin",
            email="admin@restaurant.com",
            password_hash=hash_password("admin123"),
            full_name="Administrator",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        await user_repo.create(admin)
        await session.commit()
        print("Admin creado y commit realizado")

if __name__ == '__main__':
    asyncio.run(main())
