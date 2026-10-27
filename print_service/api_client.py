"""
Cliente HTTP para comunicarse con el backend FastAPI de Afenix de Oro.

Funciones públicas
──────────────────
get_pending_orders()      → list[dict]   pedidos con print_status=PENDING
set_print_status()        → str | None   nuevo print_status confirmado por backend
                                         devuelve None si la operación no aplica
                                         (already_reserved) o falla de red
get_receipt_config()      → dict | None  configuración de recibo desde la BD
                                         devuelve None si el backend no responde

Comportamiento ante already_reserved (atomicidad #1)
──────────────────────────────────────────────────────
El endpoint PUT /{id}/print-status con new_status=PRINTING devuelve
  { success: false, data: { already_reserved: true } }
cuando la guarda atómica detecta que otro proceso ya tomó el pedido.
set_print_status() devuelve None en ese caso para que main.py lo descarte
sin marcarlo como error.
"""
import logging
from typing import Optional

import requests

from config import (
    API_BASE_URL,
    PRINTER_API_KEY,
    HTTP_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

# Header enviado en todas las peticiones al backend
_HEADERS = {
    "X-Printer-Key": PRINTER_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get(url: str, params: dict | None = None) -> Optional[dict]:
    """GET with unified error handling. Returns parsed JSON or None."""
    try:
        resp = requests.get(
            url, headers=_HEADERS, params=params,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        logger.warning("Cannot reach backend at %s", API_BASE_URL)
        return None
    except requests.exceptions.Timeout:
        logger.warning("Timeout on GET %s (>%ds)", url, HTTP_TIMEOUT_SECONDS)
        return None
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error on GET %s: %s", url, exc)
        return None
    except Exception as exc:
        logger.error("Unexpected error on GET %s: %s", url, exc, exc_info=True)
        return None


def _put(url: str, body: dict) -> Optional[dict]:
    """PUT with unified error handling. Returns parsed JSON or None."""
    try:
        resp = requests.put(
            url, headers=_HEADERS, json=body,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        logger.warning("Cannot reach backend at %s", API_BASE_URL)
        return None
    except requests.exceptions.Timeout:
        logger.warning("Timeout on PUT %s (>%ds)", url, HTTP_TIMEOUT_SECONDS)
        return None
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error on PUT %s: %s", url, exc)
        return None
    except Exception as exc:
        logger.error("Unexpected error on PUT %s: %s", url, exc, exc_info=True)
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def get_pending_orders(limit: int = 20) -> list[dict]:
    """
    Return orders with print_status=PENDING from the backend.
    Returns an empty list on any network / backend error so the polling loop
    keeps running.
    """
    url = f"{API_BASE_URL}/api/v1/orders/print-pending"
    payload = _get(url, params={"limit": limit})
    if payload is None:
        return []
    orders = payload.get("data") or []
    logger.debug("Backend returned %d pending order(s)", len(orders))
    return orders


def set_print_status(order_id: int, new_status: str) -> Optional[str]:
    """
    Update the print_status of an order.

    Returns
    ───────
    str       — the confirmed new_status on success
    None      — when:
                  • new_status == 'PRINTING' and already_reserved == True
                    (another process claimed the order — skip silently)
                  • network / backend error (caller decides how to handle)

    The distinction matters for PRINTING:
      - already_reserved=True  → skip, do NOT mark as error
      - network error          → also None, but caller should log a warning
    """
    url = f"{API_BASE_URL}/api/v1/orders/{order_id}/print-status"
    payload = _put(url, {"print_status": new_status})

    if payload is None:
        # Network or HTTP error
        logger.warning(
            "Could not update print_status of order #%d to %s (network/HTTP error)",
            order_id, new_status,
        )
        return None

    data = payload.get("data") or {}

    # Atomic guard: backend signals that another process already reserved the order
    if data.get("already_reserved"):
        logger.info(
            "Order #%d already reserved by another process (print_status=%s) — skipping",
            order_id, data.get("print_status", "?"),
        )
        return None  # caller must NOT attempt to print or mark as error

    confirmed = data.get("print_status", new_status)
    logger.debug("Order #%d → print_status=%s confirmed", order_id, confirmed)
    return confirmed


def get_stale_printing_orders(timeout_minutes: int = 5) -> Optional[list[dict]]:
    """
    Return orders that have been stuck in PRINTING for more than timeout_minutes.

    These are candidates for RECOVERY_REQUIRED — the service likely crashed
    mid-print without recording the outcome.

    Returns
    ───────
    list[dict]  — list of stale orders (may be empty)
    None        — backend unreachable (caller should skip this cycle)
    """
    url = f"{API_BASE_URL}/api/v1/orders/print-stale"
    payload = _get(url, params={"timeout_minutes": timeout_minutes})
    if payload is None:
        return None  # network error — distinguish from empty list
    orders = payload.get("data") or []
    return orders


def get_receipt_config() -> Optional[dict]:
    """
    Fetch the receipt configuration (restaurant_name, footer_message, logo_url)
    from GET /api/v1/receipt-config.

    Returns the 'data' dict on success, None if the backend is unreachable.
    The caller must apply .env fallback values when None is returned.
    """
    url = f"{API_BASE_URL}/api/v1/receipt-config"
    payload = _get(url)
    if payload is None:
        logger.warning(
            "Could not fetch receipt config from backend — will use .env fallback values"
        )
        return None
    cfg = payload.get("data")
    if cfg:
        logger.debug(
            "Receipt config loaded: restaurant='%s'",
            cfg.get("restaurant_name", "?"),
        )
    return cfg
