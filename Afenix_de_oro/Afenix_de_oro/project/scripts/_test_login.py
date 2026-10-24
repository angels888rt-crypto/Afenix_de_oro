import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.database.session import AsyncSessionLocal, engine
from app.infrastructure.database.repositories import UserRepository
from app.application.use_cases.user_use_cases import LoginUserUseCase


async def main():
    async with AsyncSessionLocal() as session:
        use_case = LoginUserUseCase(UserRepository(session))
        user, access, refresh, display = await use_case.execute(
            username="admin", password="admin123", role="ADMIN"
        )
        print("Login OK:", user.username, user.role, "| token:", access[:25], "...")
    await engine.dispose()


asyncio.run(main())
