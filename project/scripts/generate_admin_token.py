import asyncio
from sqlalchemy import text
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.security.jwt_handler import create_access_token, create_refresh_token

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id, username FROM users WHERE username='admin'"))
        row = result.fetchone()
        if not row:
            print('admin not found')
            return
        user_id = row[0]
        access = create_access_token({"sub": str(user_id), "username": "admin", "role": "ADMIN"})
        refresh = create_refresh_token({"sub": str(user_id), "username": "admin"})
        print('ACCESS_TOKEN=' + access)
        print('REFRESH_TOKEN=' + refresh)

if __name__ == '__main__':
    asyncio.run(main())
