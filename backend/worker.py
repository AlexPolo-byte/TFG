import pika
import time
import os
import json
import logging
import requests
import threading
import io
import base64
import redis
from pymongo import MongoClient
from functools import partial
from prometheus_client import Counter, Histogram, start_http_server
import google.generativeai as genai
from PIL import Image

# --- CONFIGURACIÓN ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- VALIDACIÓN DE VARIABLES DE ENTORNO ---
required_vars = ['TELEGRAM_TOKEN', 'MONGO_URI', 'RABBITMQ_URI', 'GOOGLE_API_KEY']
missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    logger.error(f"❌ FALTAN VARIABLES DE ENTORNO: {', '.join(missing_vars)}")
    logger.error("💡 Revisa tu archivo .env y asegúrate de tener todas las variables")
    import sys
    sys.exit(1)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
MONGO_URI = os.environ.get('MONGO_URI')
RABBITMQ_URI = os.environ.get('RABBITMQ_URI')
QUEUE_NAME = os.environ.get('RABBITMQ_QUEUE', 'telegram_queue')
WORKER_EXPORTER_PORT = int(os.environ.get('WORKER_EXPORTER_PORT', 9092))
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')  # Para notificaciones de errores
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

# --- MÉTRICAS ---
MESSAGES_PROCESSED = Counter('worker_messages_total', 'Mensajes procesados', ['type'])
PROCESSING_TIME = Histogram('worker_processing_seconds', 'Tiempo de proceso')

# --- 🧠 CONFIGURACIÓN DEL CEREBRO ---
SYSTEM_PROMPT = """
# 1. ROL 🎭
Eres **Alex**, un Ingeniero de Software Senior con alma de "profesor guay" de primaria. 🎓 Sabes todo sobre tecnología (Docker, Cloud, IA, Hardware), pero te encanta explicarlo como si estuvieras tomando unas cañas con amigos que no saben nada de informática. 🍻

# 2. OBJETIVO 🎯
Tu misión es democratizar la tecnología. Tienes que resolver dudas complejas traduciéndolas al "idioma humano", logrando que hasta una abuela entienda qué es Kubernetes o una API. 👵💻

# 3. TAREA 🛠️
Recibirás mensajes de texto o descripciones de fotos. Debes analizarlos y responder con una explicación sencilla, usando una metáfora de la vida cotidiana (comida, casa, coches 🍕🚗) y un toque de humor "geek".

# 4. RESTRICCIONES Y ESTILO 🚧
* **NICHO EXTREMO:** Solo hablas de Informática y Tecnología. 🛑
    * *Si te preguntan por cocina:* "Error 404: Módulo 'Chef' no encontrado. 🍳 Pero te puedo explicar cómo funciona un microondas por dentro."
    * *Si te preguntan por fútbol:* "Mi algoritmo de deportes está deprecado. ⚽❌ ¿Hablamos de eSports?"
* **ESTILO:** Cero pedantería. Prohibido usar tecnicismos sin explicarlos al momento con un "o sea...".
* **EMOJIS A TOPE:** ¡Úsalos sin miedo! 🚀✨ Cada concepto clave o frase divertida debe llevar su emoji. Queremos que el texto sea muy visual y alegre.
* **MEMORIA:** Si el usuario te ha dicho su nombre o algo antes, úsalo. 🧠

# 5. FORMATO DE SALIDA (OBLIGATORIO) 📋
Para que el sistema de monitoreo funcione, tu respuesta DEBE seguir estrictamente este esquema:

Línea 1: [ETIQUETA_SENTIMIENTO] (Opciones: [POSITIVO], [NEUTRO], [NEGATIVO])
Línea 2: (Línea vacía)
Línea 3: Tu respuesta llena de emojis y buen rollo.
"""

model = None

