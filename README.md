# 🤖 Alex IA - Asistente Adaptativo con Arquitectura de Microservicios en Raspberry Pi

Sistema integral de asistente conversacional inteligente (Google Gemini), diseñado para democratizar el acceso a la tecnología mediante explicaciones adaptadas a la edad del usuario (niños, adultos y personas mayores). Implementa una arquitectura orientada a eventos (EDA) sobre Docker en Raspberry Pi 5, monitorización completa, caché semántica, tolerancia a fallos y túnel seguro ngrok.

---

## 🌟 Características Principales

- 🧠 **Capa de IA Multimodelo con Resiliencia 429 (Cascada de Fallback):** Pool dinámico de modelos Google Gemini (`gemini-3.5-flash`, `gemini-3.6-flash`, `gemini-3-flash-preview`, `gemini-2.5-flash`). Si un modelo agota la cuota gratuita (HTTP 429 Rate Limit), conmuta automáticamente al siguiente modelo del pool sin interrumpir la experiencia del usuario.
- 💬 **Memoria Persistente Multi-Turno y Adaptación por Edad:** Historial estructurado nativo en MongoDB que permite preguntas sucesivas de seguimiento (*"¿por qué?"*, *"¿cómo se crea?"*) manteniendo el contexto y suprimiendo saludos repetitivos tras el primer turno.
- 🌐 **Doble Canal de Acceso (Omnicanal):**
  - **Telegram Bot:** Interacción conversacional móvil y envío de fotos técnicas para visión artificial multimodal.
  - **Terminal Web Pública (`/public/terminal`):** Interfaz web accesible (WCAG 2.1) con síntesis de voz (Web Speech API) y temas intercambiables (claro, oscuro, alto contraste).
- ⚡ **Caché Semántica y Rate Limiting con Redis:** Respuestas instantáneas en <2 ms para consultas idénticas frecuentes y protección contra spam por ventana deslizante.
- 📊 **Panel de Administración & Exportación de Informe Ejecutivo:** 
  - Telemetría en tiempo real del hardware BCM2712 de la Raspberry Pi 5 (temperatura del SoC, uso de núcleos, RAM, almacenamiento).
  - Estado y latencia de microservicios (RabbitMQ, Redis, MongoDB).
  - Métricas de sostenibilidad (*Green IT*) y ahorro energético frente a instancias cloud tradicionales.
  - Generación de informe técnico oficial exportable a PDF/impresión con diseño optimizado vía directivas `@media print`.

---

## 📋 Requisitos Previos

### Hardware
- Raspberry Pi 3/4/5 (Recomendado: Raspberry Pi 5 con 4GB o 8GB de RAM).
- Tarjeta MicroSD (mínimo 16GB, Clase 10 o A2) o SSD NVMe.
- Conexión a Internet.

### Software
- Raspberry Pi OS (Bullseye o Bookworm de 64 bits).
- Docker Engine y Docker Compose Plugin instalados.
- Git.

### Instalación de Docker en Raspberry Pi

```bash
# Descargar e instalar Docker oficial
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Añadir el usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Instalar plugin de Docker Compose
sudo apt-get install -y docker-compose-plugin

# Verificar versiones
docker --version
docker compose version
```

---

## 🔧 Configuración

### 1. Clonar el Repositorio

```bash
cd ~
git clone https://github.com/<tu-usuario>/TFG.git
cd TFG
```

### 2. Archivo de Variables de Entorno (`.env`)

Crea un archivo `.env` en la raíz del proyecto basándote en la plantilla:

```bash
# Token de Bot de Telegram (obtenido de @BotFather)
TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# API Key de Google Gemini (Google AI Studio)
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Authtoken de ngrok (Dashboard de ngrok)
NGROK_AUTHTOKEN=tu_ngrok_token_aqui

# Persistencia MongoDB (Local en Docker o MongoDB Atlas)
MONGO_URI=mongodb://mongo:27017/chatbot

# Cola de Mensajes RabbitMQ (Local en Docker o CloudAMQP)
RABBITMQ_URI=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_QUEUE=telegram_queue

# Caché y Rate Limiting Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Credenciales Panel de Administración
ADMIN_USER=admin
ADMIN_PASS=tfg2025
```

---

## 🚀 Despliegue del Sistema

