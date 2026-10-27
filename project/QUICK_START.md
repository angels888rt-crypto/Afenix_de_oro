"""
QUICK_START.md - Guía de Inicio Rápido (5 Minutos)

Para los impacientes: Los pasos mínimos para ejecutar la API en tu máquina local.
"""

# REQUISITOS PREVIOS

✓ Python 3.12+
✓ MySQL 8.0+ (en ejecución)
✓ pip (incluido con Python)


# PASO 1: CONFIGURAR BASE DE DATOS (1 minuto)

## Opción A: MySQL Tradicional

Abre MySQL Workbench o línea de comandos:

```sql
CREATE DATABASE restaurant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'restaurant_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON restaurant_db.* TO 'restaurant_user'@'localhost';
FLUSH PRIVILEGES;
```

## Opción B: Docker Compose (Recomendado)

```bash
docker-compose up -d
# Espera 10-15 segundos para que MySQL inicie completamente
```

Credenciales:
- Usuario: restaurant_user
- Contraseña: secure_password
- Database: restaurant_db
- Host: localhost:3306


# PASO 2: CONFIGURAR PROYECTO (1 minuto)

```bash
# Entrar al directorio del proyecto
cd path/to/project

# Copiar archivo de configuración
copy .env.example .env
# O en Linux/Mac:
# cp .env.example .env
```

El archivo .env ya tiene los valores correctos para desarrollo local.
Si usaste opciones diferentes de MySQL, edita el archivo .env.


# PASO 3: INSTALAR DEPENDENCIAS (2 minutos)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Linux/Mac:
source venv/bin/activate

# Instalar librerías
pip install -r requirements.txt
```


# PASO 4: CONFIGURAR BASE DE DATOS (30 segundos)

```bash
# Ejecutar migraciones
alembic upgrade head

# Cargar datos de demostración (Opcional)
python init_demo_data.py
```


# PASO 5: INICIAR SERVIDOR (¡LISTO!)

```bash
uvicorn main:app --reload
```

Verás algo como:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```


# PASO 6: ACCEDER A LA API

Abre en tu navegador:

**Documentación interactiva:**
- http://localhost:8000/api/docs (Swagger UI - Mejor opción)
- http://localhost:8000/api/redoc (ReDoc - Más limpio)

**Health check:**
- http://localhost:8000/health

**Desde terminal:**
```bash
curl http://localhost:8000/health
```


# PRIMEROS PASOS EN LA API

## 1. Registrar Usuario

En Swagger UI (http://localhost:8000/api/docs):

1. Busca "POST /api/v1/users/register"
2. Click en "Try it out"
3. Ingresa:
```json
{
  "username": "mi_usuario",
  "email": "mi@email.com",
  "password": "password123",
  "full_name": "Mi Nombre",
  "role": "CAMARERO"
}
```
4. Click en "Execute"


## 2. Iniciar Sesión

Busca "POST /api/v1/users/login":

```json
{
  "username": "mi_usuario",
  "password": "password123"
}
```

Copia el `access_token` de la respuesta.


## 3. Usar el Token

En Swagger UI:
1. Click en el botón "Authorize" (arriba a la derecha)
2. Pega: `Bearer <tu_token>`
3. Click en "Authorize"

Ahora todos los endpoints estarán autenticados.


## 4. Ver Platos Disponibles

Busca "GET /api/v1/dishes/available/list" y click en "Execute".

Verás todos los platos disponibles del menú.


## 5. Crear un Pedido

Busca "POST /api/v1/orders":

```json
{
  "table_id": 1,
  "items": [
    {
      "dish_id": 1,
      "quantity": 2,
      "special_notes": "Sin picante"
    }
  ],
  "notes": ""
}
```

¡Acabas de crear un pedido en una mesa!


## 6. Ver Notificaciones

Como cocinero, accede con:

```json
{
  "username": "cocinero1",
  "password": "cocinero123"
}
```

Luego busca "GET /api/v1/notifications/unread".

Verás notificaciones de nuevos pedidos.


# USUARIOS DE DEMOSTRACIÓN

Si ejecutaste `python init_demo_data.py`:

| Username | Rol | Contraseña |
|----------|-----|-----------|
| admin | ADMIN | admin123 |
| cocinero1 | COCINERO | cocinero123 |
| cocinero2 | COCINERO | cocinero123 |
| camarero1 | CAMARERO | camarero123 |
| camarero2 | CAMARERO | camarero123 |


# COMANDOS ÚTILES

```bash
# Ver estado del servidor
curl http://localhost:8000/health

# Registrar usuario (con curl)
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test",
    "email": "test@test.com",
    "password": "test123",
    "full_name": "Test User",
    "role": "CAMARERO"
  }'

# Iniciar sesión
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test",
    "password": "test123"
  }'

# Obtener mis datos (reemplazar TOKEN)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer TOKEN"

# Ver mesas disponibles
curl http://localhost:8000/api/v1/tables/available/list \
  -H "Authorization: Bearer TOKEN"

# Detener servidor
# Ctrl + C en la terminal
```


# ESTRUCTURA DE CARPETAS

```
project/
├── app/
│   ├── domain/              # Lógica de negocio
│   ├── application/         # Casos de uso
│   ├── infrastructure/      # Base de datos
│   ├── presentation/        # API REST
│   └── shared/              # Código transversal
├── alembic/                 # Migraciones BD
├── main.py                  # Punto de entrada
├── requirements.txt         # Dependencias
├── .env.example             # Configuración ejemplo
├── .env                     # Tu configuración (local)
└── README.md                # Documentación
```


# DOCUMENTACIÓN

Para más detalles:
- **README.md** - Documentación completa
- **ARCHITECTURE.md** - Explicación de arquitectura
- **EXAMPLES.md** - Ejemplos de todos los endpoints
- **DEPLOYMENT.md** - Cómo desplegar en producción


# TROUBLESHOOTING

## "Error: ModuleNotFoundError: No module named 'app'"
→ Asegúrate de estar en el directorio correcto (donde está main.py)
→ El entorno virtual debe estar activado

## "Error: MySQL connection failed"
→ Verifica que MySQL está corriendo
→ Verifica credenciales en .env
→ Verifica que la base de datos existe

## "Error: Alembic error"
→ Asegúrate de que MySQL está corriendo
→ Ejecuta: alembic upgrade head

## "Error: CORS"
→ Asegúrate de que CORS_ORIGINS en .env incluye tu dominio
→ Por defecto permite localhost:3000 y localhost:8000

## "Error: Token inválido"
→ El token expiró después de 30 minutos
→ Haz login nuevamente para obtener uno nuevo


# PROXIMOS PASOS

1. Explora la documentación interactiva en http://localhost:8000/api/docs
2. Prueba crear/actualizar/eliminar recursos
3. Lee ARCHITECTURE.md para entender cómo funciona
4. Revisa EXAMPLES.md para ver ejemplos completos
5. Lee DEPLOYMENT.md cuando quieras desplegar a producción

---

**¡Tu API está lista!** 🚀

Cualquier duda, consulta la documentación o los ejemplos en los archivos MD.
"""