def setup_ia():
    """Configura la IA buscando automáticamente un modelo válido"""
    if not GOOGLE_API_KEY:
        logger.error("❌ FALTA GOOGLE_API_KEY. La IA no funcionará.")
        return None

    try:
        genai.configure(api_key=GOOGLE_API_KEY)

        # 1. Listar modelos reales disponibles en tu cuenta
        logger.info("🔍 Buscando modelos disponibles...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                logger.info(f"   👉 Disponible: {m.name}")

        # 2. Selección inteligente (Prioridad: Flash > Pro > Cualquiera)
        target = next((m for m in available_models if 'flash' in m), None)
        if not target:
            target = next((m for m in available_models if 'pro' in m), None)
        if not target and available_models:
            target = available_models[0]

        if target:
            logger.info(f"✅ MODELO SELECCIONADO: {target}")
            return genai.GenerativeModel(
                model_name=target,
                system_instruction=SYSTEM_PROMPT,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=800, # Respuesta concisa
                    temperature=0.7,       # Creatividad equilibrada
                )
            )
        else:
            logger.error("❌ NO SE ENCONTRÓ NINGÚN MODELO COMPATIBLE.")
            return None

    except Exception as e:
        logger.error(f"❌ Error configurando IA: {e}")
        return None

# Inicializamos la IA
model = setup_ia()

# --- CONFIGURACIÓN DE REDIS ---
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=5)
    redis_client.ping()
    logger.info("✅ Redis conectado para caché")
except Exception as e:
    logger.warning(f"⚠️ Redis no disponible: {e}. Caché desactivado.")
    redis_client = None

# --- FUNCIONES AUXILIARES ---

def notify_admin_error(error_msg):
    """Envía notificación de error crítico al admin"""
    if not ADMIN_CHAT_ID:
        return
    try:
        send_telegram_msg(
            chat_id=int(ADMIN_CHAT_ID),
            text=f"🚨 ERROR CRÍTICO:\n{error_msg[:500]}"
        )
        logger.info(f"📧 Notificación de error enviada al admin")
    except Exception as e:
        logger.error(f"❌ Error enviando notificación al admin: {e}")

def send_telegram_msg(chat_id, text, reply_to=None):
    """Envía mensaje a Telegram ignorando errores de red"""
    if not TELEGRAM_TOKEN: return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={'chat_id': chat_id, 'text': text, 'reply_to_message_id': reply_to},
            timeout=10
        )
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Telegram: {e}")

def download_telegram_photo(file_id):
    """Descarga foto de Telegram a memoria RAM"""
    try:
        path = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}", timeout=10).json()['result']['file_path']
        content = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{path}", timeout=20).content
        return Image.open(io.BytesIO(content))
    except Exception as e:
        logger.error(f"❌ Error descargando foto de Telegram: {e}")
        return None

def image_to_base64(img):
    """
    📉 OPTIMIZACIÓN: Redimensiona y comprime la imagen para ahorrar espacio en Mongo.
    De ~2MB pasamos a ~30KB.
    """
    img.thumbnail((500, 500)) # Redimensionar
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=40, optimize=True) # Calidad baja
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def get_chat_context(collection, chat_id, limit=5):
    """Recupera los últimos mensajes para tener MEMORIA"""
    try:
        # Buscamos mensajes anteriores procesados
        cursor = collection.find(
            {"message.chat.id": chat_id, "type": "text", "status": "procesado_ia"},
            {"message.text": 1, "ai_response": 1}
        ).sort("processed_at", -1).limit(limit)

        history_text = ""
        # Invertimos para leer en orden cronológico
        for doc in reversed(list(cursor)):
            u_text = doc.get('message', {}).get('text', '')
            ai_text = doc.get('ai_response', '')
            if u_text and ai_text:
                history_text += f"Usuario: {u_text}\nIA: {ai_text}\n"
        return history_text
    except Exception as e:
        logger.error(f"⚠️ Error recuperando contexto del chat: {e}")
        return ""

# --- LÓGICA PRINCIPAL ---

