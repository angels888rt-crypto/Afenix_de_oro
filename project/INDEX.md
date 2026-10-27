"""
INDEX.md - Índice Completo de Documentación

Navega el proyecto usando esta guía de referencias cruzadas.
"""

# ÍNDICE DE DOCUMENTACIÓN

## Para Empezar Rápido ⚡

1. **QUICK_START.md** - Leer primero (5 minutos)
   - Requisitos mínimos
   - Pasos de instalación simplificados
   - Primeros usos de la API
   - Troubleshooting básico

2. **INSTALL.md** - Instalación paso a paso
   - Requisitos previos detallados
   - Instalación completa
   - Configuración de MySQL
   - Inicialización de datos
   - Solución de problemas

## Para Entender la Arquitectura 🏗️

3. **ARCHITECTURE.md** - Explicación de la arquitectura
   - Descripción de las 5 capas
   - Patrones implementados
   - Flujo de datos
   - Cómo agregar nuevas features
   - Convenciones de código

4. **PROJECT_SUMMARY.md** - Resumen del proyecto completo
   - Información general
   - Problema solucionado
   - Tecnologías utilizadas
   - Base de datos detallada
   - Flujos de negocio
   - Estadísticas del proyecto

## Para Usar la API 📡

5. **EXAMPLES.md** - Ejemplos de todos los endpoints
   - 35+ ejemplos de curl/HTTP
   - Autenticación
   - CRUD de recursos
   - Casos de uso completos
   - Códigos de estado HTTP

6. **README.md** - Documentación técnica completa
   - Descripción del proyecto
   - Arquitectura (breve)
   - Endpoints (listado completo)
   - Respuestas y errores
   - Business logic
   - Setup y testing

## Para Desplegar en Producción 🚀

7. **DEPLOYMENT.md** - Guía de deployment paso a paso
   - Requisitos de servidor
   - Preparación del ambiente
   - Configuración de base de datos
   - Gunicorn y Supervisor/Systemd
   - Nginx como reverse proxy
   - SSL/TLS con Let's Encrypt
   - Monitoreo y logs
   - Backups automáticos
   - Troubleshooting avanzado

## Estructura de Archivos

```
project/
├── Documentación
│   ├── INDEX.md ........................ Índice (tú estás aquí)
│   ├── QUICK_START.md ................. Inicio rápido (⭐ Comienza aquí)
│   ├── INSTALL.md ..................... Instalación detallada
│   ├── ARCHITECTURE.md ................ Estructura de la arquitectura
│   ├── EXAMPLES.md .................... Ejemplos de API
│   ├── DEPLOYMENT.md .................. Guía de deployment
│   ├── PROJECT_SUMMARY.md ............. Resumen completo del proyecto
│   └── README.md ...................... Documentación técnica principal
│
├── Configuración
│   ├── .env.example ................... Variables de entorno (plantilla)
│   ├── .env ........................... Tu configuración local
│   ├── .gitignore ..................... Git exclusions
│   ├── requirements.txt ............... Dependencias Python
│   └── docker-compose.yml ............. Orquestación de contenedores
│
├── Código Fuente
│   ├── app/ ........................... Aplicación principal
│   │   ├── domain/ .................... Lógica de negocio pura
│   │   ├── application/ ............... Casos de uso y DTOs
│   │   ├── infrastructure/ ............ Base de datos y seguridad
│   │   ├── presentation/ .............. Routers y endpoints
│   │   └── shared/ .................... Excepciones y respuestas
│   │
│   └── alembic/ ....................... Migraciones de base de datos
│       ├── versions/ .................. Cambios de esquema versionados
│       ├── env.py ..................... Configuración de Alembic
│       ├── script.py.mako ............. Template para migraciones
│       └── alembic.ini ................ Archivo de configuración
│
├── Scripts de Utilidad
│   ├── main.py ........................ Punto de entrada de la aplicación
│   ├── init_demo_data.py .............. Cargar datos de demostración
│   ├── quick_setup.py ................. Setup automatizado
│   └── test_api.py .................... Tests básicos
│
└── Información
    └── VERIFICAR.md (este archivo) ... Checklist de instalación
```


