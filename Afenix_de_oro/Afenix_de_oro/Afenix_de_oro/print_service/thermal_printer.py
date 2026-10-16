"""
Abstracción de la impresora térmica JALTECH JALP58.

Jerarquía de excepciones
─────────────────────────
PrinterError                   — base para todos los errores de impresora
  └─ PrinterUnavailableError   — impresora apagada / desconectada / no encontrada
                                 → reintento automático con backoff en main.py
  └─ PrinterContentError       — error en el contenido/formato del ticket
                                 → ERROR permanente, no reintentar

La distinción es crítica para evitar reintentos infinitos de errores de
contenido que nunca se resolverían solos, y para no abandonar pedidos
cuando el problema es simplemente la impresora física.

Estrategia de conexión en Windows (orden de preferencia)
──────────────────────────────────────────────────────────
1. Win32Raw  — usa win32print (spooler de Windows) con el nombre de impresora
               configurado en Dispositivos e impresoras. Más confiable en USB.
2. USB directo via pyusb — busca dispositivos de clase Printer (0x07).
               Fallback si win32print no está disponible.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


# ── Jerarquía de excepciones ─────────────────────────────────────────────────

class PrinterError(Exception):
    """Base exception for all thermal printer errors."""


class PrinterUnavailableError(PrinterError):
    """
    Raised when the printer cannot be reached: powered off, USB disconnected,
    driver not responding, or spooler not ready.

    Safe to retry automatically — the physical problem is likely transient.
    """


class PrinterContentError(PrinterError):
    """
    Raised when the ticket content itself causes the error (bad encoding,
    unsupported ESC/POS command, etc.) rather than a connectivity issue.

    Do NOT retry automatically — the same content will fail again.
    Mark the order as ERROR permanently.
    """


# ── Connection helpers ────────────────────────────────────────────────────────

def _open_win32raw(printer_name: str):
    """
    Attempt to open the printer using escpos.printer.Win32Raw.

    Returns the printer instance on success, None if the driver or module
    is not available.

    Raises PrinterUnavailableError if the printer name is known but the
    device is currently unreachable (offline, powered off, paper out…).
    """
    try:
        from escpos.printer import Win32Raw
        p = Win32Raw(printer_name)
        logger.debug("Win32Raw: opened '%s'", printer_name)
        return p
    except ImportError:
        logger.warning(
            "escpos.printer.Win32Raw not available — pywin32 may not be installed"
        )
        return None
    except Exception as exc:
        exc_str = str(exc).lower()
        # Distinguish "printer not found / offline" from other errors
        unavailable_hints = (
            "not found", "no se encontró", "invalid", "access denied",
            "offline", "not ready", "port", "error opening",
        )
        if any(hint in exc_str for hint in unavailable_hints):
            raise PrinterUnavailableError(
                f"Impresora '{printer_name}' no disponible: {exc}"
            ) from exc
        # Unknown error on Win32Raw — treat as unavailable (connection-level)
        logger.warning("Win32Raw('%s') failed: %s", printer_name, exc)
        raise PrinterUnavailableError(
            f"No se pudo abrir la impresora '{printer_name}': {exc}"
        ) from exc


def _open_usb_escpos():
    """
    Attempt to open a USB thermal printer using escpos.printer.Usb + pyusb.

    Scans for USB devices of class 7 (Printer) and connects to the first one.
    Returns the printer instance on success, None if not found.
    """
    try:
        import usb.core
        from escpos.printer import Usb

        devices = usb.core.find(find_all=True, bDeviceClass=0x00)
        for dev in (devices or []):
            try:
                for cfg in dev:
                    for intf in cfg:
                        if intf.bInterfaceClass == 0x07:  # Printer class
                            vid = dev.idVendor
                            pid = dev.idProduct
                            logger.info(
                                "USB printer detected: VID=0x%04x PID=0x%04x", vid, pid
                            )
                            printer = Usb(vid, pid, profile="default")
                            return printer
            except Exception:
                continue

        logger.warning("No USB printer found (class 0x07)")
        return None

    except ImportError:
        logger.warning("pyusb not installed — USB direct mode unavailable")
        return None
    except Exception as exc:
        logger.warning("USB scan error: %s", exc)
        return None


# ── PrinterManager ────────────────────────────────────────────────────────────

class PrinterManager:
    """
    Manages the connection lifecycle of the thermal printer.

    Usage (context manager):
        with PrinterManager("JALTECH JALP58") as pm:
            ticket_formatter.print_order(order, pm.get_printer(), ...)

    Exception semantics:
        open() raises PrinterUnavailableError if the printer cannot be reached
        after all connection attempts.  It never raises PrinterContentError —
        content errors are raised by ticket_formatter.print_order() instead.
    """

    def __init__(
        self,
        printer_name: str,
        connection_retries: int = 2,
        retry_delay: float = 1.5,
    ):
        self.printer_name = printer_name
        self.connection_retries = connection_retries
        self.retry_delay = retry_delay
        self._printer = None

    # ── Open / close ──────────────────────────────────────────────────────────

    def open(self) -> "PrinterManager":
        """
        Open a connection to the printer.

        Tries Win32Raw first, then USB direct.
        Raises PrinterUnavailableError if all attempts fail.
        """
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.connection_retries + 1):
            logger.debug(
                "Connection attempt %d/%d for '%s'",
                attempt, self.connection_retries, self.printer_name,
            )

            # ── Method 1: Win32Raw (recommended for Windows + USB) ────────────
            try:
                printer = _open_win32raw(self.printer_name)
                if printer is not None:
                    logger.info("Printer opened via Win32Raw: '%s'", self.printer_name)
                    self._printer = printer
                    return self
            except PrinterUnavailableError as exc:
                last_exc = exc
                # Fall through to USB fallback

            # ── Method 2: USB direct via pyusb ───────────────────────────────
            printer = _open_usb_escpos()
            if printer is not None:
                logger.info("Printer opened via USB/pyusb")
                self._printer = printer
                return self

            if attempt < self.connection_retries:
                logger.warning(
                    "Could not open printer on attempt %d — retrying in %.1fs",
                    attempt, self.retry_delay,
                )
                time.sleep(self.retry_delay)

        raise PrinterUnavailableError(
            f"Impresora '{self.printer_name}' no disponible después de "
            f"{self.connection_retries} intento(s). "
            f"Verifique que esté encendida y conectada por USB."
            + (f" Último error: {last_exc}" if last_exc else "")
        )

    def close(self) -> None:
        """Close the printer connection if open."""
        if self._printer is not None:
            try:
                self._printer.close()
            except Exception as exc:
                logger.debug("Error closing printer (ignored): %s", exc)
            finally:
                self._printer = None

    def get_printer(self):
        """Return the open printer instance."""
        if self._printer is None:
            raise PrinterUnavailableError(
                "Printer is not open. Call open() first."
            )
        return self._printer

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "PrinterManager":
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False  # do not suppress exceptions
