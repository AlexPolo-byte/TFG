import os
import pika
import json
import logging

logger = logging.getLogger(__name__)

RABBITMQ_URI = os.environ.get('RABBITMQ_URI')
RABBITMQ_QUEUE = os.environ.get('RABBITMQ_QUEUE', 'telegram_queue')

class RabbitMQClient:
    def __init__(self):
        self.conn = None
        self.ch = None
        self._conn()

    def _conn(self):
        try:
            if not RABBITMQ_URI:
                logger.error("⚠️ RABBITMQ_URI no definido en variables de entorno")
                return
                
            params = pika.URLParameters(RABBITMQ_URI)
            params.socket_timeout = 5
            params.heartbeat = 60
            self.conn = pika.BlockingConnection(params)
            self.ch = self.conn.channel()
            self.ch.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            logger.info("✅ RabbitMQ conectado")
        except Exception as e:
            logger.error(f"⚠️ RabbitMQ no disponible: {e}")
            self.conn = None
            self.ch = None

    def publish(self, msg, queue=None):
        target_queue = queue or RABBITMQ_QUEUE
        # Limpiar _id si viene de MongoDB antes de serializar
        clean_msg = {k: v for k, v in msg.items() if k != '_id'} if isinstance(msg, dict) else msg
        body_bytes = json.dumps(clean_msg, default=str)

        # Hasta 2 intentos con reconexión automática si el socket se reseteó por inactividad
        for attempt in range(2):
            try:
                if not self.conn or self.conn.is_closed or not self.ch or self.ch.is_closed:
                    self._conn()
                
                if self.conn and self.ch:
                    self.ch.basic_publish(
                        exchange='',
                        routing_key=target_queue,
                        body=body_bytes,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Reintentando publicación tras error en RabbitMQ (intento {attempt + 1}): {e}")
                try:
                    if self.conn and not self.conn.is_closed:
                        self.conn.close()
                except Exception:
                    pass
                self.conn = None
                self.ch = None

        logger.error("❌ Fallo definitivo publicando en RabbitMQ tras reintentos")
        return False

# Instancia singleton para ser usada en toda la app
mq_client = RabbitMQClient()
