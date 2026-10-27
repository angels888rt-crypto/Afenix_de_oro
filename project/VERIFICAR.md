"""
VERIFICAR.md - Checklist de Verificación del Proyecto

Use este archivo para verificar que todo está correctamente instalado.
"""

# ✅ CHECKLIST DE VERIFICACIÓN

## 1. ARCHIVOS DEL PROYECTO

Verifica que existan todos los archivos principales:

```
✓ main.py - Punto de entrada de la aplicación
✓ requirements.txt - Dependencias Python
✓ .env.example - Template de variables de entorno
✓ docker-compose.yml - Orquestación de contenedores
✓ init_demo_data.py - Script para cargar datos
✓ quick_setup.py - Setup automatizado
✓ test_api.py - Tests básicos
```

Comandos para verificar:
```bash
dir main.py
dir requirements.txt
dir .env.example
```

## 2. ESTRUCTURA DE CARPETAS

```
✓ app/domain/ - Lógica de negocio
  ✓ entities/__init__.py
  ✓ repositories/__init__.py
  ✓ services/__init__.py

✓ app/application/ - Casos de uso
  ✓ dto/__init__.py
  ✓ use_cases/
    ✓ user_use_cases.py
    ✓ table_use_cases.py
    ✓ dish_use_cases.py
    ✓ order_use_cases.py
    ✓ notification_use_cases.py

✓ app/infrastructure/ - Implementaciones
  ✓ config/settings.py
  ✓ database/
    ✓ models/database_models.py
    ✓ repositories/
      ✓ base_repositories.py
      ✓ order_repositories.py
    ✓ session.py
  ✓ security/jwt_handler.py

✓ app/presentation/ - API REST
  ✓ api/
    ✓ routers/
      ✓ user_router.py
      ✓ table_router.py
      ✓ dish_router.py
      ✓ order_router.py
      ✓ notification_router.py
    ✓ dependencies/auth_dependencies.py
    ✓ middleware/exception_handlers.py

✓ app/shared/ - Código transversal
  ✓ exceptions/custom_exceptions.py
  ✓ responses/response_schema.py
  ✓ constants/enums.py

✓ alembic/ - Migraciones
  ✓ versions/
    ✓ 001_initial_schema.py
  ✓ env.py
  ✓ script.py.mako
  ✓ alembic.ini
```

Comando para verificar:
```bash
tree /F
```

## 3. DOCUMENTACIÓN

```
✓ README.md - Documentación técnica
✓ QUICK_START.md - Inicio rápido
✓ INSTALL.md - Instalación detallada
✓ ARCHITECTURE.md - Explicación de arquitectura
✓ EXAMPLES.md - Ejemplos de API
✓ DEPLOYMENT.md - Guía de deployment
✓ PROJECT_SUMMARY.md - Resumen del proyecto
✓ INDEX.md - Índice de documentación
✓ VERIFICAR.md - Este archivo
```

## 4. VERIFICACIÓN DE INSTALACIÓN

### Requisitos Previos

```bash
# Verificar Python
python --version
# Debe ser 3.12 o superior

# Verificar MySQL
mysql --version
# Debe ser 8.0 o superior

# Verificar que MySQL está corriendo
mysql -u root -p -e "SELECT 1"
# Debe conectar exitosamente
```

### Instalación de Dependencias

```bash
# Activar entorno virtual
venv\Scripts\activate

# Verificar que pip está actualizado
pip --version

# Instalar dependencias
pip install -r requirements.txt

# Verificar que se instaló FastAPI
pip show fastapi
# Debe ser versión 0.104.1

# Verificar que se instaló SQLAlchemy
pip show sqlalchemy
# Debe ser versión 2.0.23

# Verificar que se instaló Pydantic
pip show pydantic
# Debe ser versión 2.5.0
```

### Configuración de Base de Datos

```bash
# Verificar que .env existe
dir .env

# Verificar credenciales en .env
type .env | findstr DB_HOST
type .env | findstr DB_USER

# Verificar conexión a MySQL
mysql -h localhost -u restaurant_user -p restaurant_db -e "SELECT 1"

# Verificar estructura de BD después de migraciones
mysql -u restaurant_user -p restaurant_db -e "SHOW TABLES;"
# Debe mostrar: users, tables, dishes, orders, order_items, notifications
```

### Migraciones

```bash
# Ejecutar migraciones
alembic upgrade head

# Verificar que se crearon las tablas
mysql -u restaurant_user -p restaurant_db -e "SHOW TABLES;"

# Ver esquema de usuarios
mysql -u restaurant_user -p restaurant_db -e "DESCRIBE users;"
```

### Datos de Demo (Opcional)

```bash
# Cargar datos de demostración
python init_demo_data.py

# Verificar que se cargaron usuarios
mysql -u restaurant_user -p restaurant_db -e "SELECT COUNT(*) as total_users FROM users;"
# Debe retornar 5 (admin + 2 cocineros + 2 camareros)

# Verificar que se cargaron mesas
mysql -u restaurant_user -p restaurant_db -e "SELECT COUNT(*) as total_tables FROM tables;"
# Debe retornar 10

# Verificar que se cargaron platos
mysql -u restaurant_user -p restaurant_db -e "SELECT COUNT(*) as total_dishes FROM dishes;"
# Debe retornar 12
```

## 5. VERIFICACIÓN DE LA API

### Iniciar Servidor

```bash
# Activar entorno virtual
venv\Scripts\activate

# Iniciar servidor
uvicorn main:app --reload

# Debe mostrar:
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Health Check

```bash
# En otra terminal
curl http://localhost:8000/health

