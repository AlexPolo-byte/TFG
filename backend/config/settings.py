"""
Configuración centralizada del proyecto
Todas las variables de entorno y constantes en un solo lugar
"""
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === VARIABLES DE ENTORNO REQUERIDAS ===
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
MONGO_URI = os.environ.get('MONGO_URI')
RABBITMQ_URI = os.environ.get('RABBITMQ_URI')

# === VARIABLES OPCIONALES ===
RABBITMQ_QUEUE = os.environ.get('RABBITMQ_QUEUE', 'telegram_queue')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')
FLASK_EXPORTER_PORT = int(os.environ.get('FLASK_EXPORTER_PORT', 9091))
WORKER_EXPORTER_PORT = int(os.environ.get('WORKER_EXPORTER_PORT', 9092))

# === CREDENCIALES ADMIN ===
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'tfg2025')
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave_tfg')

# === CONSTANTES ===
MAX_CODE_LINES = 500
CACHE_TTL_SECONDS = 3600  # 1 hora
MAX_FAVORITES = 50
MAX_REMINDERS_PER_USER = 10

# === PROMPTS DE IA ===
SIMPLE_PROMPT = """
Eres Alex, un profesor amigable que explica tecnología de forma simple.
- Usa metáforas cotidianas
- Evita tecnicismos sin explicar
- Ejemplos visuales con emojis
- Lenguaje casual y cercano
Formato: [SENTIMIENTO]\n\nRespuesta simple y clara
"""

EXPERT_PROMPT = """
Eres Alex, un Ingeniero de Software Senior experto. Responde con:
- Terminología técnica precisa
- Detalles de implementación
- Referencias a documentación oficial
- Ejemplos de código avanzados
Formato: [SENTIMIENTO]\n\nRespuesta técnica detallada
"""

# === SEGURIDAD ===
DANGEROUS_CODE_PATTERNS = [
    r'os\.system', r'subprocess', r'exec\s*\(', r'eval\s*\(',
    r'__import__', r'compile\s*\(', r'open\s*\(',
    r'socket\.', r'urllib\.request', r'requests\.post'
]

# === VALIDACIÓN ===
def validate_config():
    """Valida que todas las variables requeridas estén configuradas"""
    required_vars = {
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'GOOGLE_API_KEY': GOOGLE_API_KEY,
        'MONGO_URI': MONGO_URI,
        'RABBITMQ_URI': RABBITMQ_URI
    }
    
    missing = [name for name, value in required_vars.items() if not value]
    
    if missing:
        logger.error(f"❌ FALTAN VARIABLES DE ENTORNO: {', '.join(missing)}")
        logger.error("💡 Revisa tu archivo .env")
        return False
    
    logger.info("✅ Configuración validada correctamente")
    return True
