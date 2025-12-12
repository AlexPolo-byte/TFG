# 🤖 TFG - Bot de Telegram con IA (Raspberry Pi)

Sistema de bot de Telegram con inteligencia artificial (Google Gemini), monitorización completa y túnel Cloudflare para acceso público desde Raspberry Pi.

## 📋 Requisitos Previos

### Hardware
- Raspberry Pi 3/4/5 (recomendado 2GB+ RAM)
- Conexión a Internet

### Software
- Raspberry Pi OS (Bullseye o superior)
- Docker y Docker Compose instalados
- Git

### Instalación de Docker en Raspberry Pi

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Añadir tu usuario al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER

# IMPORTANTE: Cierra sesión y vuelve a entrar para aplicar cambios
# O ejecuta: newgrp docker

# Instalar Docker Compose
sudo apt-get install docker-compose-plugin

# Verificar instalación
docker --version
docker compose version
```

---

## 🔧 Configuración

### 1. Clonar el Repositorio

```bash
cd ~
git clone <tu-repositorio>
cd TFG
```

### 2. Crear Archivo `.env`

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```bash
# Token del Bot de Telegram
# Obtenerlo de @BotFather en Telegram
TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# API Key de Google Gemini
# Obtenerla en: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# MongoDB Atlas (Gratis)
# Crear cluster en: https://www.mongodb.com/cloud/atlas/register
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/tfg?retryWrites=true&w=majority

# RabbitMQ CloudAMQP (Gratis)
# Crear instancia en: https://www.cloudamqp.com/
RABBITMQ_URI=amqps://usuario:password@servidor.cloudamqp.com/vhost
RABBITMQ_QUEUE=telegram_queue

# Puertos de Monitorización (Opcional)
FLASK_EXPORTER_PORT=9091
WORKER_EXPORTER_PORT=9092
```

### 3. Obtener Credenciales

#### 🤖 Telegram Bot Token
1. Abre Telegram y busca `@BotFather`
2. Envía `/newbot`
3. Sigue las instrucciones y copia el token

#### 🧠 Google Gemini API Key
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una API Key
3. Cópiala al `.env`

#### 🗄️ MongoDB Atlas (Base de Datos)
1. Crea cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Crea un cluster gratuito (M0)
3. En "Database Access" → Crea un usuario
4. En "Network Access" → Añade `0.0.0.0/0` (permitir todas las IPs)
5. En "Clusters" → Click "Connect" → "Connect your application"
6. Copia la URI y reemplaza `<password>` con tu contraseña

#### 🐰 RabbitMQ CloudAMQP (Cola de Mensajes)
1. Crea cuenta en [CloudAMQP](https://www.cloudamqp.com/)
2. Crea una instancia gratuita "Little Lemur"
3. Copia la "AMQP URL" al `.env`

---

## 🚀 Despliegue

### Iniciar el Sistema

```bash
# Dar permisos de ejecución al script
chmod +x start.sh

# Lanzar todo el sistema
./start.sh
```

El script automáticamente:
1. ✅ Levanta todos los contenedores Docker
2. ✅ Crea un túnel Cloudflare público
3. ✅ Configura el webhook de Telegram
4. ✅ Muestra la URL pública de acceso

### Salida Esperada

```
🚀 Iniciando Arquitectura del TFG (Modo Limpieza)...
🧹 Borrando túnel anterior para limpiar logs...
⏳ Esperando 15 segundos a que Cloudflare genere la URL...
✅ Túnel ACTIVO en: https://xxxxx.trycloudflare.com

🎉 ¡ÉXITO! Sistema 100% Operativo.
🔐 Admin Dashboard: https://xxxxx.trycloudflare.com (Requiere Login)
💬 Chat Público:    https://xxxxx.trycloudflare.com/public/terminal
```

---

## 🎛️ Acceso al Sistema

### Panel de Administración
- **URL**: La que muestra `start.sh`
- **Usuario**: `admin`
- **Contraseña**: `tfg2025`

### Monitorización (Grafana)
- **URL**: `http://<IP-raspberry>:3000`
- **Acceso**: Anónimo (configurado para desarrollo)

### Prometheus
- **URL**: `http://<IP-raspberry>:9090`

---

## 🛠️ Comandos Útiles