## FLUJOS DE LECTURA RECOMENDADOS

### 👨‍💻 Si Eres Desarrollador

1. Leer QUICK_START.md (5 min)
2. Ejecutar instalación
3. Leer ARCHITECTURE.md (20 min)
4. Probar endpoints en http://localhost:8000/api/docs
5. Leer EXAMPLES.md para entender patterns (15 min)
6. Explorar código en app/
7. Leer DEPLOYMENT.md cuando necesites desplegar

### 🏗️ Si Eres Arquitecto/Tech Lead

1. Leer PROJECT_SUMMARY.md (15 min)
2. Leer ARCHITECTURE.md detalladamente (30 min)
3. Revisar database schema en README.md
4. Revisar endpoints en EXAMPLES.md
5. Explorar código en app/domain/ para ver entidades
6. Revisar DEPLOYMENT.md para infraestructura

### 🚀 Si Solo Quieres Ejecutar

1. Leer QUICK_START.md
2. Ejecutar los pasos
3. Listo, tu API está corriendo
4. Acceder a http://localhost:8000/api/docs

### 📊 Si Necesitas Desplegar en Producción

1. Leer PROJECT_SUMMARY.md (visión general)
2. Leer DEPLOYMENT.md completo
3. Leer ARCHITECTURE.md para entender estructura
4. Preparar servidor siguiendo DEPLOYMENT.md
5. Configurar MySQL, Gunicorn, Nginx, SSL
6. Usar EXAMPLES.md para testing
7. Monitorear con tools sugeridas

### 🐛 Si Hay Problemas

1. Consulta sección "Troubleshooting" en QUICK_START.md
2. Consulta sección "Solución de Problemas" en INSTALL.md
3. Si es producción, ver DEPLOYMENT.md troubleshooting
4. Revisa logs: journalctl, supervisorctl, nginx error.log

## BÚSQUEDA RÁPIDA

**¿Cómo...?**

| Pregunta | Archivo | Sección |
|----------|---------|---------|
| Instalar proyecto | INSTALL.md | Pasos 1-8 |
| Usar la API | EXAMPLES.md | Cualquier sección |
| Entender arquitectura | ARCHITECTURE.md | Capas de la arquitectura |
| Desplegar | DEPLOYMENT.md | Desde el inicio |
| Registrar usuario | EXAMPLES.md | Autenticación #1 |
| Ver pedidos | EXAMPLES.md | Gestión de pedidos #26 |
| Agregar platos | EXAMPLES.md | Gestión de platos #16 |
| Crear mesa | EXAMPLES.md | Gestión de mesas #9 |
| Configurar JWT_SECRET | .env.example | JWT section |
| Ejecutar tests | test_api.py | Dentro del archivo |
| Cargar datos demo | init_demo_data.py | Ejecutar como script |

## DOCUMENTOS POR TAMAÑO Y TIEMPO DE LECTURA

| Documento | Tamaño | Tiempo | Para |
|-----------|--------|--------|------|
| QUICK_START.md | Corto | 5 min | Inicio rápido |
| EXAMPLES.md | Largo | 20 min | API testing |
| README.md | Largo | 30 min | Referencia técnica |
| ARCHITECTURE.md | Muy largo | 45 min | Comprensión profunda |
| DEPLOYMENT.md | Muy largo | 60 min | Production setup |
| PROJECT_SUMMARY.md | Muy largo | 45 min | Resumen completo |
| INSTALL.md | Medio | 25 min | Instalación |

## APIS Y ENDPOINTS

Para lista completa de endpoints, ver:
- **EXAMPLES.md** - Ejemplos ejecutables
- **README.md** - Documentación de endpoints
- **http://localhost:8000/api/docs** - Swagger interactivo (requiere servidor corriendo)

