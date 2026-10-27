import asyncio
from app.infrastructure.database.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id, username, email, role, is_active FROM users WHERE username='admin'"))
        rows = result.fetchall()
        print('admin rows:', rows)

if __name__ == '__main__':
    asyncio.run(main())
