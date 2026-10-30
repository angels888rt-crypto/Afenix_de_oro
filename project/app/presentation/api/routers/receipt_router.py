"""Receipt config API router — ADMIN configures, CAMARERO reads for thermal receipt."""
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.infrastructure.database.models import ReceiptConfigModel
from app.application.dto import ReceiptConfigResponse, ReceiptConfigUpdateRequest
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import get_current_user, require_role

from datetime import datetime

router = APIRouter(prefix="/api/v1/receipt-config", tags=["ReceiptConfig"])

DEFAULT_NAME = "RESTAURANTE"
DEFAULT_FOOTER = "¡Gracias por su visita!"
# El logo se guarda en base de datos (no en disco) para funcionar en contenedores
# de sólo lectura (hostless) y sobrevivir a redeploys.
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
MAX_SIZE = 2 * 1024 * 1024  # 2MB

LOGO_URL = "/api/v1/receipt-config/logo"


def _to_response(model: ReceiptConfigModel) -> ReceiptConfigResponse:
    logo_url = None
    # Si hay logo guardado en BD, lo servimos por endpoint (sobrevive a redeploys de contenedor).
    if model.logo_data:
        logo_url = LOGO_URL
    elif model.logo_path:
        # Fallback: ruta de archivo legacy (solo funciona si el disco es escribible).
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

@router.get("/logo")
async def get_logo(
    session: AsyncSession = Depends(get_session),
):
    """Sirve el logo del recibo desde la base de datos."""
    cfg = await _get_or_create(session)
    if not cfg.logo_data:
        raise HTTPException(status_code=404, detail="No hay logo configurado")
    return Response(content=cfg.logo_data, media_type=cfg.logo_content_type or "image/png")

@router.post("/logo", response_model=ResponseSchema[ReceiptConfigResponse])
async def upload_logo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Sube logo. Solo ADMIN. Guarda en base de datos (no en disco) para funcionar en contenedores de sólo lectura."""
    await require_role("ADMIN")(current_user)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de imagen no permitido. Use PNG, JPEG, WEBP o GIF.")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Imagen demasiado grande. Máximo 2MB.")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Archivo vacío.")

    cfg = await _get_or_create(session)
    cfg.logo_data = content
    cfg.logo_content_type = file.content_type
    # Mantener logo_path limpio (ya no apunta a archivo en disco)
    cfg.logo_path = None
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
    cfg.logo_data = None
    cfg.logo_content_type = None
    cfg.logo_path = None
    await session.commit()
    await session.refresh(cfg)
    return ResponseSchema(success=True, message="Logo eliminado", data=_to_response(cfg))
