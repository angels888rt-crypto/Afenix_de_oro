"""
Servicio local de impresión térmica — Afenix de Oro
====================================================

Flujo de cada ciclo de polling
───────────────────────────────
1. Al arrancar:
   a. Cargar configuración del recibo desde la BD (GET /api/v1/receipt-config).
      Si el backend no responde → usar valores del .env como fallback.
   b. Recuperar pedidos bloqueados en PRINTING (función _recover_stale_printing).
      Los que llevan más de PRINTING_TIMEOUT_MINUTES → RECOVERY_REQUIRED.
      No se reimprimen automáticamente para evitar duplicados.

2. Cada POLL_INTERVAL_SECONDS:
   a. Consultar GET /api/v1/orders/print-pending.
   b. Para cada pedido PENDING:
      i.  PUT → PRINTING (guarda atómica WHERE print_status='PENDING').
          Si already_reserved=True → saltar sin marcar error.
      ii. Abrir impresora y enviar ticket ESC/POS.
      iii.Según resultado:
          • Éxito                     → PRINTED
          • PrinterUnavailableError   → backoff progresivo, volver a PENDING
            (30s → 60s → 120s → … hasta 300s, sin límite de intentos)
          • Error ambiguo post-envío  → RECOVERY_REQUIRED
            (datos ya enviados, no se sabe si imprimió — no reintentar)
          • PrinterContentError       → ERROR permanente

3. Cada PRINTING_TIMEOUT_MINUTES × 60 segundos (también al arrancar):
   Ejecutar _recover_stale_printing() para capturar crashes en producción.

Estados de print_status
────────────────────────
  PENDING            → recién creado, esperando impresión
  PRINTING           → reservado por este servicio, enviando a la impresora
  PRINTED            → bytes entregados al spooler → impresión exitosa
  ERROR              → error de contenido/configuración, no reintentable
  RECOVERY_REQUIRED  → ambigüedad post-envío o PRINTING bloqueado (apagón)
                       requiere revisión/reimpresión manual

Cómo recuperar un pedido en RECOVERY_REQUIRED
──────────────────────────────────────────────
  UPDATE orders SET print_status='PENDING', print_attempts=0 WHERE id=<id>;
"""
import logging
import signal
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import config
import api_client
import ticket_formatter
from thermal_printer import (
    PrinterManager,
    PrinterError,
    PrinterUnavailableError,
    PrinterContentError,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("print_service")

# ── Graceful shutdown ─────────────────────────────────────────────────────────
_running = True


def _handle_stop(signum, frame):
    global _running
    logger.info("Stop signal received — shutting down gracefully...")
    _running = False


signal.signal(signal.SIGINT, _handle_stop)
signal.signal(signal.SIGTERM, _handle_stop)


# ── Receipt config (loaded at startup, refreshed periodically) ────────────────
# Holds the values from GET /api/v1/receipt-config.
# Falls back to config.py values if the backend is unreachable.
_receipt_config: dict = {
    "restaurant_name": config.RESTAURANT_NAME,
    "footer_message":  config.FOOTER_MESSAGE,
    "logo_path":       None,
}

# Refresh receipt config from backend every N seconds (10 minutes default)
_RECEIPT_CONFIG_REFRESH_SECS = 600
_last_receipt_config_refresh: float = 0.0


def _load_receipt_config() -> None:
    """
    Fetch receipt config from backend and update _receipt_config in-place.
    Falls back silently to .env values if the backend is not available.
    """
    global _last_receipt_config_refresh
    cfg = api_client.get_receipt_config()
    if cfg:
        _receipt_config["restaurant_name"] = (
            cfg.get("restaurant_name") or config.RESTAURANT_NAME
        )
        _receipt_config["footer_message"] = (
            cfg.get("footer_message") or config.FOOTER_MESSAGE
        )
        _receipt_config["logo_path"] = cfg.get("logo_path")
        logger.info(
            "Receipt config loaded from DB: restaurant='%s'",
            _receipt_config["restaurant_name"],
        )
    else:
        logger.warning(
            "Using .env fallback for receipt config: restaurant='%s'",
            _receipt_config["restaurant_name"],
        )
    _last_receipt_config_refresh = time.monotonic()


# ── Stale PRINTING recovery ───────────────────────────────────────────────────
# Last time _recover_stale_printing() was run (monotonic seconds)
_last_recovery_check: float = 0.0
_RECOVERY_CHECK_INTERVAL_SECS = config.PRINTING_TIMEOUT_MINUTES * 60


def _recover_stale_printing() -> None:
    """
    Find orders that have been stuck in PRINTING longer than
    PRINTING_TIMEOUT_MINUTES and move them to RECOVERY_REQUIRED.

    This handles crashes, power cuts and abnormal terminations where the
    service died mid-print without confirming the result.

    We do NOT reset these to PENDING automatically because:
    • The ticket may have already been sent to the printer spooler.
    • Automatic reset would risk printing the same order twice.
    • An operator can reset manually after verifying the physical ticket.
    """
    global _last_recovery_check

    cutoff_utc = datetime.now(timezone.utc) - timedelta(
        minutes=config.PRINTING_TIMEOUT_MINUTES
    )
    cutoff_iso = cutoff_utc.isoformat()

    logger.debug(
        "Recovery check: looking for orders in PRINTING older than %d min (cutoff %s)",
        config.PRINTING_TIMEOUT_MINUTES,
        cutoff_iso,
    )

    # The backend /print-pending only returns PENDING orders.
    # To find stale PRINTING orders we need a dedicated query.
    # We reuse the general print-status endpoint per-order — but we don't have
    # a list endpoint for PRINTING orders. Instead we call a recovery helper
    # on the backend that returns stale PRINTING orders.
    stale = api_client.get_stale_printing_orders(
        timeout_minutes=config.PRINTING_TIMEOUT_MINUTES
    )

    if stale is None:
        # Backend not reachable — skip this cycle, try next time
        logger.warning("Recovery check skipped — backend not reachable")
        _last_recovery_check = time.monotonic()
        return

    if not stale:
        logger.debug("Recovery check: no stale PRINTING orders found")
        _last_recovery_check = time.monotonic()
        return

    logger.warning(
        "Recovery check: found %d stale PRINTING order(s) — moving to RECOVERY_REQUIRED",
        len(stale),
    )
    for order in stale:
        order_id = order["id"]
        confirmed = api_client.set_print_status(order_id, "RECOVERY_REQUIRED")
        if confirmed:
            logger.warning(
                "Order #%d moved to RECOVERY_REQUIRED "
                "(was PRINTING for >%d min — possible crash during print). "
                "To reprint: UPDATE orders SET print_status='PENDING', "
                "print_attempts=0 WHERE id=%d;",
                order_id,
                config.PRINTING_TIMEOUT_MINUTES,
                order_id,
            )
        else:
            logger.error(
                "Could not move order #%d to RECOVERY_REQUIRED — will retry next cycle",
                order_id,
            )

    _last_recovery_check = time.monotonic()


# ── Backoff state per order ───────────────────────────────────────────────────
# Maps order_id → (consecutive_unavailable_failures, next_retry_after_monotonic)
# Cleared when the order is successfully printed or moved to another terminal state.
_backoff_state: dict[int, tuple[int, float]] = {}


def _compute_backoff(failures: int) -> float:
    """
    Exponential backoff seconds for consecutive printer-unavailable failures.
      failures=1 → BASE (30s)
      failures=2 → BASE × MULT (60s)
      failures=3 → BASE × MULT² (120s)
      …capped at MAX (300s)
    """
    delay = config.PRINT_BACKOFF_BASE_SECONDS * (
        config.PRINT_BACKOFF_MULTIPLIER ** (failures - 1)
    )
    return min(delay, config.PRINT_BACKOFF_MAX_SECONDS)


def _clear_backoff(order_id: int) -> None:
    _backoff_state.pop(order_id, None)


def _is_in_backoff(order_id: int) -> bool:
    """Return True if this order is still within its backoff window."""
    if order_id not in _backoff_state:
        return False
    _failures, retry_after = _backoff_state[order_id]
    return time.monotonic() < retry_after


# ── Order processing ──────────────────────────────────────────────────────────

def _process_order(order: dict) -> None:
    """
    Attempt to print a single order.

    Decision table
    ──────────────
    already_reserved          → skip silently (atomicity guard fired)
    PrinterUnavailableError   → keep PRINTING?, apply backoff, reset to PENDING
    post-send ambiguous error → RECOVERY_REQUIRED (no reprint)
    PrinterContentError       → ERROR permanent
    success                   → PRINTED
    """
    order_id = order["id"]
    table    = order.get("table_number") or order.get("table_id", "?")

    # ── Backoff check ─────────────────────────────────────────────────────────
    if _is_in_backoff(order_id):
        failures, retry_after = _backoff_state[order_id]
        remaining = retry_after - time.monotonic()
        logger.debug(
            "Order #%d in backoff — %.0fs remaining (after %d unavailable failure(s))",
            order_id, remaining, failures,
        )
        return  # leave as PENDING, retry after backoff window expires

    logger.info("Processing order #%d (table=%s)", order_id, table)

    # ── Step 1: atomic reservation PENDING → PRINTING ─────────────────────────
    confirmed = api_client.set_print_status(order_id, "PRINTING")
    if confirmed is None:
        # already_reserved=True OR network error — skip without marking error
        logger.info(
            "Order #%d skipped (already reserved by another process or network error)",
            order_id,
        )
        return

    # ── Step 2: open printer and send ticket ──────────────────────────────────
    pm = PrinterManager(
        printer_name=config.PRINTER_NAME,
        connection_retries=2,
        retry_delay=1.5,
    )

    _sending_started = False  # tracks whether any bytes were sent

    try:
        with pm as manager:
            printer = manager.get_printer()
            # Signal that data transfer is about to begin
            _sending_started = True
            ticket_formatter.print_order(
                order,
                printer,
                restaurant_name=_receipt_config["restaurant_name"],
                footer_message=_receipt_config["footer_message"],
            )

        # ── Step 3a: success → PRINTED ────────────────────────────────────────
        result = api_client.set_print_status(order_id, "PRINTED")
        if result:
            logger.info("Order #%d printed successfully ✓", order_id)
            _clear_backoff(order_id)
        else:
            logger.warning(
                "Order #%d printed physically but could not confirm PRINTED in backend",
                order_id,
            )
            _clear_backoff(order_id)

    except PrinterUnavailableError as exc:
        # ── Printer was unreachable — safe to retry ────────────────────────────
        logger.warning("Order #%d — printer unavailable: %s", order_id, exc)

        failures = _backoff_state.get(order_id, (0, 0.0))[0] + 1
        backoff_secs = _compute_backoff(failures)
        retry_at = time.monotonic() + backoff_secs
        _backoff_state[order_id] = (failures, retry_at)

        logger.warning(
            "Order #%d → PENDING for retry in %.0fs (unavailable failure #%d)",
            order_id, backoff_secs, failures,
        )
        # Reset to PENDING so it re-appears in the next poll after backoff
        api_client.set_print_status(order_id, "PENDING")

    except PrinterContentError as exc:
        # ── Content error — permanent failure, no retry ───────────────────────
        logger.error(
            "Order #%d — content error (permanent): %s", order_id, exc
        )
        api_client.set_print_status(order_id, "ERROR")
        _clear_backoff(order_id)

    except Exception as exc:
        # ── Unknown error ─────────────────────────────────────────────────────
        if _sending_started:
            # Data transfer may have begun — outcome unknown — never reprint
            logger.error(
                "Order #%d — ambiguous error AFTER data send started: %s. "
                "Moving to RECOVERY_REQUIRED to prevent duplicate print.",
                order_id, exc, exc_info=True,
            )
            api_client.set_print_status(order_id, "RECOVERY_REQUIRED")
        else:
            # Data transfer never started — treat as unavailable, apply backoff
            logger.error(
                "Order #%d — unexpected error BEFORE data send: %s. "
                "Treating as printer unavailable, will retry with backoff.",
                order_id, exc, exc_info=True,
            )
            failures = _backoff_state.get(order_id, (0, 0.0))[0] + 1
            backoff_secs = _compute_backoff(failures)
            _backoff_state[order_id] = (failures, time.monotonic() + backoff_secs)
            api_client.set_print_status(order_id, "PENDING")

        _clear_backoff(order_id) if _sending_started else None


# ── Main polling loop ─────────────────────────────────────────────────────────

def run_polling_loop() -> None:
    """Main loop: load config, recover stale orders, poll and print."""
    logger.info("=" * 56)
    logger.info("  Afenix de Oro — Thermal Print Service")
    logger.info("  Backend  : %s", config.API_BASE_URL)
    logger.info("  Printer  : %s", config.PRINTER_NAME)
    logger.info("  Interval : %ds", config.POLL_INTERVAL_SECONDS)
    logger.info("  Backoff  : %ds base, x%.1f, max %ds",
                config.PRINT_BACKOFF_BASE_SECONDS,
                config.PRINT_BACKOFF_MULTIPLIER,
                config.PRINT_BACKOFF_MAX_SECONDS)
    logger.info("  Recovery : PRINTING timeout %d min → RECOVERY_REQUIRED",
                config.PRINTING_TIMEOUT_MINUTES)
    logger.info("=" * 56)

    # ── Startup: load receipt config and recover stale orders ─────────────────
    _load_receipt_config()
    _recover_stale_printing()

    consecutive_empty = 0

    while _running:
        now = time.monotonic()

        # ── Periodic receipt config refresh (every 10 min) ────────────────────
        if now - _last_receipt_config_refresh >= _RECEIPT_CONFIG_REFRESH_SECS:
            _load_receipt_config()

        # ── Periodic stale PRINTING recovery ──────────────────────────────────
        if now - _last_recovery_check >= _RECOVERY_CHECK_INTERVAL_SECS:
            _recover_stale_printing()

        # ── Poll for pending orders ────────────────────────────────────────────
        try:
            pending = api_client.get_pending_orders()

            if not pending:
                consecutive_empty += 1
                if consecutive_empty % 12 == 1:
                    logger.debug("No pending orders")
            else:
                consecutive_empty = 0
                # Filter out orders still in backoff window
                actionable = [o for o in pending if not _is_in_backoff(o["id"])]
                in_backoff  = len(pending) - len(actionable)
                if in_backoff:
                    logger.info(
                        "%d pending order(s) — %d actionable, %d in backoff",
                        len(pending), len(actionable), in_backoff,
                    )
                else:
                    logger.info("%d pending order(s)", len(pending))

                for order in actionable:
                    if not _running:
                        break
                    _process_order(order)

        except Exception as exc:
            logger.error("Error in polling loop: %s", exc, exc_info=True)

        # ── Interruptible sleep ────────────────────────────────────────────────
        for _ in range(config.POLL_INTERVAL_SECONDS * 10):
            if not _running:
                break
            time.sleep(0.1)

    logger.info("Print service stopped cleanly.")


if __name__ == "__main__":
    run_polling_loop()
