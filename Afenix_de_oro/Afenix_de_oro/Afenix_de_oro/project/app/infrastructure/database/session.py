"""Database session management."""
from typing import AsyncGenerator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import OperationalError

from app.infrastructure.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.debug,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


def column_exists(columns: list[dict], column_name: str) -> bool:
    """Return True if a column with the given name exists in the inspected schema."""
    return any(column.get("name") == column_name for column in columns)


async def ensure_dishes_availability_column() -> None:
    """Ensure dishes uses Disponible/Agotado (is_available) and remove stock_quantity if it exists."""
    try:
        async with engine.begin() as connection:
            def get_columns(sync_connection):
                inspector = inspect(sync_connection)
                return inspector.get_columns("dishes")

            columns = await connection.run_sync(get_columns)
            # Ensure is_available exists
            if not column_exists(columns, "is_available"):
                await connection.execute(
                    text("ALTER TABLE dishes ADD COLUMN is_available BOOLEAN NOT NULL DEFAULT 1")
                )
            # Remove stock_quantity if it still exists (migrated to is_available)
            if column_exists(columns, "stock_quantity"):
                try:
                    await connection.execute(text("ALTER TABLE dishes DROP COLUMN stock_quantity"))
                except Exception:
                    pass
    except OperationalError as exc:
        if "Duplicate column name" in str(exc) or "already exists" in str(exc).lower():
            return
        pass
    except Exception:
        pass


# Backward compat alias
async def ensure_dishes_stock_column() -> None:
    await ensure_dishes_availability_column()


async def ensure_history_table() -> None:
    """Ensure the history_logs table exists (for deployments without alembic run)."""
    try:
        from app.infrastructure.database.models import Base
        async with engine.begin() as connection:
            def create_history(sync_connection):
                inspector = inspect(sync_connection)
                if "history_logs" in inspector.get_table_names():
                    return
                # Create via metadata
                Base.metadata.create_all(sync_connection, tables=[Base.metadata.tables["history_logs"]])

            await connection.run_sync(create_history)
    except Exception:
        # Table creation failures should not block startup; alembic will handle it
        pass


async def ensure_order_daily_columns() -> None:
    """Ensure orders table has daily_number and cycle_key for 22:00 Bogota reset."""
    try:
        async with engine.begin() as connection:
            def get_columns(sync_connection):
                inspector = inspect(sync_connection)
                return inspector.get_columns("orders")

            columns = await connection.run_sync(get_columns)
            if not column_exists(columns, "daily_number"):
                await connection.execute(text("ALTER TABLE orders ADD COLUMN daily_number INT NULL"))
            if not column_exists(columns, "cycle_key"):
                await connection.execute(text("ALTER TABLE orders ADD COLUMN cycle_key VARCHAR(20) NULL"))
            # Try to create indexes if not exist (ignore errors)
            try:
                await connection.execute(text("CREATE INDEX idx_daily_number ON orders (daily_number)"))
            except Exception:
                pass
            try:
                await connection.execute(text("CREATE INDEX idx_cycle_key ON orders (cycle_key)"))
            except Exception:
                pass
            try:
                await connection.execute(text("CREATE UNIQUE INDEX uq_cycle_daily_number ON orders (cycle_key, daily_number)"))
            except Exception:
                pass
    except OperationalError as exc:
        if "Duplicate column name" in str(exc) or "already exists" in str(exc).lower():
            return
        # Don't block startup on failure
        pass
    except Exception:
        pass


async def ensure_receipt_config_table() -> None:
    """Ensure receipt_config table exists."""
    try:
        from app.infrastructure.database.models import Base
        async with engine.begin() as connection:
            def create_table(sync_connection):
                inspector = inspect(sync_connection)
                if "receipt_config" in inspector.get_table_names():
                    return
                Base.metadata.create_all(sync_connection, tables=[Base.metadata.tables["receipt_config"]])
            await connection.run_sync(create_table)
            # Asegurar registro por defecto id=1
            def ensure_row(sync_connection):
                from sqlalchemy import text as sa_text
                # Usa INSERT IGNORE para MySQL / INSERT OR IGNORE para SQLite
                try:
                    sync_connection.execute(sa_text("INSERT IGNORE INTO receipt_config (id, restaurant_name, footer_message) VALUES (1, 'RESTAURANTE', '¡Gracias por su visita!')"))
                except Exception:
                    try:
                        sync_connection.execute(sa_text("INSERT OR IGNORE INTO receipt_config (id, restaurant_name, footer_message) VALUES (1, 'RESTAURANTE', '¡Gracias por su visita!')"))
                    except Exception:
                        pass
            await connection.run_sync(ensure_row)
    except Exception:
        pass


async def ensure_order_paid_at_column() -> None:
    """Ensure orders table has paid_at column for PAGADO state."""
    try:
        async with engine.begin() as connection:
            def get_columns(sync_connection):
                inspector = inspect(sync_connection)
                return inspector.get_columns("orders")
            columns = await connection.run_sync(get_columns)
            if not column_exists(columns, "paid_at"):
                await connection.execute(text("ALTER TABLE orders ADD COLUMN paid_at DATETIME NULL"))
    except Exception:
        pass

async def ensure_order_pagado_status() -> None:
    """Ensure orders ck_order_status includes PAGADO. Fix for deployments without alembic."""
    try:
        async with engine.begin() as connection:
            def fix_constraint(sync_connection):
                from sqlalchemy import text as sa_text
                try:
                    sync_connection.execute(sa_text("ALTER TABLE orders DROP CHECK ck_order_status"))
                except Exception:
                    try:
                        sync_connection.execute(sa_text("ALTER TABLE orders DROP CONSTRAINT ck_order_status"))
                    except Exception:
                        pass
                try:
                    sync_connection.execute(sa_text("ALTER TABLE orders ADD CONSTRAINT ck_order_status CHECK (status IN ('PENDIENTE', 'NUEVO', 'EN_COCINA', 'COMPLETADO', 'ENTREGADO', 'CANCELADO', 'PAGADO'))"))
                except Exception:
                    pass
            await connection.run_sync(fix_constraint)
    except Exception:
        pass

async def ensure_dish_image_column() -> None:
    """Ensure dishes table has image_path column."""
    try:
        async with engine.begin() as connection:
            def get_columns(sync_connection):
                inspector = inspect(sync_connection)
                return inspector.get_columns("dishes")
            columns = await connection.run_sync(get_columns)
            if column_exists(columns, "image_path"):
                return
            await connection.execute(text("ALTER TABLE dishes ADD COLUMN image_path VARCHAR(255) NULL"))
    except OperationalError as exc:
        if "Duplicate column name" in str(exc) or "already exists" in str(exc).lower():
            return
        pass
    except Exception:
        pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
