"""FastAPI main application."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.infrastructure.config import settings
from app.infrastructure.database.session import ensure_dishes_availability_column, ensure_history_table, ensure_order_daily_columns, ensure_receipt_config_table, ensure_dish_image_column, ensure_order_pagado_status, ensure_order_paid_at_column
from app.presentation.api.middleware.exception_handlers import register_exception_handlers
from app.presentation.api.routers import (
    user_router, table_router, dish_router, order_router, notification_router,
    category_router, subcategory_router
)
from app.presentation.api.routers import history_router, receipt_router

# Static directories
project_root = Path(__file__).resolve().parent
static_dir = project_root / "static"
frontend_dir = project_root.parent / "frontend"

static_dir.mkdir(parents=True, exist_ok=True)
frontend_dir.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API REST para gestión de pedidos en restaurantes",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(user_router.router)
app.include_router(table_router.router)
app.include_router(dish_router.router)
app.include_router(order_router.router)
app.include_router(notification_router.router)
app.include_router(history_router.router)
app.include_router(receipt_router.router)
app.include_router(category_router.router)
app.include_router(subcategory_router.router)

# Mount legacy static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
async def startup_event() -> None:
    """Ensure the database schema matches the current application expectations."""
    await ensure_dishes_availability_column()
    await ensure_dish_image_column()
    await ensure_history_table()
    await ensure_order_daily_columns()
    await ensure_receipt_config_table()
    await ensure_order_pagado_status()
    await ensure_order_paid_at_column()
    try:
        from app.infrastructure.database.models.database_models import UserModel
        UserModel()
    except Exception:
        pass
    # Start daily cleanup at 06:00 America/Bogota (retention 4 days)
    try:
        from app.infrastructure.scheduler.history_cleanup_scheduler import start_history_cleanup_scheduler
        start_history_cleanup_scheduler()
    except Exception:
        pass
    # Start daily order reset at 22:00 America/Bogota (mesero-pedidos)
    try:
        from app.infrastructure.scheduler.order_cleanup_scheduler import start_order_cleanup_scheduler
        start_order_cleanup_scheduler()
    except Exception:
        pass

@app.get("/", response_class=FileResponse)
async def root():
    """Serve the login page by default."""
    return FileResponse(frontend_dir / "secion.html")


def _frontend_page(name: str) -> FileResponse:
    return FileResponse(frontend_dir / name)


@app.get("/secion.html", response_class=FileResponse)
async def serve_login_page():
    return _frontend_page("secion.html")


@app.get("/index.html", response_class=FileResponse)
async def serve_panel_page():
    return _frontend_page("panel.html")


@app.get("/panel.html", response_class=FileResponse)
async def serve_panel_page_direct():
    return _frontend_page("panel.html")


@app.get("/admin.html", response_class=FileResponse)
async def serve_admin_page():
    return _frontend_page("admin.html")


@app.get("/mesero.html", response_class=FileResponse)
async def serve_waiter_page():
    return _frontend_page("mesero.html")


@app.get("/admin-inventario.html", response_class=FileResponse)
async def serve_admin_inventory_page():
    return _frontend_page("admin-inventario.html")


@app.get("/admin-crear-plato.html", response_class=FileResponse)
async def serve_admin_create_dish_page():
    return _frontend_page("admin-crear-plato.html")


@app.get("/admin-categorias.html", response_class=FileResponse)
async def serve_admin_categories_page():
    return _frontend_page("admin-categorias.html")


@app.get("/admin-usuarios.html", response_class=FileResponse)
async def serve_admin_users_page():
    return _frontend_page("admin-usuarios.html")


@app.get("/admin-historial.html", response_class=FileResponse)
async def serve_admin_history_page():
    return _frontend_page("admin-historial.html")


@app.get("/admin-recibo.html", response_class=FileResponse)
async def serve_admin_receipt_page():
    return _frontend_page("admin-recibo.html")


@app.get("/mesero-crear-pedido.html", response_class=FileResponse)
async def serve_waiter_create_order_page():
    return _frontend_page("mesero-crear-pedido.html")

@app.get("/mesero-pedidos.html", response_class=FileResponse)
async def serve_waiter_orders_page():
    return _frontend_page("mesero-pedidos.html")


@app.get("/cajero.html", response_class=FileResponse)
async def serve_cajero_page():
    return _frontend_page("cajero.html")


@app.get("/cajero-entregados.html", response_class=FileResponse)
async def serve_cajero_entregados_page():
    return _frontend_page("cajero-entregados.html")


@app.get("/cajero-ventas.html", response_class=FileResponse)
async def serve_cajero_ventas_page():
    return _frontend_page("cajero-ventas.html")


@app.get("/cajero-ordenes.html", response_class=FileResponse)
async def serve_cajero_orders_page():
    return _frontend_page("cajero-ordenes.html")


@app.get("/usuario.html", response_class=FileResponse)
async def serve_users_legacy_page():
    return _frontend_page("admin-usuarios.html")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/{asset_path:path}", include_in_schema=False)
async def serve_frontend_asset(asset_path: str):
    """Serve static assets from the new frontend folder."""
    file_path = frontend_dir / asset_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Not Found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.reload,
    )
