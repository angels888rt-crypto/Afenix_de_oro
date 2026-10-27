#!/usr/bin/env python3
"""
Quick setup script for the Restaurant Order Management API

Run this script to quickly set up the environment:
    python quick_setup.py
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_success(text):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text):
    """Print error message."""
    print(f"✗ {text}")


def print_info(text):
    """Print info message."""
    print(f"ℹ {text}")


def run_command(command, description):
    """Run a command and handle errors."""
    print_info(description)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        print_success(f"{description} - Completado")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"{description} - Error: {e}")
        if e.stderr:
            print(f"  {e.stderr}")
        return False


def main():
    """Main setup function."""
    print_header("Restaurant Order Management API - Setup")
    
    # Check Python version
    if sys.version_info < (3, 12):
        print_error("Python 3.12+ es requerido")
        sys.exit(1)
    
    print_success(f"Python {sys.version.split()[0]} detectado")
    
    # Check if .env exists
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print_info("Copiando .env.example a .env")
            subprocess.run("copy .env.example .env", shell=True)
            print_success("Archivo .env creado")
            print_info("⚠  Edita .env con tus credenciales de MySQL")
        else:
            print_error(".env.example no encontrado")
    else:
        print_success("Archivo .env ya existe")
    
    # Create virtual environment
    if not Path("venv").exists():
        print_header("Creando Entorno Virtual")
        if run_command("python -m venv venv", "Creando venv"):
            if sys.platform == "win32":
                activate_cmd = "venv\\Scripts\\activate.bat"
            else:
                activate_cmd = "source venv/bin/activate"
            print_info(f"Para activar el entorno, ejecuta: {activate_cmd}")
    else:
        print_success("Entorno virtual ya existe")
    
    # Install dependencies
    print_header("Instalando Dependencias")
    
    pip_cmd = "pip" if sys.platform == "win32" else "pip3"
    if run_command(f"{pip_cmd} install --upgrade pip", "Actualizando pip"):
        if run_command(f"{pip_cmd} install -r requirements.txt", "Instalando dependencias"):
            print_success("Todas las dependencias instaladas")
    
    # Show next steps
    print_header("Próximos Pasos")
    
    print("""
1. CONFIGURAR BASE DE DATOS MYSQL:

   En MySQL, ejecuta:
   
   CREATE DATABASE restaurant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'restaurant_user'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL PRIVILEGES ON restaurant_db.* TO 'restaurant_user'@'localhost';
   FLUSH PRIVILEGES;

   O usa Docker Compose:
   docker-compose up -d

2. EDITAR ARCHIVO .env:

   Actualiza los valores de conexión a la base de datos:
   - DB_HOST
   - DB_PORT
   - DB_NAME
   - DB_USER
   - DB_PASSWORD
   - JWT_SECRET (genera una clave segura para producción)

3. EJECUTAR MIGRACIONES:

   alembic upgrade head

4. INICIALIZAR DATOS DE DEMOSTRACIÓN (Opcional):

   python init_demo_data.py

5. INICIAR EL SERVIDOR:

   uvicorn main:app --reload

6. ACCEDER A LA API:

   - API: http://localhost:8000
   - Documentación Swagger: http://localhost:8000/api/docs
   - Documentación ReDoc: http://localhost:8000/api/redoc

7. PROBAR LA API:

   Consulta EXAMPLES.md para ejemplos de cómo usar cada endpoint.
    """)
    
    print_header("Ayuda Adicional")
    
    print("""
Documentación disponible:
- INSTALL.md - Instrucciones completas de instalación
- ARCHITECTURE.md - Explicación de la arquitectura
- EXAMPLES.md - Ejemplos de todos los endpoints
- README.md - Documentación completa del proyecto

Para más ayuda, consulta los archivos anteriores o la documentación interactiva
en http://localhost:8000/api/docs una vez que el servidor esté corriendo.
    """)
    
    print_success("Setup completado!")


if __name__ == "__main__":
    main()
