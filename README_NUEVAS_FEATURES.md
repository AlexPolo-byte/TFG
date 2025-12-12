# 📝 Sección para Añadir al README.md

## 🆕 Nuevas Funcionalidades

### 🤖 Comandos del Bot

El bot ahora soporta los siguientes comandos:

| Comando | Descripción |
|---------|-------------|
| `/start` | Presentación del bot y capacidades |
| `/help` | Lista de comandos disponibles |
| `/stats` | Estadísticas del sistema y usuario |

**Ejemplo de uso:**
```
Usuario: /stats
Bot: 📊 ESTADÍSTICAS:

💬 Total mensajes: 1,234
👤 Tus mensajes: 42
🤖 Sistema operativo correctamente
```

---

### ⚡ Sistema de Caché (Redis)

Las respuestas de la IA se cachean durante 1 hora para:
- ✅ Reducir llamadas a la API de Google (ahorro de costos)
- ✅ Respuestas instantáneas para preguntas repetidas
- ✅ Menor carga en el sistema

**Configuración:**
- Redis usa máximo 100MB de RAM
- Política: `allkeys-lru` (elimina claves menos usadas)
- TTL: 3600 segundos (1 hora)

---

### 🚨 Notificaciones de Errores

Los errores críticos se envían automáticamente al administrador vía Telegram.

**Configuración:**
```bash
# En .env
ADMIN_CHAT_ID=123456789  # Tu chat ID de Telegram
```

**Obtener tu Chat ID:**
1. Abre Telegram y busca `@userinfobot`
2. Envía `/start`
3. Copia el número que te muestra

---

### 💾 Backups Automáticos

Script de backup incluido que guarda MongoDB en formato JSON comprimido.

**Uso manual:**
```bash
docker exec backend_telegram python backup_db.py
```

**Configurar backup automático (cron):**
```bash
# En la Raspberry Pi, editar crontab
crontab -e

# Añadir línea (backup diario a las 2 AM)
0 2 * * * docker exec backend_telegram python backup_db.py
```

Los backups se guardan en `/app/backups/` y se mantienen los últimos 7.

---

### 🏥 Health Checks

Docker reinicia automáticamente servicios que fallen.

**Ver estado:**
```bash
docker ps
# Columna STATUS mostrará "healthy" o "unhealthy"
```

**Endpoints:**
- Backend: `http://localhost:5000/health`
- Redis: `redis-cli ping`

---

### 📊 Alertas de Grafana

Configuración incluida para alertas automáticas.

**Alertas configuradas:**
- 🔴 CPU > 80% durante 2 minutos
- 🔴 Memoria > 400MB
- 🔴 Más de 10 errores/minuto
- 🔴 Servicio caído
- 🟡 Procesamiento lento (>10s)

**Configurar:**
1. Ir a Grafana → Alerting → Alert rules
2. Importar `grafana-alerts.yml`
3. Configurar canal de notificación (Telegram/Email)

---

### 🧪 Tests Automatizados

Suite de tests incluida para validar funcionalidad.

**Ejecutar tests:**
```bash
# Todos los tests
pytest tests/ -v

# Solo tests de worker
pytest tests/test_worker.py -v

# Solo tests de app
pytest tests/test_app.py -v
```

**Cobertura:**
- ✅ Detección de sentimiento
- ✅ Sistema de caché
- ✅ Comandos del bot
- ✅ Validación de configuración
- ✅ Endpoints y timeouts

---

### 🔐 Seguridad Mejorada

Las credenciales de admin ahora se configuran vía variables de entorno.

**En .env:**
```bash
ADMIN_USER=tu_usuario_personalizado
ADMIN_PASS=tu_contraseña_segura
SECRET_KEY=clave_secreta_aleatoria
```

**Generar clave secreta segura:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📈 Métricas y Monitorización

### Prometheus Metrics

Nuevas métricas disponibles:
- `worker_messages_total{type="text|photo|error"}` - Mensajes procesados por tipo
- `worker_processing_seconds` - Tiempo de procesamiento
- `flask_http_requests_total` - Requests HTTP
- `rabbitmq_publish_errors_total` - Errores de RabbitMQ

**Acceder:**
- Prometheus: `http://<raspberry-ip>:9090`
- Grafana: `http://<raspberry-ip>:3000`

---

## 🔧 Troubleshooting Adicional

### Redis no conecta

```bash
# Verificar que Redis está corriendo
docker logs redis

# Probar conexión manual
docker exec -it redis redis-cli ping
# Debe responder: PONG
```

### Tests fallan

```bash
# Instalar dependencias de tests
pip install pytest pytest-mock

# Ejecutar con más detalle
pytest tests/ -vv --tb=long
```

### Backups no se crean

```bash
# Verificar permisos
docker exec backend_telegram ls -la /app/backups/

# Ejecutar manualmente para ver errores
docker exec backend_telegram python backup_db.py
```

### Notificaciones no llegan

```bash
# Verificar ADMIN_CHAT_ID
docker exec worker printenv | grep ADMIN_CHAT_ID

# Forzar error para probar
docker exec worker python -c "from worker import notify_admin_error; notify_admin_error('Test')"
```
