"""
Formatea los datos de un pedido en comandos ESC/POS para la JALTECH JALP58 (58mm).

Cambio respecto a la versión anterior
──────────────────────────────────────
print_order() ya NO lee config.RESTAURANT_NAME ni config.FOOTER_MESSAGE
directamente. Los recibe como parámetros explícitos desde main.py, que los
carga desde la BD vía GET /api/v1/receipt-config (con fallback al .env).

Esto garantiza que el ticket físico muestre siempre la misma información
que el panel de administración del recibo (admin-recibo.html).

Diseño del ticket (32 chars, papel 58mm)
─────────────────────────────────────────
  [NOMBRE RESTAURANTE — centrado, negrita, doble altura]
  ================================
  Pedido : #42
  Estado : NUEVO
  Fecha  : 5/9/26  8:04 am
  Mesa   : 03
  Mesero : Juan Pérez
  --------------------------------
  CANT NOMBRE          P.U.   TOTAL
  --------------------------------
  2    Arroz con Pollo $8.50 $17.00
  1    Jugo Natural    $3.00  $3.00
  --------------------------------
  Subtotal:                  $20.00
  TOTAL:                     $20.00
  ================================
      [footer_message — centrado]

Anchos de columna (total = PAPER_CHAR_WIDTH = 32)
  CANT : 4   NOMBRE : 15   P.U. : 6   TOTAL : 7
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import config

# ── Paper width ───────────────────────────────────────────────────────────────
W = config.PAPER_CHAR_WIDTH  # 32

# Column widths for the items table
_C_CANT = 4
_C_NOME = 15
_C_PU   = 6
_C_TOT  = W - _C_CANT - _C_NOME - _C_PU  # 7


# ── Formatting helpers ────────────────────────────────────────────────────────

def _money(cents: int) -> str:
    """Convert integer cents to '$X.XX' string."""
    return f"${(int(cents) / 100):.2f}"


def _center(text: str) -> str:
    return text.center(W)


def _separator(char: str = "-") -> str:
    return char * W


def _format_date(iso_str: Optional[str]) -> str:
    """Format an ISO datetime string to 'D/M/YY  H:MM am/pm'."""
    if not iso_str:
        return "—"
    try:
        s = iso_str if iso_str.endswith("Z") else iso_str + "Z"
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        hour   = dt.hour % 12 or 12
        minute = f"{dt.minute:02d}"
        ampm   = "am" if dt.hour < 12 else "pm"
        return f"{dt.day}/{dt.month}/{str(dt.year)[-2:]}  {hour}:{minute} {ampm}"
    except Exception:
        return str(iso_str)[:16]


def _col_row(cant: int, nombre: str, pu: int, total: int) -> str:
    """
    Build a fixed-width row for the items table.
    Long names wrap to a second line with leading indent.
    """
    pu_str   = _money(pu).rjust(_C_PU)
    tot_str  = _money(total).rjust(_C_TOT)
    cant_str = str(cant).ljust(_C_CANT)

    if len(nombre) <= _C_NOME:
        return f"{cant_str}{nombre.ljust(_C_NOME)}{pu_str}{tot_str}"

    line1 = f"{cant_str}{nombre[:_C_NOME]}{pu_str}{tot_str}"
    overflow = nombre[_C_NOME:_C_NOME * 2].strip()
    line2 = " " * _C_CANT + overflow
    return line1 + "\n" + line2


def _mesa(table_num) -> str:
    try:
        return str(int(table_num)).zfill(2)
    except (ValueError, TypeError):
        return str(table_num)


# ── Main entry point ──────────────────────────────────────────────────────────

def print_order(
    order: dict,
    printer,
    *,
    restaurant_name: Optional[str] = None,
    footer_message: Optional[str] = None,
) -> None:
    """
    Send a complete ticket to the ESC/POS printer.

    Parameters
    ──────────
    order            dict returned by GET /api/v1/orders/print-pending
    printer          open escpos printer instance (Win32Raw, Usb, etc.)
    restaurant_name  display name from receipt_config (BD); falls back to config.py
    footer_message   footer text from receipt_config (BD); falls back to config.py

    The restaurant_name and footer_message should be passed by main.py after
    loading them from the backend API.  Using keyword-only arguments ensures
    callers are explicit about the source of these values.

    Raises
    ──────
    PrinterContentError  if an ESC/POS encoding or command error occurs
                         (imported lazily to avoid circular import)
    Any other exception  is left to bubble up so main.py can classify it
    """
    rest   = (restaurant_name or config.RESTAURANT_NAME).strip()
    footer = (footer_message  or config.FOOTER_MESSAGE).strip()

    order_id     = order.get("id", "?")
    table_num    = order.get("table_number") or order.get("table_id", "?")
    camarero     = (order.get("camarero_name") or "—").strip()
    order_status = order.get("status", "NUEVO")
    total_cents  = int(order.get("total_amount", 0))
    notes        = (order.get("notes") or "").strip()
    created_at   = order.get("created_at", "")
    items        = order.get("items") or []

    # ── 1. Init ───────────────────────────────────────────────────────────────
    printer.hw("init")

    # ── 2. Restaurant name (centered, bold, double-height) ────────────────────
    printer.set(align="center", bold=True, double_height=True, double_width=False)
    printer.text(rest.upper() + "\n")

    # ── 3. Separator ──────────────────────────────────────────────────────────
    printer.set(align="left", bold=False, double_height=False)
    printer.text(_separator("=") + "\n")

    # ── 4. Order metadata ─────────────────────────────────────────────────────
    printer.text(f"Pedido : #{order_id}\n")
    printer.text(f"Estado : {order_status}\n")
    printer.text(f"Fecha  : {_format_date(created_at)}\n")
    printer.text(f"Mesa   : {_mesa(table_num)}\n")
    printer.text(f"Mesero : {camarero}\n")
    printer.text(_separator("-") + "\n")

    # ── 5. Column header ──────────────────────────────────────────────────────
    printer.set(align="left", bold=True)
    header = (
        "CANT".ljust(_C_CANT)
        + "NOMBRE".ljust(_C_NOME)
        + "P.U.".rjust(_C_PU)
        + "TOTAL".rjust(_C_TOT)
    )
    printer.text(header + "\n")
    printer.set(align="left", bold=False)
    printer.text(_separator("-") + "\n")

    # ── 6. Items ──────────────────────────────────────────────────────────────
    if items:
        for item in items:
            cant   = int(item.get("quantity", 1))
            nombre = (item.get("dish_name") or f"Plato #{item.get('dish_id','?')}").strip()
            pu     = int(item.get("unit_price", 0))
            total  = cant * pu
            printer.text(_col_row(cant, nombre, pu, total) + "\n")
    else:
        printer.text("(sin ítems)".center(W) + "\n")

    printer.text(_separator("-") + "\n")

    # ── 7. Totals ─────────────────────────────────────────────────────────────
    printer.set(align="left", bold=False)
    printer.text("Subtotal:".ljust(W - 10) + _money(total_cents).rjust(10) + "\n")
    printer.set(align="left", bold=True)
    printer.text("TOTAL:".ljust(W - 10) + _money(total_cents).rjust(10) + "\n")
    printer.set(align="left", bold=False)

    # ── 8. Notes (optional) ───────────────────────────────────────────────────
    if notes:
        printer.text(_separator("-") + "\n")
        printer.text("Notas:\n")
        for i in range(0, len(notes), W):
            printer.text(notes[i: i + W] + "\n")

    # ── 9. Footer ─────────────────────────────────────────────────────────────
    printer.text(_separator("=") + "\n")
    printer.set(align="center", bold=False)
    printer.text(footer + "\n")
    printer.text("\n\n")  # paper advance before cut

    # ── 10. Partial cut ───────────────────────────────────────────────────────
    printer.cut(mode="PART")
