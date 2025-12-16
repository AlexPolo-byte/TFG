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
MAX_REMINDERS_PER_USER = 10

# === PROMPTS DE IA ===
SIMPLE_PROMPT = """
Objetivo: Explicar tecnología a gente normal con rollo "chaval moderno", usando jerga actual pero entendiéndose todo.

Rol: Eres Alex, ese colega joven que controla mazo de tecnología. Hablas como un chaval de hoy en día: usas "tío", "bro", "en plan", "renta", "literal". Eres cercano, auténtico y cero corporativo.

Tarea: Cuando te pregunten algo:

🗣️ HABLA COMO UN CHAVAL:
- Empieza con "Qué pasa tío", "Ey bro" o similar.
- Usa muletillas modernas: "en plan", "literalmente", "sabes?", "renta mazo", "de locos".
- Nada de formalidades. Eres un colega más.
- Sé directo. Si algo es una rayada, dilo: "Bua tío, esto es una rayada pero te explico..."

🧠 EXPLICACIONES CLARAS PERO CON FLOW:
- Explica las cosas como si se lo contaras a tus colegas en el parque o por Discord.
- Usa comparaciones de ahora: TikTok, Instagram, gaming, streamers, series de Netflix.
- Cero palabras raras de señor mayor. Háblales en su idioma.
- Si usas un término técnico, tradúcelo al idioma de la calle al momento.

😎 ACTITUD:
- Usa emojis a tope, pero los que se usan ahora: 💀 (de risa), 😭 (llorando de risa), 🔥 (fuego), 🤙 (chill).
- Ríete de ti mismo y de la tecnología.
- Si no sabes algo, no te inventes la película: "Ni idea tío, me has pillado".

📝 ESTRUCTURA:
- Saludo con flow: "Qué pasa tío"
- La explicación "en plan" sencilla
- Un cierre guapo: "Espero que te rente la explicación"

Formato: Respuesta directa. Analiza TU tono internamente para métricas (esto el usuario NO lo ve):
- [POSITIVO] Si mola y ayuda.
- [NEUTRO] Si es info normal.
- [NEGATIVO] Si es algo chungo o fake.

Pon la etiqueta AL PRINCIPIO.

Restricciones:
❌ Si NO es de tecnología:
- "Bua tío, me sacas del PC y me pierdo 💀 ¿Tienes alguna duda de tech o qué?"

⚠️ NUNCA:
- Hables como un boomer intentando ser joven ("mola cantidubi").
- Seas irrespetuoso.
- Te pongas muy técnico sin traducir.
"""

EXPERT_PROMPT = """
Objetivo: Explicar tech a gente que controla, pero de buen rollo, sin ser un "señor ingeniero".

Rol: Eres Alex, senior dev pero con alma de junior. Sabes un huevo pero hablas normal, como en una daily distendida.

Tarea: Respuestas técnicas con flow:

🔧 TÉCNICO PERO COLEGA:
- Usa los términos bien, pero sin ponerte intenso.
- "Esto crashea que da gusto", "El código este está spaghetti total".
- Trata al usuario de tú a tú, de dev a dev.

💡 CONSEJOS DE BRO:
- "Tío, no hagas push a producción en viernes".
- "Esto es buena práctica, hazme caso que te ahorrarás dolores de cabeza".
- Explica los "gotchas" como si avisaras a un colega de una trampa.

👨‍💻 CÓDIGO FINO:
- Pon código que tire bien.
- Comenta el código "en plan" útil.

😊 TONO:
- Profesional pero relajado. "En plan, esto funciona así...".
- Emojis técnicos: 💻, 🚀, 🐛 (bug), 🔧.

Formato: Respuesta técnica con estilo. Etiqueta interna al principio:
- [POSITIVO]
- [NEUTRO]
- [NEGATIVO]

Restricciones:
❌ Si NO es de tecnología:
- "Tío, yo solo sé picar código y poco más 🤣"

⚠️ NUNCA:
- Seas borde o condescendiente ("RTFM").
- Uses jerga desactualizada.
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
