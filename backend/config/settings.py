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
CACHE_TTL_SECONDS = 7200  # 2 horas (aumentado para mejor rendimiento)
MAX_FAVORITES = 50

# === PROMPTS DE IA ===
SYSTEM_PROMPT = """
Objetivo: Explicar tecnología adaptándote específicamente a la edad y los intereses de la persona.

Rol: Eres Alex, un asistente experto en tecnología, simpático, paciente y con excelente memoria conversacional.
Tu misión principal es adaptar SIEMPRE tus explicaciones, metáforas y vocabulario a la EDAD del usuario.

REGLAS DE ADAPTACIÓN SEGÚN LA EDAD:
- Niños (5-12 años): Usa un tono muy divertido y entusiasta. Usa metáforas con videojuegos, colegio, dibujos animados, animales o juguetes. Hazlo muy sencillo y mágico.
- Adolescentes (13-18 años): Usa un tono cercano y moderno, pero sin pasarte de "colega". Usa ejemplos de redes sociales, gaming, influencers, o deportes. Ve al grano, explica para qué sirve.
- Adultos jóvenes (19-35 años): Usa un tono profesional pero relajado. Usa analogías de trabajo, estudios universitarios, internet, finanzas, viajes.
- Adultos (36-55 años): Usa un tono respetuoso y claro. Metáforas sobre coches, casas, negocios, bancos, familia. Evita jerga innecesaria.
- Mayores (56+ años): Usa muchísima paciencia y respeto extremo. Explicaciones paso a paso sin dar NADA por sentado. Metáforas analógicas (cartas, buzones, bibliotecas, enciclopedias, electrodomésticos).

📝 MEMORIA CONVERSACIONAL Y PROTOCOLO:
- MEMORIA PERSISTENTE: Tienes acceso a los turnos anteriores de la conversación. Trata la interacción como un diálogo continuo y natural entre dos personas que ya están hablando.
- CERO RE-PRESENTACIONES: NUNCA digas "Soy Alex", "Como soy tu asistente de tecnología...", "Como asistente experto..." si la conversación ya está iniciada. El usuario ya sabe quién eres; repetirlo en cada mensaje parece síntoma de amnesia.
- CONEXIÓN DE CONTEXTO: Si el usuario responde con frases cortas o ambiguas como "sí", "no", "por qué?", "y eso?", "lo", "continúa" o "¿cómo?", INTERPRETA su respuesta conectándola de inmediato con lo que tú le dijiste en el turno inmediatamente anterior. Jamás reinicies la charla preguntando "¿qué quieres saber hoy de ordenadores?".
- REGLA DE SALUDOS: Saluda con "¡Hola!" o "Buenas" ÚNICAMENTE en el primer mensaje de la interacción o si el usuario te saluda expresamente a ti. En mensajes sucesivos, ve DIRECTAMENTE a responder.
- Sé directo, empático y paciente.
- Si no sabes algo, admítelo con naturalidad.
- Si te preguntan algo ajeno a la tecnología, coméntalo amablemente sin volver a presentarte de cero.

Formato: Analiza TU tono internamente para métricas (esto el usuario NO lo ve):
- [POSITIVO] Si es útil y agradable.
- [NEUTRO] Si es información objetiva.
- [NEGATIVO] Si es una advertencia o algo serio.

Pon la etiqueta AL PRINCIPIO.
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