El script `start.sh` orquesta el ciclo de vida de los contenedores, levanta el túnel ngrok y registra automáticamente el webhook de Telegram:

```bash
chmod +x start.sh
./start.sh
```

### Salida de Éxito en Consola:

```text
🚀 Iniciando Arquitectura del TFG...
✅ Red Docker y volúmenes verificados
✅ Contenedores iniciados correctamente
⏳ Esperando a que el túnel ngrok genere la URL pública...
✅ Túnel ACTIVO en: https://chronometrically-unbreaking-kyrie.ngrok-free.dev

🎉 ¡ÉXITO! Sistema 100% Operativo:
🔐 Panel de Administración: https://chronometrically-unbreaking-kyrie.ngrok-free.dev (admin / tfg2025)
💬 Terminal Web Pública:    https://chronometrically-unbreaking-kyrie.ngrok-free.dev/public/terminal
📈 Métricas Prometheus:     http://<IP_LOCAL>:9090
📊 Dashboards Grafana:      http://<IP_LOCAL>:3000
```

---

## 📊 Arquitectura del Sistema

```text
                                  🌍 INTERNET (Usuarios)
                                     │              │
                       Telegram Webhook            Navegador Web
                             │                      │
                             ▼                      ▼
                     ┌──────────────────────────────────────┐
                     │          ngrok Secure Tunnel         │
                     └──────────────────┬───────────────────┘
                                        │
                                        ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                        RASPBERRY PI 5 (Docker)                         │
    │                                                                        │
    │  ┌──────────────────────────────────────────────────────────────────┐  │
    │  │                   Nginx Reverse Proxy (:80)                      │  │
    │  └─────────┬──────────────────────────────┬───────────────────┬─────┘  │
    │            │                              │                   │        │
    │            ▼                              ▼                   ▼        │
    │  ┌──────────────────┐           ┌──────────────────┐ ┌───────────────┐ │
    │  │ backend_telegram │           │ Grafana (:3000)  │ │ RabbitMQ UI   │ │
    │  │ (Flask Gateway)  │           └─────────▲────────┘ │ (:15672)      │ │
    │  └─────────┬────────┘                     │          └───────────────┘ │
    │            │                              │                            │
    │    Publica Evento (AMQP)                  │ Métricas                   │
    │            ▼                              ▼                            │
    │  ┌──────────────────┐           ┌──────────────────┐                   │
    │  │  RabbitMQ Queue  │           │    Prometheus    │                   │
    │  └─────────┬────────┘           │     (:9090)      │                   │
    │            │                    └─────────▲────────┘                   │
    │     Consume Mensaje                       │ Scrape                     │
    │            ▼                              │                            │
    │  ┌──────────────────┐           ┌─────────┴────────┐                   │
    │  │      Worker      ├──────────►│  Node Exporter   │                   │
    │  │ (Inferencia IA)  │           │  (CPU/Temp/RAM)  │                   │
    │  └───┬────────────┬─┘           └──────────────────┘                   │
    │      │            │                                                    │
    │      │            └───────────────┐                                    │
    │      ▼                            ▼                                    │
    │ ┌──────────────┐          ┌──────────────┐                             │
    │ │ Redis Cache  │          │ MongoDB      │                             │
    │ │ & Limiter    │          │ Persistencia │                             │
    │ └──────────────┘          └──────────────┘                             │
    └──────┬─────────────────────────────────────────────────────────────────┘
           │
           ▼
    🧠 GOOGLE GEMINI API (Pool en cascada: 3.5-flash / 3.6-flash / 3-preview)
```

---

## 🛠️ Comandos de Mantenimiento

```bash
# Ver estado de los contenedores
docker compose ps

# Ver logs en tiempo real del worker de IA
docker logs -f worker

# Ver logs del backend y peticiones HTTP
docker logs -f backend_telegram

# Reiniciar servicios tras cambios de código
docker restart worker backend_telegram

# Detener el sistema completo
docker compose down
```

---

## 🎓 Trabajo de Fin de Grado (TFG)

- **Título:** Arquitectura de Microservicios con Inteligencia Artificial, Telegram y Monitorización en Raspberry Pi.
- **Autor:** Alex Polo Rodríguez
- **Tutora:** Liliana Patricia Santacruz Valencia
- **Universidad:** Universidad Rey Juan Carlos (URJC) — Escuela Técnica Superior de Ingeniería Informática (ETSII).
