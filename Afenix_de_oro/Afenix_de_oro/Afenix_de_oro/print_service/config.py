"""
Configuración del servicio de impresión térmica — Afenix de Oro.
Lee variables de entorno desde print_service/.env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la misma carpeta que este archivo
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)


# ── Backend API ──────────────────────────────────────────────────────────────
# URL base del servidor FastAPI (sin barra final)
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

# Clave de API del servicio de impresión (debe coincidir con PRINTER_API_KEY en project/.env)
PRINTER_API_KEY: str = os.getenv("PRINTER_API_KEY", "afenix-print-2026")

# ── Impresora ────────────────────────────────────────────────────────────────
# Nombre del dispositivo tal como aparece en Panel de Control → Dispositivos e impresoras
PRINTER_NAME: str = os.getenv("PRINTER_NAME", "JALTECH JALP58")

# Ancho de papel en caracteres para impresora de 58mm (~32 chars con fuente normal)
PAPER_CHAR_WIDTH: int = int(os.getenv("PAPER_CHAR_WIDTH", "32"))

# ── Fallback de configuración del recibo ────────────────────────────────────
# Usados SOLO si GET /api/v1/receipt-config falla o el backend no está disponible.
# En condiciones normales, los valores vienen de la base de datos vía el backend.
RESTAURANT_NAME: str = os.getenv("RESTAURANT_NAME", "RESTAURANTE")
FOOTER_MESSAGE: str = os.getenv("FOOTER_MESSAGE", "¡Gracias por su visita!")

# ── Polling ──────────────────────────────────────────────────────────────────
# Segundos entre cada consulta de pedidos pendientes
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))

# Timeout HTTP para peticiones al backend (en segundos)
HTTP_TIMEOUT_SECONDS: int = int(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))

# ── Recuperación de PRINTING bloqueados ──────────────────────────────────────
# Pedidos que lleven más de este tiempo en estado PRINTING se consideran
# bloqueados (crash / apagón durante la impresión) y se mueven a
# RECOVERY_REQUIRED para revisión manual.
# Debe ser mayor que el tiempo máximo de impresión de un ticket (~30 s).
PRINTING_TIMEOUT_MINUTES: int = int(os.getenv("PRINTING_TIMEOUT_MINUTES", "5"))

# ── Backoff progresivo para impresora no disponible ──────────────────────────
# Espera inicial (segundos) tras el primer fallo de impresora no disponible.
PRINT_BACKOFF_BASE_SECONDS: int = int(os.getenv("PRINT_BACKOFF_BASE_SECONDS", "30"))

# Multiplicador aplicado tras cada fallo consecutivo de impresora no disponible.
# Ejemplo: 30s → 60s → 120s → 240s → ... hasta MAX
PRINT_BACKOFF_MULTIPLIER: float = float(os.getenv("PRINT_BACKOFF_MULTIPLIER", "2.0"))

# Espera máxima entre reintentos cuando la impresora está no disponible (segundos).
PRINT_BACKOFF_MAX_SECONDS: int = int(os.getenv("PRINT_BACKOFF_MAX_SECONDS", "300"))

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", "printer_service.log")