# Debe retornar:
# {"success":true,"message":"Service is healthy"}
```

### Documentación Interactiva

```
Abre en navegador:
- http://localhost:8000/api/docs (Swagger UI)
- http://localhost:8000/api/redoc (ReDoc)
- http://localhost:8000/api/openapi.json (OpenAPI schema)
```

### Probar Endpoints

```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test",
    "email": "test@test.com",
    "password": "test123",
    "full_name": "Test",
    "role": "CAMARERO"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test",
    "password": "test123"
  }'

# Obtener información del usuario actual (necesita TOKEN)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 6. VERIFICACIÓN DE CÓDIGO

### Imports

```bash
# Verificar que no hay errores de import
python -c "from app.infrastructure.config import settings; print('Settings OK')"
python -c "from app.domain.entities import User; print('Entities OK')"
python -c "from app.application.use_cases import *; print('Use Cases OK')"
python -c "from app.infrastructure.database.session import get_session; print('Database OK')"
```

### Tipo Hints

```bash
# Verificar que los type hints son correctos (si tienes mypy)
mypy app --ignore-missing-imports
```

### Linting

```bash
# Verificar sintaxis con pylint (opcional)
pip install pylint
pylint app
```

## 7. VERIFICACIÓN DE SEGURIDAD

```bash
# Verificar que JWT_SECRET en .env no es la default
grep "JWT_SECRET" .env
# Debe ser diferente de "your-super-secret-key"

# Verificar que DEBUG está False en producción
grep "DEBUG" .env
# Debe ser False

# Verificar que .env no está en git
grep ".env" .gitignore
# Debe contener ".env"
```

## 8. LOGS Y ERRORES

### Ver Logs de la API

```bash
# Logs de Uvicorn se muestran en la terminal

# Ver logs detallados
uvicorn main:app --reload --log-level debug
```

### Ver Logs de MySQL

```bash
# En Ubuntu/Linux
sudo tail -f /var/log/mysql/error.log

# En Windows (si usas Docker)
docker logs restaurant_mysql
```

## 9. PERFORMANCE BÁSICO

```bash
# Verificar tiempo de respuesta
time curl http://localhost:8000/health

# Debe ser < 100ms para health check
```

## 10. CHECKLIST FINAL

Marca cada ítem completado:

```
Instalación
☐ Python 3.12+ instalado
☐ MySQL 8.0+ corriendo
☐ Entorno virtual creado y activado
☐ Dependencias instaladas (pip install -r requirements.txt)
☐ .env configurado con credenciales correctas

Base de Datos
☐ Base de datos 'restaurant_db' creada
☐ Usuario 'restaurant_user' creado
☐ Migraciones ejecutadas (alembic upgrade head)
☐ 6 tablas creadas (users, tables, dishes, orders, order_items, notifications)
☐ Datos de demo cargados (python init_demo_data.py)

API
☐ Servidor inicia sin errores (uvicorn main:app --reload)
☐ Health check responde (curl http://localhost:8000/health)
☐ Documentación accesible (http://localhost:8000/api/docs)
☐ Usuario registrado exitosamente
☐ Login funciona y retorna token JWT
☐ Endpoints de mesa funcionan
☐ Endpoints de platos funcionan
☐ Creación de pedidos funciona
☐ Notificaciones se generan automáticamente

Código
☐ No hay errores de import
☐ Type hints están presentes
☐ Excepciones manejan correctamente
☐ Respuestas siguen formato estándar

Seguridad
☐ JWT_SECRET es único (no el default)
☐ DEBUG es False en producción
☐ .env está en .gitignore
☐ Credenciales MySQL son seguras

Documentación
☐ Todos los archivos README/MD presentes
☐ EXAMPLES.md tiene ejemplos funcionales
☐ ARCHITECTURE.md explica el proyecto
☐ DEPLOYMENT.md cubre producción

Testing
☐ test_api.py puede ejecutarse
☐ Endpoints responden correctamente
☐ Datos se persisten en BD
```

## 11. COMANDOS DE DIAGNÓSTICO

Si algo falla, ejecuta estos comandos:

```bash
# Ver configuración de la aplicación
python -c "from app.infrastructure.config import settings; print(settings.database_url)"

# Ver versiones instaladas
pip freeze | findstr -E "fastapi|sqlalchemy|pydantic|alembic|mysql"

# Verificar conexión a BD
python -c "
import asyncio
from app.infrastructure.database.session import AsyncSessionLocal
async def test():
    async with AsyncSessionLocal() as session:
        result = await session.execute('SELECT 1')
        print('BD conectada:', result.scalar())
asyncio.run(test())
"

# Ver entorno cargado
python -c "from app.infrastructure.config import settings; print(f'ENV: {settings.APP_ENV}, DEBUG: {settings.DEBUG}')"
```

## 12. PRÓXIMOS PASOS DESPUÉS DE VERIFICAR

Una vez que todo esté verificado:

✓ Leer ARCHITECTURE.md para entender la estructura
✓ Revisar EXAMPLES.md para ver todos los endpoints
✓ Explorar código en app/ para entender implementación
✓ Leer DEPLOYMENT.md para prepararse para producción
✓ Personalizar según necesidades específicas

---

## CONCLUSIÓN

Si todos los checks pasaron: ✅ **Tu API está lista para usar!**

Si hay problemas:
1. Revisa INSTALL.md sección Troubleshooting
2. Revisa logs de errores
3. Verifica que MySQL está corriendo
4. Verifica que .env tiene credenciales correctas

**¡Disfruta usando la API! 🚀**
"""
