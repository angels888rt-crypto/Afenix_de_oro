-- ============================================================
--  Migración manual completa — Afenix de Oro
--  Equivalente a: cd project && alembic upgrade head
--  Base de datos: proyecto_afenix
--
--  Usar SOLO si no puedes correr Alembic directamente.
--
--  Cómo ejecutarlo:
--    mysql -u root -p proyecto_afenix < apply_migration.sql
--  O pegar el contenido en MySQL Workbench / phpMyAdmin.
--
--  Qué hace este script:
--    Migración 002 — agrega columnas de impresión a orders
--    Migración 003 — crea tabla receipt_config e inserta registro por defecto
--
--  Qué NO hace:
--    - No toca users, dishes, tables, notifications
--    - No modifica pedidos existentes (solo agrega columnas con DEFAULT)
--    - No elimina ningún dato
-- ============================================================

USE proyecto_afenix;

-- ============================================================
-- MIGRACIÓN 002: columnas de impresión en orders
-- ============================================================

-- VARCHAR(20) necesario para acomodar RECOVERY_REQUIRED (17 chars)
-- Valores válidos: PENDING | PRINTING | PRINTED | ERROR | RECOVERY_REQUIRED
ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS print_status   VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        COMMENT 'Estado de impresión térmica: PENDING | PRINTING | PRINTED | ERROR | RECOVERY_REQUIRED',
    ADD COLUMN IF NOT EXISTS print_attempts INT         NOT NULL DEFAULT 0
        COMMENT 'Número de intentos de impresión realizados',
    ADD COLUMN IF NOT EXISTS printed_at     DATETIME    NULL
        COMMENT 'Timestamp en que el pedido fue impreso correctamente';

-- Índice para que el servicio encuentre rápidamente los pedidos PENDING
CREATE INDEX IF NOT EXISTS idx_print_status ON orders (print_status);

-- ============================================================
-- MIGRACIÓN 003: tabla de configuración del recibo
-- ============================================================

-- Crea la tabla solo si no existe (idempotente)
CREATE TABLE IF NOT EXISTS receipt_config (
    id              INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    restaurant_name VARCHAR(100) NOT NULL DEFAULT 'RESTAURANTE'
        COMMENT 'Nombre del restaurante que aparece en el ticket térmico',
    footer_message  VARCHAR(500) NOT NULL DEFAULT '¡Gracias por su visita!'
        COMMENT 'Mensaje al pie del ticket térmico',
    logo_path       VARCHAR(255) NULL
        COMMENT 'Ruta relativa del logo bajo /static/uploads/, NULL si no hay logo',
    created_at      DATETIME     NOT NULL,
    updated_at      DATETIME     NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar registro singleton id=1 solo si no existe (idempotente)
INSERT INTO receipt_config (id, restaurant_name, footer_message, logo_path, created_at, updated_at)
SELECT 1, 'RESTAURANTE', '¡Gracias por su visita!', NULL, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM receipt_config WHERE id = 1);

-- ============================================================
-- VERIFICACIÓN FINAL
-- ============================================================

SELECT 'orders — columnas de impresión' AS verificacion;
SELECT
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'proyecto_afenix'
  AND TABLE_NAME   = 'orders'
  AND COLUMN_NAME  IN ('print_status', 'print_attempts', 'printed_at')
ORDER BY ORDINAL_POSITION;

SELECT 'receipt_config — tabla y registro' AS verificacion;
SELECT id, restaurant_name, footer_message, logo_path FROM receipt_config WHERE id = 1;
