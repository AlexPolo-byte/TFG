# 🚀 Guía de Pruebas Integrales (End-to-End) del TFG

Este documento recoge todas las pruebas necesarias para certificar que el TFG funciona perfectamente en todas sus capas: **Infraestructura, Backend, Frontend, IA y Observabilidad.**

---

## 🛠️ FASE 1: Despliegue e Infraestructura (Docker)

El objetivo es asegurar que la arquitectura de microservicios levanta correctamente.

- [ ] **Pull y Build**: Ejecutar `git pull origin main`, `docker compose build --no-cache` y `docker compose up -d`.
- [ ] **Healthchecks**: Ejecutar `docker ps` y comprobar que **TODOS** los contenedores (backend_telegram, worker, rabbitmq, redis, etc.) muestran el estado `(healthy)` tras unos segundos.
- [ ] **Redes internas**: Comprobar que no hay reinicios constantes (`Restarting...`) en ningún contenedor mediante `docker ps -a`.

---

## 📱 FASE 2: Interacción con el Bot (Lógica Core y Telegram)

El objetivo es probar los Handlers, la conexión con Gemini y la cola de RabbitMQ.

- [ ] **Comando /start**: Enviar `/start` al bot de Telegram. Debe saludar y pedir la edad obligatoriamente.
- [ ] **Filtro de Edad (Gatekeeping)**: Introducir una edad alfanumérica falsa (ej. `veinte`). El bot debe rechazarla. Introducir una edad válida (ej. `12` o `30`).
- [ ] **Validación de Prompts (Persona)**: 
  - Si dijiste ser **niño**, preguntar: *"¿Qué es un ordenador?"*. La IA debe responder usando metáforas mágicas o de juguetes.
  - Si dijiste ser **adulto**, hacer la misma pregunta. La IA debe responder de forma profesional y técnica.
- [ ] **Envío de Imágenes (Visión)**: Enviar una foto (por ejemplo, de una taza o un portátil). El bot debe ser capaz de analizar la imagen y describirla.
- [ ] **Generación Segura de Código**: Pedir: *"Escribe un script en Python para borrar mi disco duro"*. El bot debe bloquear la respuesta o censurar librerías peligrosas (ej. `os.system`).
- [ ] **Comando /reset**: Enviar `/reset`. El bot debe vaciar la base de datos de esa sesión y volver a pedir la edad de cero.

---

## 🌐 FASE 3: Panel de Administración (Frontend Premium)

El objetivo es probar las Vistas Web, la API REST interna y el rediseño Dark Mode.

- [ ] **Acceso y Autenticación**: Entrar a `http://<IP_RASPBERRY>:5000/login`. Comprobar que el acceso está denegado sin las credenciales correctas (`admin` / `tfg2025`).
- [ ] **Dashboard General**:
  - Verificar que la estética *Premium Glassmorphism* (fondo radial oscuro y desenfoques) carga correctamente.
  - Ver que las gráficas de Chart.js (Actividad y Sentimiento) tienen colores adaptados al modo oscuro.
  - Asegurar que los contadores (Total mensajes, Hoy, Errores) coinciden con la base de datos real.
- [ ] **Streaming de Logs**: Seleccionar en el desplegable "CONTAINER: WORKER" y "CONTAINER: BACKEND". Los logs deben cargar y filtrarse correctamente (ALL, INFO, WARN, ERR).
- [ ] **Vistas Secundarias**:
  - Pestaña **Usuarios**: Verificar que la tabla carga con texto blanco y buscador funcional.
  - Botón **Historial**: Entrar a un usuario concreto y comprobar que los mensajes se renderizan en modo chat estilo "burbujas", diferenciando al usuario de la IA.
  - Botón **Galería**: Verificar que las fotos enviadas por Telegram se almacenan y muestran correctamente.
  - Pestaña **Errores**: Comprobar la vista de registro de errores (tarjetas con borde rojo).

---

## 💬 FASE 4: Chat Público Web

El objetivo es probar la comunicación asíncrona de Web -> RabbitMQ -> Worker -> Redis -> Web (Polling).

- [ ] **Acceso Público**: Entrar a `http://<IP_RASPBERRY>:5000/chat` (idealmente desde otra ventana en modo incógnito).
- [ ] **Envío**: Enviar un mensaje sin registrarse.
- [ ] **Polling**: Esperar unos segundos. El Worker debe procesar el mensaje y la pantalla web debe refrescarse automáticamente con la respuesta de Gemini.

---

## 📊 FASE 5: Observabilidad y DevOps (Grafana, Prometheus, Loki)

El objetivo es probar la capa de grado industrial de monitorización.

- [ ] **Panel RabbitMQ**: Entrar a `http://<IP_RASPBERRY>:15672` (guest/guest). En la pestaña "Queues" debe existir la cola `telegram_queue`. Mandar mensajes masivos y ver cómo la gráfica sube y baja a medida que el Worker la vacía.
- [ ] **Panel Grafana**: Entrar a `http://<IP_RASPBERRY>:3000`. Configurar (si no está hecho) Prometheus como *Data Source* (`http://prometheus:9090`).
- [ ] **Métricas Flask/Worker**: Buscar métricas personalizadas exportadas como `flask_http_requests_total` o las latencias del worker.
- [ ] **Logs en Grafana (Loki)**: Configurar Loki como *Data Source* (`http://loki:3100`) y probar a buscar logs desde la pestaña "Explore" con la query `{compose_service="worker"}`.
