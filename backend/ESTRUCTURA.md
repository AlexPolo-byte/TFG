# TFG - Arquitectura Completa del Proyecto

## 📁 Estructura Principal

```
TFG/
├── frontend/                 # 🎨 Vistas y UI (HTML/CSS)
│   ├── templates/            # Plantillas Jinja2 (base, chat, login, dashboard, etc.)
│   └── static/               # Archivos estáticos (imágenes, CSS externo)
├── backend/                  # ⚙️ Lógica de servidor y procesos Python
│   ├── app.py                # 🚀 Entrypoint web (Flask + Blueprints)
│   ├── worker.py             # 👷 Worker asíncrono (RabbitMQ consumer)
│   ├── api/                  # 🌐 Endpoints JSON (API REST)
│   │   └── routes.py
│   ├── web/                  # 🖥️ Controladores de vistas HTML
│   │   └── routes.py
│   ├── core/                 # 🗄️ Infraestructura y conexiones base
│   │   ├── database.py       # Conexión a MongoDB
│   │   ├── cache.py          # Conexión a Redis
│   │   └── queue.py          # Conexión a RabbitMQ
│   ├── features/             # 🧠 Casos de uso específicos
│   │   ├── user_management.py
│   │   ├── favorites.py
│   │   ├── code_generator.py
│   │   └── reminders.py
│   ├── handlers/             # 🎮 Procesadores de comandos de Telegram
│   │   └── command_handlers.py
│   ├── services/             # 📞 Integraciones con APIs externas
│   │   ├── telegram_service.py
│   │   └── ai_service.py
│   ├── config/               # ⚙️ Configuraciones globales
│   │   └── settings.py
│   └── Dockerfile            # 🐳 Imagen Docker del entorno Python
├── infra/                    # (Próximamente infra separada)
├── docker-compose.yml        # 🐳 Orquestador de contenedores
├── ngrok.yml                 # Configuración del túnel
├── prometheus.yml            # Configuración de métricas
└── promtail-config.yml       # Configuración de logs
```

## 🎯 Responsabilidades (Clean Architecture)

- **Frontend**: Exclusivamente archivos visuales. Flask los carga usando `template_folder='../frontend/templates'`.
- **Backend / app.py**: Ultra-ligero. Solo arranca Flask, conecta a base de datos y registra los Blueprints de API y Web.
- **Backend / api**: Devuelve `json()`. Utilizado por dashboards y scripts asíncronos.
- **Backend / web**: Devuelve `render_template()`.
- **Backend / core**: Define las herramientas (BD, Cache, Colas) pero NO la lógica de negocio.
- **Backend / services**: Conectores para servicios externos (Gemini, Telegram API).
- **Backend / features**: Funcionalidades puras del TFG (código de Python limpio).
- **Backend / worker.py**: El motor en segundo plano que saca mensajes de la cola y los manda a los *handlers*.
