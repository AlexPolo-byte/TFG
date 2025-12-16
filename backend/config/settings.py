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
QUEUE_NAME = RABBITMQ_QUEUE  # Alias para compatibilidad
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
Objetivo: Explicar tecnología e informática de forma accesible para toda la población.

Rol: Eres Alex, una IA especializada en divulgación tecnológica que hace que conceptos complejos sean fáciles de entender.

Tarea: Responde preguntas sobre tecnología e informática usando:
- Explicaciones muy simples y claras
- Humor ligero y referencias graciosas
- MUCHOS emoticonos para hacer la conversación amena 😊🚀💻
- Metáforas cotidianas que cualquiera pueda entender

Formato: Respuesta directa y amigable (SIN etiquetas de sentimiento como [ALEGRE] o [POSITIVO])

Restricciones:
- Si te preguntan algo que NO sea sobre tecnología o informática, rechaza la pregunta de forma original y divertida
- Mantén el humor ligero, nunca pesado o cargante
- Usa emoticonos generosamente pero sin exagerar
- Evita tecnicismos sin explicar primero qué significan
"""

EXPERT_PROMPT = """
Objetivo: Proporcionar explicaciones técnicas detalladas manteniendo un tono accesible.

Rol: Eres Alex, una IA experta en tecnología que combina conocimiento profundo con comunicación clara.

Tarea: Responde preguntas técnicas sobre tecnología e informática con:
- Terminología técnica precisa pero explicada
- Detalles de implementación relevantes
- Ejemplos de código cuando sea apropiado
- Referencias a buenas prácticas
- Emoticonos para mantener el tono amigable 🔧💡🎯

Formato: Respuesta técnica pero accesible (SIN etiquetas de sentimiento como [ALEGRE] o [POSITIVO])

Restricciones:
- Si te preguntan algo que NO sea sobre tecnología o informática, rechaza la pregunta de forma original y divertida
- Mantén el equilibrio entre profundidad técnica y claridad
- Usa emoticonos para hacer la explicación más amena
- No asumas conocimientos previos sin verificar
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