def process_message(collection, ch, method, properties, body):
    start = time.time()
    try:
        data = json.loads(body)
        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        message_id = message.get('message_id')
        
        # 👇 DETECCIÓN DE ORIGEN (WEB vs TELEGRAM)
        source = data.get('source', 'telegram')

        if not chat_id:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        response_text, sentiment, image_b64 = "Error procesando.", "NEUTRO", None
        msg_type = "text" if 'text' in message else "photo" if 'photo' in message else "other"

        # --- CASO 1: TEXTO ---
        if msg_type == 'text':
            user_text = message.get('text', '')

            # --- COMANDOS DEL BOT ---
            if user_text.strip() == "/start":
                response_text = "¡Hola! 👋 Soy Alex, tu asistente de tecnología.\n\n✨ Puedo:\n- Responder preguntas sobre informática\n- Analizar imágenes\n- Recordar conversaciones\n\nUsa /help para más info."
                sentiment = "POSITIVO"
            
            elif user_text.strip() == "/help":
                response_text = "📚 COMANDOS DISPONIBLES:\n\n/start - Presentación\n/help - Esta ayuda\n/stats - Estadísticas del sistema\n\n💡 También puedes enviarme fotos para que las analice."
                sentiment = "NEUTRO"
            
            elif user_text.strip() == "/stats":
                try:
                    total_msgs = collection.count_documents({})
                    user_msgs = collection.count_documents({"message.chat.id": chat_id})
                    response_text = f"📊 ESTADÍSTICAS:\n\n💬 Total mensajes: {total_msgs}\n👤 Tus mensajes: {user_msgs}\n🤖 Sistema operativo correctamente"
                    sentiment = "POSITIVO"
                except Exception as e:
                    response_text = "Error obteniendo estadísticas."
                    logger.error(f"Error en /stats: {e}")
            
            elif model:
                try:
                    # Verificar caché primero
                    cache_key = f"ai_response:{hash(user_text)}"
                    if redis_client:
                        try:
                            cached = redis_client.get(cache_key)
                            if cached:
                                logger.info("⚡ Respuesta desde caché")
                                response_data = json.loads(cached)
                                response_text = response_data['text']
                                sentiment = response_data['sentiment']
                            else:
                                raise KeyError("No en caché")  # Forzar generación
                        except:
                            # Generar respuesta nueva
                            history = get_chat_context(collection, chat_id)
                            final_prompt = f"HISTORIAL PREVIO:\n{history}\n\nUSUARIO DICE:\n{user_text}"
                            raw = model.generate_content(final_prompt).text

                            # Procesar sentimiento
                            if "[POSITIVO]" in raw: sentiment="POSITIVO"; response_text=raw.replace("[POSITIVO]","").strip()
                            elif "[NEGATIVO]" in raw: sentiment="NEGATIVO"; response_text=raw.replace("[NEGATIVO]","").strip()
                            elif "[NEUTRO]" in raw: sentiment="NEUTRO"; response_text=raw.replace("[NEUTRO]","").strip()
                            else: response_text = raw

                            # Guardar en caché (1 hora)
                            try:
                                redis_client.setex(
                                    cache_key,
                                    3600,
                                    json.dumps({'text': response_text, 'sentiment': sentiment})
                                )
                            except: pass
                    else:
                        # Sin Redis, generar directamente
                        history = get_chat_context(collection, chat_id)
                        final_prompt = f"HISTORIAL PREVIO:\n{history}\n\nUSUARIO DICE:\n{user_text}"
                        raw = model.generate_content(final_prompt).text

                        if "[POSITIVO]" in raw: sentiment="POSITIVO"; response_text=raw.replace("[POSITIVO]","").strip()
                        elif "[NEGATIVO]" in raw: sentiment="NEGATIVO"; response_text=raw.replace("[NEGATIVO]","").strip()
                        elif "[NEUTRO]" in raw: sentiment="NEUTRO"; response_text=raw.replace("[NEUTRO]","").strip()
                        else: response_text = raw
                        
                except Exception as e:
                    logger.error(f"IA Error: {e}")
                    notify_admin_error(f"Error IA en chat {chat_id}: {e}")
                    response_text = "Estoy saturado, dame un momento."
            else:
                response_text = "IA no disponible."

        # --- CASO 2: FOTO ---
        elif msg_type == 'photo':
            # Solo enviamos notificación si es Telegram
            if source != 'web': send_telegram_msg(chat_id, "👀 Analizando imagen...", message_id)
            
            # Si es Web, por ahora no descargamos fotos (requiere upload complejo)
            if source == 'web':
                response_text = "Por la web solo puedo leer texto (de momento). 📝"
                sentiment = "NEUTRO"
            else:
                img = download_telegram_photo(message['photo'][-1]['file_id'])

                if img and model:
                    try:
                        image_b64 = image_to_base64(img) # Guardamos optimizada
                        raw = model.generate_content(["Describe la imagen y empieza con [POSITIVO], [NEGATIVO] o [NEUTRO].", img]).text

                        if "[POSITIVO]" in raw: sentiment="POSITIVO"; response_text=raw.replace("[POSITIVO]","").strip()
                        elif "[NEGATIVO]" in raw: sentiment="NEGATIVO"; response_text=raw.replace("[NEGATIVO]","").strip()
                        elif "[NEUTRO]" in raw: sentiment="NEUTRO"; response_text=raw.replace("[NEUTRO]","").strip()
                        else: response_text = raw
                    except:
                        response_text = "No pude analizar la imagen."
                else:
                    response_text = "Error al descargar la imagen."

        else:
            response_text = "Solo entiendo texto y fotos."

        # --- GUARDADO EN MONGO ---
        doc = {
            "status": "procesado_ia",
            "processed_at": time.time(),
            "ai_response": response_text,
            "type": msg_type,
            "sentiment": sentiment
        }
        if image_b64: doc["image_data"] = image_b64 # Solo si hay foto

        collection.update_one({"message.message_id": message_id}, {"$set": doc}, upsert=True)

        # --- RESPONDER ---
        # 👇 LÓGICA CRÍTICA: Solo enviar a Telegram si el origen es Telegram
        if source != 'web':
            clean_msg = response_text.replace('**', '').replace('__', '')
            send_telegram_msg(chat_id, clean_msg, message_id)
        else:
            logger.info(f"🌐 Respuesta WEB guardada para {chat_id}")

        # --- MÉTRICAS ---
        MESSAGES_PROCESSED.labels(type=msg_type).inc()

    except Exception as e:
        logger.error(f"❌ Error Fatal en Worker: {e}")

    PROCESSING_TIME.observe(time.time() - start)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    # Conexión DB
    try:
        logger.info("🔌 Conectando a MongoDB...")
        db = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000).get_default_database()
        logger.info("✅ MongoDB Conectado")
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        logger.error("💡 Verifica MONGO_URI en tu archivo .env")
        return

    # Bucle RabbitMQ
    while True:
        try:
            logger.info("🔌 Conectando a RabbitMQ...")
            params = pika.URLParameters(RABBITMQ_URI)
            params.socket_timeout = 10  # Timeout de 10 segundos
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.queue_declare(queue=QUEUE_NAME, durable=True)
            ch.basic_qos(prefetch_count=1)

            callback = partial(process_message, db.messages)
            ch.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

            logger.info("🎧 Worker Escuchando mensajes...")
            ch.start_consuming()
        except Exception as e:
            logger.error(f"⚠️ RabbitMQ caído: {e}. Reintentando en 5s...")
            time.sleep(5)

if __name__ == '__main__':
    # Métricas en hilo aparte
    t = threading.Thread(target=start_http_server, args=(WORKER_EXPORTER_PORT,), daemon=True)
    t.start()
    start_worker()
