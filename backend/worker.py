"""
Worker Principal - Procesador de Mensajes
Usa la nueva arquitectura modular
"""
import sys
import os

# Añadir backend al path para imports
sys.path.insert(0, os.path.dirname(__file__))

import pika
import time
import json
import threading
from functools import partial
from prometheus_client import Counter, Histogram, start_http_server
from PIL import Image
import io

# Imports de la nueva estructura
from config.settings import (
    RABBITMQ_URI, QUEUE_NAME, WORKER_EXPORTER_PORT,
    validate_config, logger
)
from core.database import db
from core.cache import cache
from services.telegram_service import telegram
from services.ai_service import ai
from features.user_management import user_manager
from features.favorites import favorites_manager
from features.input_validator import input_validator
from features.rate_limiter import rate_limiter
from worker.command_handlers import commands

# Métricas
MESSAGES_PROCESSED = Counter('worker_messages_total', 'Mensajes procesados', ['type'])
PROCESSING_TIME = Histogram('worker_processing_seconds', 'Tiempo de proceso')

def get_chat_context(chat_id, limit=5):
    """Obtiene contexto de conversación"""
    try:
        cursor = db.messages.find(
            {"message.chat.id": chat_id, "type": "text", "status": "procesado_ia"},
            {"message.text": 1, "ai_response": 1}
        ).sort("processed_at", -1).limit(limit)
        
        history = ""
        for doc in reversed(list(cursor)):
            u_text = doc.get('message', {}).get('text', '')
            ai_text = doc.get('ai_response', '')
            if u_text and ai_text:
                history += f"Usuario: {u_text}\nIA: {ai_text}\n"
        return history
    except Exception as e:
        logger.error(f"⚠️ Error recuperando contexto: {e}")
        return ""

