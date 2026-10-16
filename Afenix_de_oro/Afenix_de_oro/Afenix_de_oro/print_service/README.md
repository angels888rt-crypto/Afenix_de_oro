# Servicio de Impresión Térmica — Afenix de Oro

Servicio Python independiente que corre en el **computador del restaurante** conectado
por USB a la impresora **JALTECH JALP58 de 58mm**.

Detecta pedidos nuevos automáticamente y los imprime via ESC/POS sin intervención del mesero.

---

## Arquitectura

```
Celular del mesero
      ↓  (Wi-Fi / red local)
Página web  →  POST /api/v1/orders
      ↓
Backend FastAPI  →  MySQL (orders.print_status = PENDING)
      ↓  (polling cada 5s)
Este servicio  →  GET /api/v1/orders/print-pending
      ↓  (ESC/POS via Win32Raw / pyusb)
Impresora JALTECH JALP58
```

---

## Requisitos

| Requisito | Versión mínima |
|-----------|----------------|
| Windows   | 10 / 11        |
| Python    | 3.10+          |
| Driver impresora JALP58 instalado en Windows | — |
| Backend Afenix de Oro corriendo | Puerto 8000 |

---

## Instalación rápida

1. **Conecta la JALP58 por USB** al computador e instala su driver.
   Verifica que aparezca en *Panel de Control → Dispositivos e impresoras*.
   Anota el nombre exacto (lo necesitas en el `.env`).

2. **Instala el servicio** haciendo doble clic en:
   ```
   print_service\install.bat
   ```
   El script:
   - Crea un entorno virtual Python (`venv/`)
   - Instala las dependencias (`requirements.txt`)
   - Crea el archivo `.env` desde `.env.example`
   - Abre `.env` en el Bloc de notas para que lo configures
   - Aplica la migración a la base de datos

3. **Configura `.env`** (se abre automáticamente durante la instalación):
   ```env
   PRINTER_NAME=JALTECH JALP58        ← nombre exacto en Windows
   RESTAURANT_NAME=Mi Restaurante     ← aparece en el ticket
   FOOTER_MESSAGE=¡Gracias por su visita!
   API_BASE_URL=http://localhost:8000 ← URL del backend
   PRINTER_API_KEY=afenix-print-2026  ← igual que en project/.env
   ```

4. **Aplica la migración** a MySQL (si no la aplicaste en el paso 2):

   **Opción A — Alembic** (desde la carpeta `project/`):
   ```bat
   cd project
   alembic upgrade head
   ```

   **Opción B — SQL directo** (desde MySQL Workbench o consola):
   ```sql
   -- Ejecutar el archivo print_service\apply_migration.sql
   mysql -u root -p proyecto_afenix < print_service\apply_migration.sql
   ```

5. **Inicia el servicio**:
   ```
   print_service\start_service.bat
   ```

---

## Uso diario

Cada vez que abras el restaurante, simplemente ejecuta `start_service.bat`.
Mantén la ventana abierta durante el servicio.

```
 ===================================================
  Servicio de Impresion Termica — Afenix de Oro
  Presiona Ctrl+C para detener
 ===================================================

2026-09-05 08:00:01 [INFO] Servicio de impresión Afenix de Oro iniciado
2026-09-05 08:00:01 [INFO] Backend   : http://localhost:8000
2026-09-05 08:00:01 [INFO] Impresora : JALTECH JALP58
2026-09-05 08:00:01 [INFO] Intervalo : 5s
2026-09-05 08:04:12 [INFO] 1 pedido(s) pendiente(s) de impresión
2026-09-05 08:04:12 [INFO] Procesando pedido #42 (mesa=03, intento=1/3)
2026-09-05 08:04:13 [INFO] Pedido #42 impreso correctamente ✓
```

---

## Estructura del ticket impreso

```
      MI RESTAURANTE
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
    ¡Gracias por su visita!
```

---

## Estados de impresión

| Estado     | Significado |
|------------|-------------|
| `PENDING`  | Pedido creado, esperando ser impreso |
| `PRINTING` | El servicio tomó el pedido y está imprimiendo |
| `PRINTED`  | Impresión exitosa |
| `ERROR`    | Falló después de `MAX_PRINT_ATTEMPTS` intentos |

Si un pedido queda en `ERROR`, el servicio **no lo vuelve a intentar automáticamente**.
Puedes reiniciarlo manualmente desde MySQL:
```sql
UPDATE orders SET print_status = 'PENDING', print_attempts = 0 WHERE id = 42;
```

---

## Configuración avanzada

### Cambiar el nombre de la impresora

Si la impresora aparece con un nombre diferente en Windows:

1. Abre *Panel de Control → Dispositivos e impresoras*
2. Haz clic derecho en la JALP58 → *Propiedades de la impresora*
3. Copia el nombre exacto del título de la ventana
4. Pégalo en `.env` como `PRINTER_NAME=<nombre exacto>`

### Si el backend corre en otro computador

Cambia `API_BASE_URL` en `.env`:
```env
API_BASE_URL=http://192.168.1.10:8000
```
Asegúrate de que el puerto 8000 esté accesible en la red local.

### Cambiar el intervalo de polling

```env
POLL_INTERVAL_SECONDS=3   # más rápido
POLL_INTERVAL_SECONDS=10  # más lento (menor carga)
```

### Logs

Los logs se guardan en `print_service\printer_service.log` y también se muestran
en la consola. Para ver solo errores:
```env
LOG_LEVEL=WARNING
```

---

## Solución de problemas

### "No se pudo conectar al backend"
- Verifica que el backend FastAPI esté corriendo (`python main.py` en `project/`)
- Verifica que `API_BASE_URL` en `.env` sea correcto
- Si hay firewall, permite el puerto 8000

### "No se pudo abrir Win32Raw"
- Verifica que el driver de la JALP58 esté instalado
- Verifica que `PRINTER_NAME` sea exactamente igual al nombre en Windows
- Intenta imprimir una página de prueba desde *Dispositivos e impresoras*

### "Pedido impreso dos veces"
Esto **no debería ocurrir** por diseño (el estado pasa a `PRINTING` antes de imprimir).
Si ocurre, verifica que no haya dos instancias del servicio corriendo al mismo tiempo.

### La migración falla con "Duplicate column"
Las columnas ya existen. No es un error — el script SQL usa `ADD COLUMN IF NOT EXISTS`.
Para Alembic, si falla, ejecuta el SQL directo.

---

## Archivos del servicio

```
print_service/
├── main.py              ← Punto de entrada, loop de polling
├── config.py            ← Lee variables de .env
├── api_client.py        ← HTTP al backend FastAPI
├── thermal_printer.py   ← Gestión de conexión a la impresora
├── ticket_formatter.py  ← Genera el ticket ESC/POS para la JALP58
├── requirements.txt     ← Dependencias Python
├── .env.example         ← Plantilla de configuración
├── .env                 ← Tu configuración (NO subir a git)
├── apply_migration.sql  ← Migración SQL alternativa a Alembic
├── run_migration.bat    ← Aplica la migración via Alembic
├── install.bat          ← Instalador completo (ejecutar primero)
├── start_service.bat    ← Inicia el servicio
└── README.md            ← Este archivo
```
