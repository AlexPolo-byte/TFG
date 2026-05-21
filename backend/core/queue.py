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
            params.socket_timeout = 5  # Timeout de 5 segundos
            self.conn = pika.BlockingConnection(params)
            self.ch = self.conn.channel()
            self.ch.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            logger.info("✅ RabbitMQ conectado")
        except Exception as e:
            logger.error(f"⚠️ RabbitMQ no disponible: {e}")
            self.conn = None

    def publish(self, msg, queue=None):
        target_queue = queue or RABBITMQ_QUEUE
        if not self.conn or self.conn.is_closed:
            self._conn()
        if self.conn:
            try:
                self.ch.basic_publish(
                    exchange='',
                    routing_key=target_queue,
                    body=json.dumps(msg, default=str)
                )
                return True
            except Exception as e:
                logger.error(f"❌ Error publicando en RabbitMQ: {e}")
                self.conn = None  # Force reconnect next time
        return False

# Instancia singleton para ser usada en toda la app
mq_client = RabbitMQClient()