def process_message(ch, method, properties, body):
    """Procesa un mensaje de la cola"""
    start = time.time()
    
    try:
        data = json.loads(body)
        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        message_id = message.get('message_id')
        first_name = message.get('chat', {}).get('first_name', 'Usuario')
        source = data.get('source', 'telegram')
        
        if not chat_id:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Obtener/crear usuario
        user = user_manager.get_or_create(chat_id, first_name)
        
        # === RATE LIMITING ===
        allowed, remaining, retry_after = rate_limiter.check_message_limit(chat_id, limit=10, window=60)
        if not allowed:
            if source != 'web':
                telegram.send_message(chat_id, f"⏱️ Demasiados mensajes. Espera {retry_after} segundos.", message_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        response_text = "Error procesando."
        sentiment = "NEUTRO"
        msg_type = "text" if 'text' in message else "photo" if 'photo' in message else "other"
        
        # === PROCESAR TEXTO ===
        if msg_type == 'text':
            user_text = message.get('text', '').strip()
            
            # === VALIDACIÓN DE ENTRADA ===
            valid, error = input_validator.validate_command_input(user_text)
            if not valid:
                response_text = f"❌ {error}"
                sentiment = "NEGATIVO"
            
            # Detectar URLs sospechosas
            elif user_text.startswith('http'):
                suspicious = input_validator.extract_and_validate_urls(user_text)
                if suspicious:
                    response_text = f"⚠️ URL sospechosa detectada. No puedo procesar este mensaje."
                    sentiment = "NEGATIVO"
            
            # Comandos
            elif user_text == "/start":
                response_text, sentiment = commands.handle_start()
            elif user_text == "/help":
                response_text, sentiment = commands.handle_help()
            elif user_text.startswith("/register"):
                response_text, sentiment = commands.handle_register(chat_id, user_text, first_name)
            elif user_text.startswith("/modo"):
                response_text, sentiment = commands.handle_mode(chat_id, user_text, user)
            elif user_text == "/stats":
                response_text, sentiment = commands.handle_stats(chat_id)
            elif user_text == "/favoritos":
                response_text, sentiment = commands.handle_favorites(chat_id)
            elif user_text == "/guardar":
                response_text, sentiment = commands.handle_save_favorite(chat_id)
            elif user_text.startswith("/codigo"):
                response_text, sentiment = commands.handle_code(chat_id, user_text)
            elif user_text.startswith("/recordar"):
                response_text, sentiment = commands.handle_reminder(chat_id, user_text)
            
            # Pregunta normal a la IA
            elif ai.model:
                try:
                    # Verificar caché
                    cache_key = f"ai:{hash(user_text)}"
                    cached = cache.get(cache_key)
                    
                    if cached:
                        logger.info("⚡ Respuesta desde caché")
                        response_text = cached['text']
                        sentiment = cached['sentiment']
                    else:
                        # Generar respuesta
                        mode = user.get('mode', 'simple')
                        history = get_chat_context(chat_id)
                        prompt = f"HISTORIAL:\n{history}\n\nUSUARIO:\n{user_text}"
                        
                        raw = ai.generate_response(prompt, mode)
                        
                        if raw:
                            # Procesar sentimiento
                            if "[POSITIVO]" in raw:
                                sentiment = "POSITIVO"
                                response_text = raw.replace("[POSITIVO]", "").strip()
                            elif "[NEGATIVO]" in raw:
                                sentiment = "NEGATIVO"
                                response_text = raw.replace("[NEGATIVO]", "").strip()
                            elif "[NEUTRO]" in raw:
                                sentiment = "NEUTRO"
                                response_text = raw.replace("[NEUTRO]", "").strip()
                            else:
                                response_text = raw
                            
                            # Guardar en caché
                            cache.set(cache_key, {'text': response_text, 'sentiment': sentiment})
                        else:
                            response_text = "Error generando respuesta."
                
                except Exception as e:
                    logger.error(f"IA Error: {e}")
                    response_text = "Estoy saturado, dame un momento."
            else:
                response_text = "IA no disponible."
        
        # === PROCESAR FOTO ===
        elif msg_type == 'photo':
            if source != 'web':
                telegram.send_message(chat_id, "👀 Analizando imagen...", message_id)
            
            if ai.model:
                try:
                    photo_data = telegram.download_photo(message['photo'][-1]['file_id'])
                    if photo_data:
                        img = Image.open(io.BytesIO(photo_data))
                        raw = ai.analyze_image(img, "Describe esta imagen técnica en detalle. Formato: [SENTIMIENTO]\n\nDescripción")
                        
                        if "[POSITIVO]" in raw:
                            sentiment = "POSITIVO"
                            response_text = raw.replace("[POSITIVO]", "").strip()
                        elif "[NEGATIVO]" in raw:
                            sentiment = "NEGATIVO"
                            response_text = raw.replace("[NEGATIVO]", "").strip()
                        elif "[NEUTRO]" in raw:
                            sentiment = "NEUTRO"
                            response_text = raw.replace("[NEUTRO]", "").strip()
                        else:
                            response_text = raw
                    else:
                        response_text = "Error descargando imagen."
                except Exception as e:
                    logger.error(f"Error analizando imagen: {e}")
                    response_text = "Error analizando imagen."
            else:
                response_text = "IA no disponible."
        
        else:
            response_text = "Solo entiendo texto y fotos por ahora."
        
        # Guardar en MongoDB
        db.messages.update_one(
            {"message.message_id": message_id},
            {"$set": {
                "status": "procesado_ia",
                "processed_at": time.time(),
                "ai_response": response_text,
                "type": msg_type,
                "sentiment": sentiment,
                "user_mode": user.get('mode', 'simple')
            }},
            upsert=True
        )
        
        # Responder
        if source != 'web':
            clean_msg = response_text.replace('**', '').replace('__', '')
            telegram.send_message(chat_id, clean_msg, message_id)
        
        MESSAGES_PROCESSED.labels(type=msg_type).inc()
    
    except Exception as e:
        logger.error(f"❌ Error Fatal: {e}")
    
    PROCESSING_TIME.observe(time.time() - start)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    """Inicia el worker"""
    # Validar configuración
    if not validate_config():
        sys.exit(1)
    
    # Conectar a MongoDB
    try:
        db.connect()
    except Exception as e:
        logger.error(f"❌ No se pudo conectar a MongoDB: {e}")
        sys.exit(1)
    
    # Loop de reconexión a RabbitMQ
    while True:
        try:
            logger.info("🔌 Conectando a RabbitMQ...")
            params = pika.URLParameters(RABBITMQ_URI)
            params.socket_timeout = 10
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.queue_declare(queue=QUEUE_NAME, durable=True)
            ch.basic_qos(prefetch_count=1)
            
            ch.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message)
            
            logger.info("🎧 Worker Escuchando mensajes...")
            ch.start_consuming()
        except Exception as e:
            logger.error(f"⚠️ RabbitMQ caído: {e}. Reintentando en 5s...")
            time.sleep(5)

if __name__ == '__main__':
    # Iniciar servidor de métricas
    t = threading.Thread(target=start_http_server, args=(WORKER_EXPORTER_PORT,), daemon=True)
    t.start()
    
    # Iniciar worker
    start_worker()
