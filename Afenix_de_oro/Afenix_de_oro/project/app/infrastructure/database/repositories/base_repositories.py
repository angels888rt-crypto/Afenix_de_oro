"""Repository implementations using SQLAlchemy."""
from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from unittest import result

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    UserModel, TableModel, DishModel, CategoryModel, OrderModel, OrderItemModel, NotificationModel,
    SubcategoryModel, SubcategoryOptionModel, DishSubcategoryAssociation, OrderItemSubcategorySelectionModel
)
from app.domain.entities import (
    User, Table, Dish, Category, Order, OrderItem, Notification,
    Subcategory, SubcategoryOption, OrderItemSubcategorySelection
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


class CategoryRepository:
    """Category repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, category: Category) -> Category:
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
        result = await self.session.execute(
            select(CategoryModel).where(
                CategoryModel.id == category_id,
                CategoryModel.deleted_at.is_(None)
            )
        )
        cat = result.scalars().first()
        return self._to_domain(cat) if cat else None

    async def get_by_name(self, name: str) -> Optional[Category]:
        result = await self.session.execute(
            select(CategoryModel).where(
                func.lower(CategoryModel.name) == func.lower(name),
                CategoryModel.deleted_at.is_(None)
            )
        )
        cat = result.scalars().first()
        return self._to_domain(cat) if cat else None

    async def list(self, skip: int = 0, limit: int = 100) -> list[Category]:
        result = await self.session.execute(
            select(CategoryModel).where(
                CategoryModel.deleted_at.is_(None)
            ).order_by(CategoryModel.name.asc()).offset(skip).limit(limit)
        )
        cats = result.scalars().all()
        return [self._to_domain(c) for c in cats]

    async def list_all(self) -> list[Category]:
        return await self.list(skip=0, limit=1000)

    async def update(self, category_id: int, category: Category) -> Optional[Category]:
        stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        db_cat = result.scalars().first()
        if not db_cat:
            return None
        if category.name:
            db_cat.name = category.name
        if category.description is not None:
            db_cat.description = category.description
        db_cat.updated_at = datetime.now(timezone.utc)
        db_cat.updated_by = category.updated_by
        await self.session.commit()
        await self.session.refresh(db_cat)
        # sync dishes category string if name changed
        if category.name and db_cat.name != category.name:
            pass
        # Ensure dishes.category stays synced when name changes
        if category.name:
            await self.session.execute(
                select(DishModel).where(DishModel.category_id == category_id)
            )
            # Update denormalized column
            from sqlalchemy import update as sa_update
            await self.session.execute(
                sa_update(DishModel).where(DishModel.category_id == category_id).values(category=db_cat.name, updated_at=datetime.now(timezone.utc))
            )
            await self.session.commit()
        return self._to_domain(db_cat)

    async def delete(self, category_id: int) -> bool:
        stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        db_cat = result.scalars().first()
        if not db_cat:
            return False
        # Check if has dishes
        cnt = await self.session.execute(select(func.count()).select_from(DishModel).where(DishModel.category_id == category_id, DishModel.deleted_at.is_(None)))
        count = cnt.scalar() or 0
        if count > 0:
            return False  # caller should handle error
        db_cat.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def count_dishes(self, category_id: int) -> int:
        cnt = await self.session.execute(select(func.count()).select_from(DishModel).where(DishModel.category_id == category_id, DishModel.deleted_at.is_(None)))
        return int(cnt.scalar() or 0)

    @staticmethod
    def _to_domain(db_cat: CategoryModel) -> Category:
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


class SubcategoryRepository:
    """Subcategory repository with options and dish associations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, subcategory: Subcategory) -> Subcategory:
        db_sub = SubcategoryModel(name=subcategory.name, description=subcategory.description, created_by=subcategory.created_by)
        self.session.add(db_sub)
        await self.session.flush()
        # create initial options if provided
        for opt in subcategory.options:
            db_opt = SubcategoryOptionModel(subcategory_id=db_sub.id, name=opt.name, created_by=subcategory.created_by)
            self.session.add(db_opt)
        await self.session.commit()
        await self.session.refresh(db_sub)
        # associate dishes if provided
        if subcategory.dish_ids:
            for dish_id in subcategory.dish_ids:
                # validate dish exists
                exists = await self.session.execute(select(DishModel).where(DishModel.id == dish_id, DishModel.deleted_at.is_(None)))
                if exists.scalars().first():
                    self.session.add(DishSubcategoryAssociation(dish_id=dish_id, subcategory_id=db_sub.id))
            await self.session.commit()
        return await self.get_by_id(db_sub.id)

    async def get_by_id(self, sub_id: int) -> Optional[Subcategory]:
        result = await self.session.execute(select(SubcategoryModel).where(SubcategoryModel.id == sub_id, SubcategoryModel.deleted_at.is_(None)).options(selectinload(SubcategoryModel.options)))
        db_sub = result.scalars().first()
        if not db_sub:
            return None
        # load dish_ids
        dish_res = await self.session.execute(select(DishSubcategoryAssociation.dish_id).where(DishSubcategoryAssociation.subcategory_id == sub_id))
        dish_ids = [r[0] for r in dish_res.all()]
        return self._to_domain(db_sub, dish_ids)

    async def get_by_name(self, name: str) -> Optional[Subcategory]:
        result = await self.session.execute(select(SubcategoryModel).where(func.lower(SubcategoryModel.name) == func.lower(name), SubcategoryModel.deleted_at.is_(None)))
        db_sub = result.scalars().first()
        return await self.get_by_id(db_sub.id) if db_sub else None

    async def list(self, skip: int = 0, limit: int = 100) -> list[Subcategory]:
        result = await self.session.execute(select(SubcategoryModel).where(SubcategoryModel.deleted_at.is_(None)).order_by(SubcategoryModel.name.asc()).offset(skip).limit(limit).options(selectinload(SubcategoryModel.options)))
        subs = result.scalars().all()
        out = []
        for db_sub in subs:
            dish_res = await self.session.execute(select(DishSubcategoryAssociation.dish_id).where(DishSubcategoryAssociation.subcategory_id == db_sub.id))
            dish_ids = [r[0] for r in dish_res.all()]
            out.append(self._to_domain(db_sub, dish_ids))
        return out

    async def update(self, sub_id: int, subcategory: Subcategory) -> Optional[Subcategory]:
        result = await self.session.execute(select(SubcategoryModel).where(SubcategoryModel.id == sub_id, SubcategoryModel.deleted_at.is_(None)).options(selectinload(SubcategoryModel.options)))
        db_sub = result.scalars().first()
        if not db_sub:
            return None
        if subcategory.name:
            db_sub.name = subcategory.name
        if subcategory.description is not None:
            db_sub.description = subcategory.description
        db_sub.updated_at = datetime.now(timezone.utc)
        db_sub.updated_by = subcategory.updated_by
        await self.session.commit()
        # update dish associations if provided (not None)
        if subcategory.dish_ids is not None:
            # delete old
            await self.session.execute(select(DishSubcategoryAssociation).where(DishSubcategoryAssociation.subcategory_id == sub_id))
            del_res = await self.session.execute(select(DishSubcategoryAssociation).where(DishSubcategoryAssociation.subcategory_id == sub_id))
            # Use delete via ORM bulk
            from sqlalchemy import delete
            await self.session.execute(delete(DishSubcategoryAssociation).where(DishSubcategoryAssociation.subcategory_id == sub_id))
            for did in subcategory.dish_ids:
                exists = await self.session.execute(select(DishModel).where(DishModel.id == did, DishModel.deleted_at.is_(None)))
                if exists.scalars().first():
                    self.session.add(DishSubcategoryAssociation(dish_id=did, subcategory_id=sub_id))
            await self.session.commit()
        await self.session.refresh(db_sub)
        return await self.get_by_id(sub_id)

    async def delete(self, sub_id: int) -> bool:
        result = await self.session.execute(select(SubcategoryModel).where(SubcategoryModel.id == sub_id, SubcategoryModel.deleted_at.is_(None)))
        db_sub = result.scalars().first()
        if not db_sub:
            return False
        # Check if subcategory is used in any order selection; if used, keep soft delete but rename to free unique
        cnt = await self.session.execute(select(func.count()).select_from(OrderItemSubcategorySelectionModel).where(OrderItemSubcategorySelectionModel.subcategory_id == sub_id))
        used = (cnt.scalar() or 0) > 0
        original_name = db_sub.name
        db_sub.deleted_at = datetime.now(timezone.utc)
        if used:
            db_sub.name = f"{original_name}_deleted_{sub_id}_{int(datetime.now(timezone.utc).timestamp())}"
        opt_res = await self.session.execute(select(SubcategoryOptionModel).where(SubcategoryOptionModel.subcategory_id == sub_id, SubcategoryOptionModel.deleted_at.is_(None)))
        for opt in opt_res.scalars().all():
            opt.deleted_at = datetime.now(timezone.utc)
            if used:
                opt.name = f"{opt.name}_deleted_{opt.id}"
        # remove dish associations
        from sqlalchemy import delete
        await self.session.execute(delete(DishSubcategoryAssociation).where(DishSubcategoryAssociation.subcategory_id == sub_id))
        await self.session.commit()
        return True

    # Options management
    async def create_option(self, sub_id: int, name: str, created_by: Optional[int] = None) -> Optional[SubcategoryOption]:
        # check subcategory exists
        sub = await self.get_by_id(sub_id)
        if not sub:
            return None
        # duplicate check
        dup = await self.session.execute(select(SubcategoryOptionModel).where(SubcategoryOptionModel.subcategory_id == sub_id, func.lower(SubcategoryOptionModel.name)==func.lower(name), SubcategoryOptionModel.deleted_at.is_(None)))
        if dup.scalars().first():
            return None
        db_opt = SubcategoryOptionModel(subcategory_id=sub_id, name=name, created_by=created_by)
        self.session.add(db_opt)
        await self.session.commit()
        await self.session.refresh(db_opt)
        return self._opt_to_domain(db_opt)

    async def update_option(self, sub_id: int, option_id: int, name: str, updated_by: Optional[int]=None) -> Optional[SubcategoryOption]:
        result = await self.session.execute(select(SubcategoryOptionModel).where(SubcategoryOptionModel.id==option_id, SubcategoryOptionModel.subcategory_id==sub_id, SubcategoryOptionModel.deleted_at.is_(None)))
        db_opt = result.scalars().first()
        if not db_opt:
            return None
        # duplicate check
        dup = await self.session.execute(select(SubcategoryOptionModel).where(SubcategoryOptionModel.subcategory_id==sub_id, func.lower(SubcategoryOptionModel.name)==func.lower(name), SubcategoryOptionModel.id!=option_id, SubcategoryOptionModel.deleted_at.is_(None)))
        if dup.scalars().first():
            return None
        db_opt.name = name
        db_opt.updated_at = datetime.now(timezone.utc)
        db_opt.updated_by = updated_by
        await self.session.commit()
        await self.session.refresh(db_opt)
        return self._opt_to_domain(db_opt)

    async def delete_option(self, sub_id: int, option_id: int) -> bool:
        result = await self.session.execute(select(SubcategoryOptionModel).where(SubcategoryOptionModel.id==option_id, SubcategoryOptionModel.subcategory_id==sub_id, SubcategoryOptionModel.deleted_at.is_(None)))
        db_opt = result.scalars().first()
        if not db_opt:
            return False
        # check if option is used in any order selection (cannot delete if used - prevent orphan)
        cnt = await self.session.execute(select(func.count()).select_from(OrderItemSubcategorySelectionModel).where(OrderItemSubcategorySelectionModel.option_id==option_id))
        if (cnt.scalar() or 0) > 0:
            return False
        original_name = db_opt.name
        db_opt.deleted_at = datetime.now(timezone.utc)
        db_opt.name = f"{original_name}_deleted_{option_id}_{int(datetime.now(timezone.utc).timestamp())}"
        await self.session.commit()
        return True

    async def list_options(self, sub_id: int) -> list[SubcategoryOption]:
        result = await self.session.execute(select(SubcategoryOptionModel).where(SubcategoryOptionModel.subcategory_id==sub_id, SubcategoryOptionModel.deleted_at.is_(None)).order_by(SubcategoryOptionModel.name.asc()))
        opts = result.scalars().all()
        return [self._opt_to_domain(o) for o in opts]

    async def get_option(self, option_id: int) -> Optional[SubcategoryOption]:
        result = await self.session.execute(select(SubcategoryOptionModel).where(SubcategoryOptionModel.id==option_id, SubcategoryOptionModel.deleted_at.is_(None)))
        o = result.scalars().first()
        return self._opt_to_domain(o) if o else None

    async def get_subcategories_for_dish(self, dish_id: int) -> list[Subcategory]:
        # find subcategory ids for dish
        res = await self.session.execute(select(DishSubcategoryAssociation.subcategory_id).where(DishSubcategoryAssociation.dish_id==dish_id))
        sub_ids = [r[0] for r in res.all()]
        if not sub_ids:
            return []
        result = await self.session.execute(select(SubcategoryModel).where(SubcategoryModel.id.in_(sub_ids), SubcategoryModel.deleted_at.is_(None)).options(selectinload(SubcategoryModel.options)))
        subs = result.scalars().all()
        # filter options to not deleted
        out=[]
        for db_sub in subs:
            # options already loaded but need to filter deleted
            db_sub.options = [o for o in db_sub.options if o.deleted_at is None]
            dish_res = await self.session.execute(select(DishSubcategoryAssociation.dish_id).where(DishSubcategoryAssociation.subcategory_id==db_sub.id))
            dish_ids = [r[0] for r in dish_res.all()]
            out.append(self._to_domain(db_sub, dish_ids))
        return out

    async def get_dishes_for_subcategory(self, sub_id: int) -> list[int]:
        res = await self.session.execute(select(DishSubcategoryAssociation.dish_id).where(DishSubcategoryAssociation.subcategory_id==sub_id))
        return [r[0] for r in res.all()]

    @staticmethod
    def _to_domain(db_sub: SubcategoryModel, dish_ids: list[int]) -> Subcategory:
        return Subcategory(
            id=db_sub.id,
            name=db_sub.name,
            description=db_sub.description,
            options=[SubcategoryRepository._opt_to_domain(o) for o in (db_sub.options or []) if o.deleted_at is None],
            dish_ids=dish_ids,
            created_at=db_sub.created_at,
            updated_at=db_sub.updated_at,
            deleted_at=db_sub.deleted_at,
            created_by=db_sub.created_by,
            updated_by=db_sub.updated_by,
        )

    @staticmethod
    def _opt_to_domain(db_opt: SubcategoryOptionModel) -> SubcategoryOption:
        return SubcategoryOption(
            id=db_opt.id,
            subcategory_id=db_opt.subcategory_id,
            name=db_opt.name,
            created_at=db_opt.created_at,
            updated_at=db_opt.updated_at,
            deleted_at=db_opt.deleted_at,
            created_by=db_opt.created_by,
            updated_by=db_opt.updated_by,
        )


