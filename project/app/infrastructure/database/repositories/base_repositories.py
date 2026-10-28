"""Repository implementations using SQLAlchemy."""
from typing import Optional
from datetime import datetime, timezone
from unittest import result

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.infrastructure.database.models import (
    UserModel, TableModel, DishModel, OrderModel, OrderItemModel, NotificationModel, CategoryModel
)
from app.domain.entities import (
    User, Table, Dish, Order, OrderItem, Notification, Category
)


class UserRepository:
    """User repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        db_user = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, 'value') else user.role,
            is_active=user.is_active,
            phone=user.phone,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )
        self.session.add(db_user)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(db_user)
        return self._to_domain(db_user)
    
    async def get_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[User]:
        """Get user by ID."""
        conditions = [UserModel.id == user_id]
        if not include_deleted:
            conditions.append(UserModel.deleted_at.is_(None))

        result = await self.session.execute(
            select(UserModel).where(*conditions)
        )
        user = result.scalars().first()
        return self._to_domain(user) if user else None
    
    async def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
        """Get user by username."""
        conditions = [UserModel.username == username]
        if not include_deleted:
            conditions.append(UserModel.deleted_at.is_(None))

        result = await self.session.execute(
            select(UserModel).where(*conditions)
        )
        user = result.scalars().first()
        return self._to_domain(user) if user else None
    
    async def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        """Get user by email."""
        conditions = [UserModel.email == email]
        if not include_deleted:
            conditions.append(UserModel.deleted_at.is_(None))

        result = await self.session.execute(
            select(UserModel).where(*conditions)
        )
        user = result.scalars().first()
        return self._to_domain(user) if user else None
    
    async def get_by_role(self, role: str, skip: int = 0, limit: int = 10) -> list[User]:
        """Get users by role."""
        result = await self.session.execute(
            select(UserModel).where(
                UserModel.role == role,
                UserModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        users = result.scalars().all()
        return [self._to_domain(user) for user in users]
    
    async def update(self, user_id: int, user: User) -> Optional[User]:
        """Update user and persist changes to the database."""
        db_user = await self.get_by_id(user_id)
        if not db_user:
            return None
        
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        db_user = result.scalars().first()
        
        # Admin may update additional fields: username, email, password_hash, role
        if getattr(user, 'username', None):
            db_user.username = user.username
        if getattr(user, 'email', None):
            db_user.email = user.email
        if getattr(user, 'password_hash', None):
            db_user.password_hash = user.password_hash
        if getattr(user, 'full_name', None):
            db_user.full_name = user.full_name
        if getattr(user, 'phone', None) is not None:
            db_user.phone = user.phone
        if getattr(user, 'is_active', None) is not None:
            db_user.is_active = user.is_active
        if getattr(user, 'role', None):
            db_user.role = user.role.value if hasattr(user.role, 'value') else user.role
        db_user.updated_at = datetime.now(timezone.utc)
        db_user.updated_by = user.updated_by

        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(db_user)
        return self._to_domain(db_user)
    
    async def delete(self, user_id: int) -> bool:
        """Soft delete user."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        db_user = result.scalars().first()
    
        if not db_user:
            return False

        db_user.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.commit()
        return True

    async def restore(self, user: User) -> User:
        """Restore a soft-deleted user."""
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(stmt)
        db_user = result.scalars().first()
        if not db_user:
            return await self.create(user)

        db_user.full_name = user.full_name or db_user.full_name
        db_user.password_hash = user.password_hash or db_user.password_hash
        db_user.role = user.role.value if hasattr(user.role, 'value') else user.role
        db_user.is_active = user.is_active if user.is_active is not None else db_user.is_active
        db_user.phone = user.phone if user.phone is not None else db_user.phone
        db_user.updated_at = datetime.now(timezone.utc)
        db_user.updated_by = user.updated_by
        db_user.deleted_at = None

        await self.session.commit()
        await self.session.refresh(db_user)
        return self._to_domain(db_user)
    
    async def list(self, skip: int = 0, limit: int = 10) -> list[User]:
        """List users."""
        result = await self.session.execute(
            select(UserModel).where(
                UserModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        users = result.scalars().all()
        return [self._to_domain(user) for user in users]
    
    @staticmethod
    def _to_domain(db_user: UserModel) -> User:
        """Convert database model to domain entity."""
        return User(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            password_hash=db_user.password_hash,
            full_name=db_user.full_name,
            role=db_user.role,
            is_active=db_user.is_active,
            phone=db_user.phone,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            deleted_at=db_user.deleted_at,
            created_by=db_user.created_by,
            updated_by=db_user.updated_by,
        )


class TableRepository:
    """Table repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, table: Table) -> Table:
        """Create a new table."""
        db_table = TableModel(
            table_number=table.table_number,
            capacity=table.capacity,
            status=table.status.value if hasattr(table.status, 'value') else table.status,
            location=table.location,
            created_by=table.created_by,
        )
        self.session.add(db_table)
        await self.session.commit()
        await self.session.refresh(db_table)
        return self._to_domain(db_table)
    
    async def get_by_id(self, table_id: int) -> Optional[Table]:
        """Get table by ID."""
        result = await self.session.execute(
            select(TableModel).where(
                TableModel.id == table_id,
                TableModel.deleted_at.is_(None)
            )
        )
        table = result.scalars().first()
        return self._to_domain(table) if table else None
    
    async def get_by_number(self, table_number: int, include_deleted: bool = False) -> Optional[Table]:
        """Get table by number."""
        conditions = [TableModel.table_number == table_number]
        if not include_deleted:
            conditions.append(TableModel.deleted_at.is_(None))

        result = await self.session.execute(
            select(TableModel).where(*conditions)
        )
        table = result.scalars().first()
        return self._to_domain(table) if table else None

    async def restore(self, table: Table) -> Table:
        """Restore a soft-deleted table."""
        stmt = select(TableModel).where(TableModel.table_number == table.table_number)
        result = await self.session.execute(stmt)
        db_table = result.scalars().first()
        if not db_table:
            return await self.create(table)

        db_table.capacity = table.capacity
        db_table.status = table.status.value if hasattr(table.status, 'value') else table.status
        db_table.location = table.location
        db_table.updated_at = datetime.now(timezone.utc)
        db_table.updated_by = table.updated_by
        db_table.deleted_at = None

        await self.session.commit()
        await self.session.refresh(db_table)
        return self._to_domain(db_table)

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 10) -> list[Table]:
        """Get tables by status."""
        result = await self.session.execute(
            select(TableModel).where(
                TableModel.status == status,
                TableModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        tables = result.scalars().all()
        return [self._to_domain(table) for table in tables]
    
    async def update(self, table_id: int, table: Table) -> Optional[Table]:
        """Update table."""
        stmt = select(TableModel).where(TableModel.id == table_id)
        result = await self.session.execute(stmt)
        db_table = result.scalars().first()
        
        if not db_table:
            return None
        
        if table.capacity:
            db_table.capacity = table.capacity
        if table.status:
            db_table.status = table.status.value if hasattr(table.status, 'value') else table.status
        if table.location is not None:
            db_table.location = table.location
        db_table.updated_at = datetime.now(timezone.utc)
        db_table.updated_by = table.updated_by
        
        await self.session.flush()
        return self._to_domain(db_table)
    
    async def delete(self, table_id: int) -> bool:
        """Soft delete table."""
        stmt = select(TableModel).where(TableModel.id == table_id)
        result = await self.session.execute(stmt)
        db_table = result.scalars().first()
        
        if not db_table:
            return False
        
        await self.session.delete(db_table)
        await self.session.commit()
        return True
    
    async def list(self, skip: int = 0, limit: int = 10) -> list[Table]:
        """List tables."""
        result = await self.session.execute(
            select(TableModel).where(
                TableModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        tables = result.scalars().all()
        return [self._to_domain(table) for table in tables]
    
    @staticmethod
    def _to_domain(db_table: TableModel) -> Table:
        """Convert database model to domain entity."""
        return Table(
            id=db_table.id,
            table_number=db_table.table_number,
            capacity=db_table.capacity,
            status=db_table.status,
            location=db_table.location,
            created_at=db_table.created_at,
            updated_at=db_table.updated_at,
            deleted_at=db_table.deleted_at,
            created_by=db_table.created_by,
            updated_by=db_table.updated_by,
        )


class DishRepository:
    """Dish repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, dish: Dish) -> Dish:
        """Create a new dish."""
        db_dish = DishModel(
            name=dish.name,
            description=dish.description,
            price=dish.price,
            estimated_time=dish.estimated_time,
            category=dish.category,
            is_available=dish.is_available,
            preparation_notes=dish.preparation_notes,
            image_path=getattr(dish, 'image_path', None),
            created_by=dish.created_by,
        )
        self.session.add(db_dish)
        await self.session.commit()
        return self._to_domain(db_dish)
    
    async def get_by_id(self, dish_id: int) -> Optional[Dish]:
        """Get dish by ID."""
        result = await self.session.execute(
            select(DishModel).where(
                DishModel.id == dish_id,
                DishModel.deleted_at.is_(None)
            )
        )
        dish = result.scalars().first()
        return self._to_domain(dish) if dish else None
    
    async def get_by_category(self, category: str, skip: int = 0, limit: int = 10) -> list[Dish]:
        """Get dishes by category."""
        result = await self.session.execute(
            select(DishModel).where(
                DishModel.category == category,
                DishModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        dishes = result.scalars().all()
        return [self._to_domain(dish) for dish in dishes]
    
    async def search(self, query: str, skip: int = 0, limit: int = 10) -> list[Dish]:
        """Search dishes by name or description."""
        search_query = f"%{query}%"
        result = await self.session.execute(
            select(DishModel).where(
                (DishModel.name.ilike(search_query) | DishModel.description.ilike(search_query)),
                DishModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        dishes = result.scalars().all()
        return [self._to_domain(dish) for dish in dishes]
    
    async def get_available(self, skip: int = 0, limit: int = 10) -> list[Dish]:
        """Get available dishes."""
        result = await self.session.execute(
            select(DishModel).where(
                DishModel.is_available == True,
                DishModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        dishes = result.scalars().all()
        return [self._to_domain(dish) for dish in dishes]
    
    async def update(self, dish_id: int, dish: Dish) -> Optional[Dish]:
        """Update dish."""
        stmt = select(DishModel).where(DishModel.id == dish_id)
        result = await self.session.execute(stmt)
        db_dish = result.scalars().first()
        
        if not db_dish:
            return None
        
        if dish.name:
            db_dish.name = dish.name
        if dish.description is not None:
            db_dish.description = dish.description
        if dish.price:
            db_dish.price = dish.price
        if dish.estimated_time:
            db_dish.estimated_time = dish.estimated_time
        if dish.category:
            db_dish.category = dish.category
        if dish.is_available is not None:
            db_dish.is_available = dish.is_available
        if dish.preparation_notes is not None:
            db_dish.preparation_notes = dish.preparation_notes
        if getattr(dish, 'image_path', None) is not None:
            db_dish.image_path = dish.image_path
        db_dish.updated_at = datetime.now(timezone.utc)
        db_dish.updated_by = dish.updated_by
        
        await self.session.commit()
        return self._to_domain(db_dish)
    
    async def delete(self, dish_id: int) -> bool:
        """Soft-delete a dish so historical orders remain valid."""
        stmt = select(DishModel).where(
            DishModel.id == dish_id,
            DishModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        db_dish = result.scalars().first()
        if not db_dish:
            return False
        db_dish.deleted_at = datetime.now(timezone.utc)
        db_dish.is_available = False
        db_dish.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def list(self, skip: int = 0, limit: int = 10) -> list[Dish]:
        """List dishes."""
        result = await self.session.execute(
            select(DishModel).where(
                DishModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        dishes = result.scalars().all()
        return [self._to_domain(dish) for dish in dishes]
    
    @staticmethod
    def _to_domain(db_dish: DishModel) -> Dish:
        """Convert database model to domain entity."""
        return Dish(
            id=db_dish.id,
            name=db_dish.name,
            description=db_dish.description,
            price=db_dish.price,
            estimated_time=db_dish.estimated_time,
            category=db_dish.category,
            is_available=db_dish.is_available,
            preparation_notes=db_dish.preparation_notes,
            image_path=getattr(db_dish, 'image_path', None),
            created_at=db_dish.created_at,
            updated_at=db_dish.updated_at,
            deleted_at=db_dish.deleted_at,
            created_by=db_dish.created_by,
            updated_by=db_dish.updated_by,
        )


class CategoryRepository:
    """Category repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, category: Category) -> Category:
        """Create a new category."""
        db_cat = CategoryModel(
            name=category.name,
            description=category.description,
            created_by=category.created_by,
        )
        self.session.add(db_cat)
        await self.session.commit()
        await self.session.refresh(db_cat)
        return self._to_domain(db_cat)

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        result = await self.session.execute(
            select(CategoryModel).where(
                CategoryModel.id == category_id,
                CategoryModel.deleted_at.is_(None)
            )
        )
        cat = result.scalars().first()
        return self._to_domain(cat) if cat else None

    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name."""
        result = await self.session.execute(
            select(CategoryModel).where(
                CategoryModel.name.ilike(name),
                CategoryModel.deleted_at.is_(None)
            )
        )
        cat = result.scalars().first()
        return self._to_domain(cat) if cat else None

    async def update(self, category_id: int, category: Category) -> Optional[Category]:
        """Update category."""
        stmt = select(CategoryModel).where(CategoryModel.id == category_id)
        result = await self.session.execute(stmt)
        db_cat = result.scalars().first()

        if not db_cat:
            return None

        if category.name is not None:
            db_cat.name = category.name
        if category.description is not None:
            db_cat.description = category.description
        db_cat.updated_at = datetime.now(timezone.utc)
        db_cat.updated_by = category.updated_by

        await self.session.commit()
        await self.session.refresh(db_cat)
        return self._to_domain(db_cat)

    async def delete(self, category_id: int) -> bool:
        """Soft delete category."""
        stmt = select(CategoryModel).where(CategoryModel.id == category_id)
        result = await self.session.execute(stmt)
        db_cat = result.scalars().first()

        if not db_cat:
            return False

        db_cat.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def list(self, skip: int = 0, limit: int = 10) -> list[Category]:
        """List categories."""
        result = await self.session.execute(
            select(CategoryModel).where(
                CategoryModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        cats = result.scalars().all()
        return [self._to_domain(cat) for cat in cats]

    async def count_dishes(self, category_name: str) -> int:
        """Count dishes in a category by category name."""
        from app.infrastructure.database.models import DishModel
        result = await self.session.execute(
            select(func.count(DishModel.id)).where(
                DishModel.category == category_name,
                DishModel.deleted_at.is_(None)
            )
        )
        return result.scalar() or 0

    @staticmethod
    def _to_domain(db_cat: CategoryModel) -> Category:
        """Convert database model to domain entity."""
        return Category(
            id=db_cat.id,
            name=db_cat.name,
            description=db_cat.description,
            created_at=db_cat.created_at,
            updated_at=db_cat.updated_at,
            deleted_at=db_cat.deleted_at,
            created_by=db_cat.created_by,
            updated_by=db_cat.updated_by,
        )

