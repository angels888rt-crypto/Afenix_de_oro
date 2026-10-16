"""Receipt config API router — ADMIN configures, CAMARERO reads for thermal receipt."""
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.infrastructure.database.models import ReceiptConfigModel
from app.application.dto import ReceiptConfigResponse, ReceiptConfigUpdateRequest
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import get_current_user, require_role

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/receipt-config", tags=["ReceiptConfig"])

# Directorio donde se guardan los logos
project_root = Path(__file__).resolve().parents[4]  # project/
static_dir = project_root / "static"
uploads_dir = static_dir / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
static_dir.mkdir(parents=True, exist_ok=True)

DEFAULT_NAME = "RESTAURANTE"
DEFAULT_FOOTER = "¡Gracias por su visita!"
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
MAX_SIZE = 2 * 1024 * 1024  # 2MB

def _to_response(model: ReceiptConfigModel) -> ReceiptConfigResponse:
    logo_url = None
    if model.logo_path:
        # logo_path es como /static/uploads/xxx.png -> ya es URL
        # Si empieza con /static, lo dejamos tal cual, si no, lo prefijamos
        if model.logo_path.startswith("/"):
            logo_url = model.logo_path
        else:
            logo_url = f"/{model.logo_path.lstrip('/')}"
    return ReceiptConfigResponse(
        id=model.id,
        restaurant_name=model.restaurant_name,
        footer_message=model.footer_message,
        logo_path=model.logo_path,
        logo_url=logo_url,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

async def _get_or_create(session: AsyncSession) -> ReceiptConfigModel:
    result = await session.execute(select(ReceiptConfigModel).where(ReceiptConfigModel.id == 1))
    cfg = result.scalars().first()
    if cfg:
        return cfg
    cfg = ReceiptConfigModel(
        id=1,
        restaurant_name=DEFAULT_NAME,
        footer_message=DEFAULT_FOOTER,
        logo_path=None,
    )
    session.add(cfg)
    await session.commit()
    await session.refresh(cfg)
    return cfg

@router.get("", response_model=ResponseSchema[ReceiptConfigResponse])
async def get_receipt_config(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Obtiene configuración del recibo. Cualquier usuario autenticado (ADMIN/CAMARERO) puede leer."""
    # No require_role, solo autenticado
    cfg = await _get_or_create(session)
    return ResponseSchema(success=True, message="Configuración obtenida", data=_to_response(cfg))

@router.put("", response_model=ResponseSchema[ReceiptConfigResponse])
async def update_receipt_config(
    request: ReceiptConfigUpdateRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Actualiza nombre y mensaje. Solo ADMIN."""
    await require_role("ADMIN")(current_user)
    cfg = await _get_or_create(session)
    if request.restaurant_name is not None:
        cfg.restaurant_name = request.restaurant_name.strip() or DEFAULT_NAME
    if request.footer_message is not None:
        cfg.footer_message = request.footer_message.strip() or DEFAULT_FOOTER
    if request.logo_path is not None:
        # Permite limpiar logo pasando cadena vacía
        cfg.logo_path = request.logo_path if request.logo_path else None
    await session.commit()
    await session.refresh(cfg)
    return ResponseSchema(success=True, message="Configuración actualizada", data=_to_response(cfg))

@router.post("/logo", response_model=ResponseSchema[ReceiptConfigResponse])
async def upload_logo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Sube logo. Solo ADMIN. Guarda en /static/uploads/ y actualiza config."""
    await require_role("ADMIN")(current_user)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de imagen no permitido. Use PNG, JPEG, WEBP o GIF.")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Imagen demasiado grande. Máximo 2MB.")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Archivo vacío.")

    # Determinar extensión
    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
        # fallback según content-type
        mapping = {"image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}
        ext = mapping.get(file.content_type, ".png")

    filename = f"receipt_logo_{uuid.uuid4().hex}{ext}"
    # Limpiar logos antiguos para no acumular
    # Guardar nuevo
    dest = uploads_dir / filename
    with open(dest, "wb") as f:
        f.write(content)

    # Opcional: borrar logo anterior si existe
    cfg = await _get_or_create(session)
    if cfg.logo_path:
        try:
            old_path = static_dir / Path(cfg.logo_path.lstrip("/")).relative_to("static") if cfg.logo_path.startswith("/static") else Path(cfg.logo_path)
            # old_path ya es uploads/..., intentar borrar
            old_full = static_dir / Path(cfg.logo_path.replace("/static/", "").lstrip("/"))
            if old_full.exists() and old_full.is_file():
                # No borrar si es el mismo archivo recién subido
                if old_full.resolve() != dest.resolve():
                    old_full.unlink(missing_ok=True)
        except Exception:
            pass

    cfg.logo_path = f"/static/uploads/{filename}"
    await session.commit()
    await session.refresh(cfg)
    return ResponseSchema(success=True, message="Logo actualizado", data=_to_response(cfg))

@router.delete("/logo", response_model=ResponseSchema[ReceiptConfigResponse])
async def delete_logo(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Elimina logo. Solo ADMIN."""
    await require_role("ADMIN")(current_user)
    cfg = await _get_or_create(session)
    if cfg.logo_path:
        try:
            old_full = static_dir / Path(cfg.logo_path.replace("/static/", "").lstrip("/"))
            if old_full.exists():
                old_full.unlink(missing_ok=True)
        except Exception:
            pass
    cfg.logo_path = None
    await session.commit()
    await session.refresh(cfg)
    return ResponseSchema(success=True, message="Logo eliminado", data=_to_response(cfg))