class DishRepository:
    """Dish repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _load_subcategories(self, dish_id: int) -> list[Subcategory]:
        # reuse subcategory logic without creating repo cycle - query directly
        res = await self.session.execute(select(DishSubcategoryAssociation.subcategory_id).where(DishSubcategoryAssociation.dish_id == dish_id))
        sub_ids = [r[0] for r in res.all()]
        if not sub_ids:
            return []
        result = await self.session.execute(select(SubcategoryModel).where(SubcategoryModel.id.in_(sub_ids), SubcategoryModel.deleted_at.is_(None)).options(selectinload(SubcategoryModel.options)))
        subs = result.scalars().all()
        out=[]
        for db_sub in subs:
            db_sub.options = [o for o in db_sub.options if o.deleted_at is None]
            # dish_ids for domain (optional)
            out.append(Subcategory(
                id=db_sub.id,
                name=db_sub.name,
                description=db_sub.description,
                options=[SubcategoryOption(id=o.id, subcategory_id=o.subcategory_id, name=o.name, created_at=o.created_at, updated_at=o.updated_at) for o in db_sub.options],
                dish_ids=[],
                created_at=db_sub.created_at,
                updated_at=db_sub.updated_at,
            ))
        return out
    
    async def create(self, dish: Dish) -> Dish:
        """Create a new dish."""
        # Resolve category name from category_id if provided
        cat_name = dish.category
        cat_id = getattr(dish, 'category_id', None)
        if cat_id:
            cat = await self.session.execute(select(CategoryModel).where(CategoryModel.id == cat_id, CategoryModel.deleted_at.is_(None)))
            cat_obj = cat.scalars().first()
            if cat_obj:
                cat_name = cat_obj.name
        db_dish = DishModel(
            name=dish.name,
            description=dish.description,
            price=dish.price,
            estimated_time=dish.estimated_time,
            category=cat_name or dish.category or "",
            category_id=cat_id,
            is_available=dish.is_available,
            preparation_notes=dish.preparation_notes,
            image_path=getattr(dish, 'image_path', None),
            created_by=dish.created_by,
        )
        self.session.add(db_dish)
        await self.session.commit()
        await self.session.refresh(db_dish)
        domain = self._to_domain(db_dish)
        domain.subcategories = await self._load_subcategories(domain.id)
        return domain
    
    async def get_by_id(self, dish_id: int) -> Optional[Dish]:
        """Get dish by ID."""
        result = await self.session.execute(
            select(DishModel).where(
                DishModel.id == dish_id,
                DishModel.deleted_at.is_(None)
            )
        )
        dish = result.scalars().first()
        if not dish:
            return None
        domain = self._to_domain(dish)
        domain.subcategories = await self._load_subcategories(dish.id)
        return domain
    
    async def get_by_category(self, category: str, skip: int = 0, limit: int = 10) -> list[Dish]:
        """Get dishes by category."""
        result = await self.session.execute(
            select(DishModel).where(
                DishModel.category == category,
                DishModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        dishes = result.scalars().all()
        out=[]
        for d in dishes:
            dom = self._to_domain(d)
            dom.subcategories = await self._load_subcategories(d.id)
            out.append(dom)
        return out
    
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
        out=[]
        for d in dishes:
            dom = self._to_domain(d)
            dom.subcategories = await self._load_subcategories(d.id)
            out.append(dom)
        return out
    
    async def get_available(self, skip: int = 0, limit: int = 10) -> list[Dish]:
        """Get available dishes."""
        result = await self.session.execute(
            select(DishModel).where(
                DishModel.is_available == True,
                DishModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        dishes = result.scalars().all()
        out=[]
        for d in dishes:
            dom = self._to_domain(d)
            dom.subcategories = await self._load_subcategories(d.id)
            out.append(dom)
        return out
    
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
        # Handle category change via category_id
        cat_id = getattr(dish, 'category_id', None)
        if cat_id is not None:
            # validate exists
            cat = await self.session.execute(select(CategoryModel).where(CategoryModel.id == cat_id, CategoryModel.deleted_at.is_(None)))
            cat_obj = cat.scalars().first()
            if cat_obj:
                db_dish.category_id = cat_id
                db_dish.category = cat_obj.name
        elif dish.category:
            # legacy string update -> try to find or keep
            db_dish.category = dish.category
            # try to find category by name to sync id
            cat = await self.session.execute(select(CategoryModel).where(func.lower(CategoryModel.name) == func.lower(dish.category), CategoryModel.deleted_at.is_(None)))
            cat_obj = cat.scalars().first()
            if cat_obj:
                db_dish.category_id = cat_obj.id
        if dish.is_available is not None:
            db_dish.is_available = dish.is_available
        if dish.preparation_notes is not None:
            db_dish.preparation_notes = dish.preparation_notes
        if getattr(dish, 'image_path', None) is not None:
            db_dish.image_path = dish.image_path
        db_dish.updated_at = datetime.now(timezone.utc)
        db_dish.updated_by = dish.updated_by
        
        await self.session.commit()
        await self.session.refresh(db_dish)
        domain = self._to_domain(db_dish)
        domain.subcategories = await self._load_subcategories(dish_id)
        return domain
    
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
        out=[]
        for d in dishes:
            dom = self._to_domain(d)
            dom.subcategories = await self._load_subcategories(d.id)
            out.append(dom)
        return out
    
    @staticmethod
    def _to_domain(db_dish: DishModel) -> Dish:
        """Convert database model to domain entity."""
        # Resolve category_name via relationship or fallback to category string
        cat_name = None
        try:
            if getattr(db_dish, 'category_obj', None) and db_dish.category_obj:
                cat_name = db_dish.category_obj.name
            elif getattr(db_dish, 'category_id', None):
                # lazy: keep as stored category string
                cat_name = db_dish.category
            else:
                cat_name = db_dish.category
        except Exception:
            cat_name = db_dish.category
        return Dish(
            id=db_dish.id,
            name=db_dish.name,
            description=db_dish.description,
            price=db_dish.price,
            estimated_time=db_dish.estimated_time,
            category=db_dish.category,
            category_id=getattr(db_dish, 'category_id', None),
            category_name=cat_name,
            is_available=db_dish.is_available,
            preparation_notes=db_dish.preparation_notes,
            image_path=getattr(db_dish, 'image_path', None),
            subcategories=[],
            created_at=db_dish.created_at,
            updated_at=db_dish.updated_at,
            deleted_at=db_dish.deleted_at,
            created_by=db_dish.created_by,
            updated_by=db_dish.updated_by,
        )
