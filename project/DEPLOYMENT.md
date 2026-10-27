"""
DEPLOYMENT.md - Guía de Deployment en Producción

Esta guía cubre cómo desplegar la API de Restaurant Order Management en producción.
"""

## AMBIENTE DE PRODUCCIÓN - REQUISITOS

- Servidor Linux (Ubuntu 20.04+ recomendado)
- Python 3.12+
- MySQL 8.0+
- Nginx (como reverse proxy)
- SSL/TLS Certificate (Let's Encrypt recomendado)
- Supervisor o systemd (para gestión de procesos)


## PASOS DE DEPLOYMENT


### 1. PREPARACIÓN DEL SERVIDOR

```bash
# Actualizar el sistema
sudo apt update
sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3.12 python3.12-venv python3-pip \
  mysql-server nginx supervisor curl git

# Crear usuario para la aplicación
sudo useradd -m -d /home/restaurant restaurant

# Cambiar a ese usuario
sudo su - restaurant
```


### 2. CLONAR EL PROYECTO

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/restaurant-api.git
cd restaurant-api

# Crear entorno virtual
python3.12 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```


### 3. CONFIGURACIÓN DE LA BASE DE DATOS

```bash
# Crear base de datos
mysql -u root -p << EOF
CREATE DATABASE restaurant_db 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'restaurant_prod'@'localhost' 
  IDENTIFIED BY 'super_secure_password_change_this';

GRANT ALL PRIVILEGES ON restaurant_db.* 
  TO 'restaurant_prod'@'localhost';

FLUSH PRIVILEGES;
EOF
```


### 4. CONFIGURAR VARIABLES DE ENTORNO

```bash
# Crear archivo .env con valores de producción
cat > .env << EOF
# Environment
APP_NAME=Restaurant Order Management System
APP_VERSION=1.0.0
APP_ENV=production
DEBUG=False

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=restaurant_db
DB_USER=restaurant_prod
DB_PASSWORD=super_secure_password_change_this
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20

# JWT (CAMBIAR ESTOS VALORES)
JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_DAYS=30

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
RELOAD=False

# CORS
CORS_ORIGINS=["https://tu-dominio.com"]
EOF

# Restringir permisos del archivo .env
chmod 600 .env
```


### 5. EJECUTAR MIGRACIONES

```bash
# Activar entorno si no está activo
source venv/bin/activate

# Ejecutar migraciones
alembic upgrade head

# Cargar datos iniciales (opcional)
python init_demo_data.py
```


### 6. CONFIGURAR GUNICORN

```bash
# Instalar Gunicorn
pip install gunicorn

# Crear archivo de configuración de Gunicorn
cat > gunicorn.conf.py << EOF
import multiprocessing

# Número de workers (generalmente 2-4 x cores)
workers = multiprocessing.cpu_count() * 2 + 1

# Tipo de worker
worker_class = "uvicorn.workers.UvicornWorker"

# Puerto
bind = "127.0.0.1:8000"

# Timeout
timeout = 120

# Logging
accesslog = "/var/log/restaurant/access.log"
errorlog = "/var/log/restaurant/error.log"
loglevel = "info"

# Process naming
proc_name = "restaurant_api"
EOF
```


### 7. CONFIGURAR SUPERVISOR (O SYSTEMD)

#### Opción A: Con Supervisor

```bash
# Crear archivo de configuración
sudo cat > /etc/supervisor/conf.d/restaurant.conf << EOF
[program:restaurant_api]
directory=/home/restaurant/restaurant-api
command=/home/restaurant/restaurant-api/venv/bin/gunicorn \
    --config gunicorn.conf.py \
    --workers 4 \
    main:app

user=restaurant
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/restaurant/gunicorn.log
environment=PATH="/home/restaurant/restaurant-api/venv/bin",LANG="en_US.UTF-8"
EOF

# Crear directorio de logs
sudo mkdir -p /var/log/restaurant
sudo chown restaurant:restaurant /var/log/restaurant

# Recargar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start restaurant_api
```

#### Opción B: Con Systemd

```bash
# Crear archivo de servicio
sudo cat > /etc/systemd/system/restaurant.service << EOF
[Unit]
Description=Restaurant API
After=network.target mysql.service

[Service]
Type=notify
User=restaurant
WorkingDirectory=/home/restaurant/restaurant-api
ExecStart=/home/restaurant/restaurant-api/venv/bin/gunicorn \
    --config gunicorn.conf.py \
    --workers 4 \
    main:app

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable restaurant.service
sudo systemctl start restaurant.service

# Ver estado
sudo systemctl status restaurant.service
```


### 8. CONFIGURAR NGINX

```bash
# Crear archivo de configuración de Nginx
sudo cat > /etc/nginx/sites-available/restaurant.conf << 'EOF'
upstream restaurant_app {
    server 127.0.0.1:8000;
}

# Redirigir HTTP a HTTPS
server {
    listen 80;
    server_name tu-dominio.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logs
    access_log /var/log/nginx/restaurant_access.log;
    error_log /var/log/nginx/restaurant_error.log;

    # Proxy
    location / {
        proxy_pass http://restaurant_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support (si se implementa en futuro)
    location /ws {
        proxy_pass http://restaurant_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/restaurant.conf \
    /etc/nginx/sites-enabled/

# Deshabilitar sitio por defecto
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```


### 9. CONFIGURAR SSL CON LET'S ENCRYPT

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado
sudo certbot certonly --standalone \
    -d tu-dominio.com \
    -d www.tu-dominio.com \
    --email tu-email@example.com \
    --agree-tos \
    --no-eff-email

# Auto-renovación
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Probar renovación
sudo certbot renew --dry-run
```


### 10. MONITOREO Y LOGGING

```bash
# Verificar estado del servicio
sudo systemctl status restaurant.service

# Ver logs
sudo journalctl -u restaurant.service -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/restaurant_access.log
sudo tail -f /var/log/nginx/restaurant_error.log

# Instalar monitoreo (opcional)
# sudo apt install htop iotop nethogs

# Ver procesos de la API
ps aux | grep gunicorn
```


### 11. BACKUPS AUTOMÁTICOS

```bash
# Crear script de backup
cat > ~/backup_db.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/home/restaurant/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="restaurant_db"
DB_USER="restaurant_prod"
BACKUP_FILE="$BACKUP_DIR/restaurant_backup_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

mysqldump -u $DB_USER -p -p $DB_NAME | gzip > $BACKUP_FILE

# Mantener solo los últimos 7 días
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completado: $BACKUP_FILE"
EOF

chmod +x ~/backup_db.sh

# Agregar a crontab (ejecutar diariamente a las 2 AM)
crontab -e
# Agregar línea:
# 0 2 * * * /home/restaurant/backup_db.sh
```


### 12. MONITOREO CON NEWRELIC (Opcional)

```bash
# Instalar agente
pip install newrelic

# Agregar a gunicorn_conf.py
# import newrelic.agent
# newrelic.agent.initialize('/path/to/newrelic.ini')
```


## CHECKLIST DE SEGURIDAD

- [ ] JWT_SECRET cambió a un valor seguro aleatorio
- [ ] Base de datos tiene usuario y contraseña seguros
- [ ] SSL/TLS está configurado
- [ ] CORS_ORIGINS está restringido a dominios autorizados
- [ ] Firewall está configurado para permitir solo puertos necesarios (22, 80, 443)
- [ ] SSH key-based authentication está habilitado
- [ ] Backups automáticos están configurados
- [ ] Monitoreo y alertas están configuradas
- [ ] Debug está deshabilitado (DEBUG=False)
- [ ] Logs están siendo guardados y rotados


## MONITOREO DE DISPONIBILIDAD

```bash
# Health check simple
curl -X GET https://tu-dominio.com/health

# Monitoreo con cron
cat > ~/check_health.sh << 'EOF'
#!/bin/bash
if ! curl -s https://tu-dominio.com/health > /dev/null; then
    sudo systemctl restart restaurant.service
fi
EOF

chmod +x ~/check_health.sh

# Ejecutar cada 5 minutos
# */5 * * * * /home/restaurant/check_health.sh
```


## ESCALADO

Para manejar más tráfico:

1. **Aumentar workers de Gunicorn**: Cambiar `workers` en gunicorn.conf.py
2. **Database connection pooling**: Aumentar DB_POOL_SIZE en .env
3. **Load balancing**: Usar Nginx como load balancer con múltiples instancias
4. **Redis caching**: Agregar caché para consultas frecuentes
5. **CDN**: Usar CDN para assets estáticos


## TROUBLESHOOTING

### Servidor no inicia
```bash
sudo systemctl status restaurant.service
sudo journalctl -u restaurant.service -n 50
```

### Error de conexión a BD
```bash
# Verificar conexión MySQL
mysql -h localhost -u restaurant_prod -p restaurant_db

# Ver logs del servicio
sudo systemctl restart restaurant.service
sudo tail -f /var/log/syslog
```

### Nginx no proxying correctamente
```bash
# Verificar configuración
sudo nginx -t

# Recargar
sudo systemctl reload nginx

# Ver error log
sudo tail -f /var/log/nginx/error.log
```


## ACTUALIZAR CÓDIGO

```bash
# Descargar cambios
cd /home/restaurant/restaurant-api
git pull origin main

# Instalar dependencias nuevas (si hay)
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar migraciones (si hay)
alembic upgrade head

# Reiniciar servicio
sudo systemctl restart restaurant.service

# Verificar
curl https://tu-dominio.com/health
```


## CONTACTO Y SOPORTE

Para issues de deployment, consulta:
- Logs de systemd: `sudo journalctl -u restaurant.service`
- Logs de Nginx: `/var/log/nginx/`
- Health check: `curl https://tu-dominio.com/health`

"""