Grupos de endpoints:
- Usuarios: 8 endpoints
- Mesas: 7 endpoints
- Platos: 8 endpoints
- Pedidos: 8 endpoints
- Notificaciones: 4 endpoints
- Health: 2 endpoints

**Total: 40+ endpoints**

## STACK TECNOLÓGICO

Para información detallada sobre herramientas:

**Framework y ORM:**
- FastAPI - EXAMPLES.md, ARCHITECTURE.md
- SQLAlchemy 2.0 - README.md Database Schema
- Pydantic v2 - ARCHITECTURE.md Application Layer

**Base de Datos:**
- MySQL 8.0+ - INSTALL.md Paso 1, DEPLOYMENT.md
- Alembic - ARCHITECTURE.md Infrastructure Layer

**Seguridad:**
- JWT - ARCHITECTURE.md Domain Services
- Bcrypt - ARCHITECTURE.md Security Layer

**Deployment:**
- Gunicorn - DEPLOYMENT.md Paso 6
- Nginx - DEPLOYMENT.md Paso 8
- Supervisor/Systemd - DEPLOYMENT.md Pasos 7

## CONVENCIONES Y PATRONES

Para entender cómo se hace todo:

| Concepto | Documento | Sección |
|----------|-----------|---------|
| Casos de uso | ARCHITECTURE.md | Application Layer |
| Repositorio | ARCHITECTURE.md | Repository Pattern |
| Entidades | ARCHITECTURE.md | Domain Layer |
| DTOs | ARCHITECTURE.md | Application Layer |
| RBAC | ARCHITECTURE.md | RBAC Pattern |
| Excepciones | ARCHITECTURE.md | Shared Layer |

## TROUBLESHOOTING RÁPIDO

**Problema → Solución**

| Problema | Referencia |
|----------|-----------|
| ModuleNotFoundError: app | QUICK_START.md Troubleshooting |
| MySQL connection failed | QUICK_START.md o INSTALL.md Troubleshooting |
| CORS error | QUICK_START.md Troubleshooting |
| Token inválido | QUICK_START.md Troubleshooting |
| Alembic error | QUICK_START.md Troubleshooting |
| Nginx no proxying | DEPLOYMENT.md Troubleshooting |
| Supervisor issue | DEPLOYMENT.md Paso 7 |

## CÓMO CONTRIBUIR / MODIFICAR

Para agregar nuevas features:

1. Leer ARCHITECTURE.md sección "Adición de una Nueva Característica"
2. Seguir pasos: Domain → Application → Infrastructure → Presentation
3. Crear migraciones Alembic en alembic/versions/
4. Actualizar documentación
5. Agregar tests
6. Hacer commit y push

## PREGUNTAS FRECUENTES (FAQ)

**P: ¿Por dónde empiezo?**
R: QUICK_START.md → 5 minutos para tener API corriendo

**P: ¿Cómo agrego un nuevo endpoint?**
R: ARCHITECTURE.md → Sección "Adición de una Nueva Característica"

**P: ¿Cómo despliego en producción?**
R: DEPLOYMENT.md → Paso a paso

**P: ¿Dónde hay ejemplos de API?**
R: EXAMPLES.md → 35+ ejemplos con curl/HTTP

**P: ¿Cómo entiendo la arquitectura?**
R: ARCHITECTURE.md → Explicación detallada de 5 capas

**P: ¿Qué cambio en .env para producción?**
R: DEPLOYMENT.md Paso 4 → Valores de producción

---

## REFERENCIA RÁPIDA DE COMANDOS

```bash
# Setup
python -m venv venv
venv\Scripts\activate  # Windows o source venv/bin/activate
pip install -r requirements.txt

# Migraciones
alembic upgrade head
python init_demo_data.py

# Ejecutar
uvicorn main:app --reload

# Tests
pytest test_api.py -v

# Docs
http://localhost:8000/api/docs
```

---

**¡Selecciona el documento que necesitas arriba y comienza!** 📖
