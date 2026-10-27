"""
Script to initialize the database with demo data.

Run this after migrations to populate the database with sample data:
    python init_demo_data.py
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.repositories import (
    UserRepository, TableRepository, DishRepository
)
from app.domain.entities import User, Table, Dish
from app.infrastructure.security.jwt_handler import hash_password
from app.shared.constants.enums import UserRole, TableStatus


async def init_demo_data():
    """Initialize demo data."""
    async with AsyncSessionLocal() as session:
        try:
            # Create admin user
            user_repo = UserRepository(session)
            
            admin = User(
                username="admin",
                email="admin@restaurant.com",
                password_hash=hash_password("admin123"),
                full_name="Administrator",
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            await user_repo.create(admin)
            print("✓ Admin user created")
            
            # Create camarero users
            camarero1 = User(
                username="camarero1",
                email="camarero1@restaurant.com",
                password_hash=hash_password("camarero123"),
                full_name="Juan Pérez",
                role=UserRole.CAMARERO.value,
                is_active=True,
                phone="3333333333",
            )
            await user_repo.create(camarero1)
            print("✓ Camarero 1 created")
            
            camarero2 = User(
                username="camarero2",
                email="camarero2@restaurant.com",
                password_hash=hash_password("camarero123"),
                full_name="María García",
                role=UserRole.CAMARERO.value,
                is_active=True,
                phone="4444444444",
            )
            await user_repo.create(camarero2)
            print("✓ Camarero 2 created")
            
            # Create tables
            table_repo = TableRepository(session)
            
            for i in range(1, 11):
                table = Table(
                    table_number=i,
                    capacity=4 if i % 2 == 0 else 2,
                    status=TableStatus.DISPONIBLE.value,
                    location=f"Sección A" if i <= 5 else "Sección B",
                )
                await table_repo.create(table)
            print("✓ 10 tables created")
            
            # Create dishes
            dish_repo = DishRepository(session)
            
            dishes_data = [
                # Appetizers
                {"name": "Alitas de pollo", "category": "Entrantes", "price": 450, "time": 600, "desc": "Alitas BBQ"},
                {"name": "Camarones al ajillo", "category": "Entrantes", "price": 550, "time": 480},
                
                # Main courses
                {"name": "Carne asada", "category": "Platos Principales", "price": 1200, "time": 1200, "desc": "Carne asada con papas"},
                {"name": "Pechuga de pollo", "category": "Platos Principales", "price": 950, "time": 900, "desc": "Pechuga rellena de queso y jamón"},
                {"name": "Salmón a la mantequilla", "category": "Platos Principales", "price": 1400, "time": 1080, "desc": "Salmón fresco con salsa de limón"},
                {"name": "Pasta Alfredo", "category": "Platos Principales", "price": 850, "time": 780},
                
                # Soups
                {"name": "Sopa de verduras", "category": "Sopas", "price": 350, "time": 300},
                {"name": "Caldo de pollo", "category": "Sopas", "price": 300, "time": 300},
                
                # Salads
                {"name": "Ensalada César", "category": "Ensaladas", "price": 550, "time": 180},
                {"name": "Ensalada de vegetales", "category": "Ensaladas", "price": 450, "time": 180},
                
                # Desserts
                {"name": "Flan", "category": "Postres", "price": 250, "time": 120},
                {"name": "Tiramisú", "category": "Postres", "price": 300, "time": 120},
            ]
            
            for data in dishes_data:
                dish = Dish(
                    name=data["name"],
                    category=data["category"],
                    price=data["price"],
                    estimated_time=data["time"],
                    description=data.get("desc"),
                    is_available=True,
                )
                await dish_repo.create(dish)
            
            print(f"✓ {len(dishes_data)} dishes created")
            
            # Commit all changes
            await session.commit()
            print("\n✅ Demo data initialized successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error initializing demo data: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_demo_data())