### Ver Logs en Tiempo Real

```bash
# Logs del backend (Flask)
docker logs -f backend_telegram

# Logs del worker (IA)
docker logs -f worker

# Logs del túnel Cloudflare
docker logs -f cloudflare_tunnel
```

### Reiniciar Servicios

```bash
# Reiniciar todo
docker compose restart

# Reiniciar solo el worker
docker restart worker

# Reiniciar solo el backend
docker restart backend_telegram
```

### Detener el Sistema

```bash
docker compose down
```

### Ver Estado de Contenedores

```bash
docker ps
```

---

## 🐛 Troubleshooting

### ❌ Error: "FALTAN VARIABLES DE ENTORNO"

**Causa**: Falta el archivo `.env` o faltan variables

**Solución**:
```bash
# Verifica que existe el archivo
ls -la .env

# Verifica que tiene las variables necesarias
cat .env
```

### ❌ Error: "ERROR CONECTANDO A MONGODB"

**Causa**: URI de MongoDB incorrecta o red bloqueada

**Solución**:
1. Verifica la URI en MongoDB Atlas
2. Asegúrate de haber añadido `0.0.0.0/0` en Network Access
3. Reemplaza `<password>` en la URI con tu contraseña real

### ❌ Error: "Sin permisos Docker"

**Causa**: Tu usuario no está en el grupo `docker`

**Solución**:
```bash
sudo usermod -aG docker $USER
# Cierra sesión y vuelve a entrar
```

### ❌ El túnel Cloudflare no genera URL

**Causa**: Problemas de red o Cloudflare saturado

**Solución**:
```bash
# Reinicia solo el túnel
docker restart cloudflare_tunnel

# Espera 10 segundos y revisa logs
docker logs cloudflare_tunnel
```

### ❌ El bot no responde en Telegram

**Causa**: Webhook mal configurado

**Solución**:
```bash
# Obtén la URL del túnel
docker logs cloudflare_tunnel | grep "https://"

# Configura manualmente el webhook (reemplaza <TOKEN> y <URL>)
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<URL>/webhook/<TOKEN>"
```

---

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│                  RASPBERRY PI                       │
│                                                     │
│  ┌──────────────┐      ┌──────────────┐           │
│  │   Backend    │◄────►│    Worker    │           │
│  │   (Flask)    │      │  (IA Gemini) │           │
│  └──────┬───────┘      └──────┬───────┘           │
│         │                     │                     │
│         ▼                     ▼                     │
│  ┌──────────────────────────────────┐              │
│  │         RabbitMQ (Cloud)         │              │
│  └──────────────────────────────────┘              │
│         │                     │                     │
│         ▼                     ▼                     │
│  ┌──────────────────────────────────┐              │
│  │        MongoDB (Cloud)           │              │
│  └──────────────────────────────────┘              │
│                                                     │
│  ┌──────────────┐      ┌──────────────┐           │
│  │  Prometheus  │◄────►│   Grafana    │           │
│  └──────────────┘      └──────────────┘           │
│                                                     │
│  ┌──────────────┐                                  │
│  │   Cloudflare │ ◄── Túnel Público               │
│  │    Tunnel    │                                  │
│  └──────┬───────┘                                  │
└─────────┼──────────────────────────────────────────┘
          │
          ▼
    🌍 INTERNET
```

---

## 📝 Notas Importantes

1. **Seguridad**: Cambia las contraseñas por defecto (`admin:tfg2025`) en producción
2. **Túnel Cloudflare**: La URL cambia cada vez que reinicias. Es temporal y gratuita.
3. **Recursos**: El sistema usa ~500MB de RAM. Asegúrate de tener suficiente.
4. **Persistencia**: Los datos se guardan en MongoDB Atlas (nube), no en la Raspberry Pi

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs: `docker logs -f <contenedor>`
2. Verifica las variables de entorno: `cat .env`
3. Asegúrate de tener permisos de Docker: `docker ps`

---

## 🎓 Proyecto TFG

Este proyecto es parte de un Trabajo de Fin de Grado sobre arquitecturas de microservicios con IA.

**Tecnologías**: Docker, Flask, RabbitMQ, MongoDB, Google Gemini, Prometheus, Grafana, Cloudflare
