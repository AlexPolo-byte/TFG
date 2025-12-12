# Backend Reestructurado - Documentación

## 📁 Nueva Estructura

```
backend/
├── config/
│   └── settings.py          # ⚙️ Configuración centralizada
├── core/
│   ├── database.py          # 🗄️ Gestión de MongoDB
│   └── cache.py             # 💾 Gestión de Redis
├── services/
│   ├── telegram_service.py  # 📱 Comunicación con Telegram
│   └── ai_service.py        # 🧠 Servicio de IA (Gemini)
├── features/
│   ├── user_management.py   # 👤 Gestión de usuarios
│   ├── favorites.py         # ⭐ Sistema de favoritos
│   ├── code_generator.py    # 💻 Generación segura de código
│   └── reminders.py         # ⏰ Recordatorios programados
├── worker/
│   └── command_handlers.py  # 🎮 Handlers de comandos
├── api/
│   └── (próximamente)       # 🌐 Endpoints REST
├── app.py                   # 🚀 Aplicación Flask principal
├── worker.py                # ⚙️ Worker de procesamiento
└── requirements.txt         # 📦 Dependencias
```

## 🎯 Responsabilidades por Módulo

### Config
- **settings.py**: Variables de entorno, constantes, prompts de IA, validación

### Core
- **database.py**: Singleton de MongoDB con acceso a colecciones
- **cache.py**: Gestión de Redis con get/set/delete

### Services
- **telegram_service.py**: Envío de mensajes, voz, descarga de fotos
- **ai_service.py**: Configuración de Gemini, generación de respuestas, análisis de imágenes

### Features
- **user_management.py**: CRUD de usuarios, estadísticas
- **favorites.py**: Guardar/recuperar favoritos con límites
- **code_generator.py**: Generación segura con sanitización
- **reminders.py**: Programación de tareas con APScheduler

### Worker
- **command_handlers.py**: Lógica de todos los comandos del bot

## ✅ Ventajas de esta Estructura

1. **Separación de responsabilidades** - Cada archivo tiene un propósito claro
2. **Nombres descriptivos** - Se entiende qué hace cada módulo
3. **Fácil de mantener** - Cambios localizados en archivos específicos
4. **Testeable** - Cada módulo se puede testear independientemente
5. **Escalable** - Fácil añadir nuevas features sin tocar código existente
6. **Profesional** - Sigue mejores prácticas de arquitectura

## 🔄 Próximos Pasos

1. Actualizar `worker.py` para usar los nuevos módulos
2. Actualizar `app.py` para usar los nuevos módulos
3. Validar sintaxis de todos los archivos
4. Ejecutar tests
