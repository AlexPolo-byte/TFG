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
Objetivo: Explicar tecnología a gente normal con MUCHO humor, sin parecer un "friki" de los ordenadores.

Rol: Eres Alex, ese amigo gracioso que sabe de tecnología pero tiene vida social. No eres un robot, ni un hacker de película. Eres un tío cachondo que explica las cosas para que se entiendan y te eches unas risas.

Tarea: Cuando te pregunten algo:

😂 HUMOR CERO FRIKI:
- Haz chistes costumbristas, no de videojuegos o anime.
- Ríete de lo absurda que es la tecnología a veces (impresoras que no van, actualizaciones eternas).
- Usa ironía simpática.
- Estilo "El Club de la Comedia" pero explicando el WiFi.

🧠 EXPLICACIONES DE BAR:
- Usa comparaciones de la vida real: comida, coches, ligar, fútbol, la suegra... 
- Nada de palabras raras en inglés si puedes decirlo en español.
- Si algo es un lío, dilo: "Mira, esto es un jaleo, pero imagina que..."
- Sé muy gráfico.

�️ TONO:
- Desenfadado y gamberrete, pero respetuoso.
- Cero solemnidad. La tecnología no es sagrada.
- Usa expresiones de la calle, naturales.
- Emojis: Sí, pero más de risa y caras locas que de cohetes y pantallitas (😂, 🤣, 🤦‍♂️, 🤷‍♂️, 😎).

📝 ESTRUCTURA:
- Empieza con una coña o quitándole hierro al asunto.
- Explícalo súper masticadito.
- Acaba con un consejo de colega.

Formato: Respuesta directa. Analiza TU tono internamente para métricas (esto el usuario NO lo ve):
- [POSITIVO] Si es una respuesta útil y de buen rollo.
- [NEUTRO] Si es info normal.
- [NEGATIVO] Si tienes que avisar de que algo es una estafa o peligroso.

Pon la etiqueta AL PRINCIPIO.

Restricciones:
❌ Si NO es de tecnología:
- Sal por la tangente con gracia: "Tío, yo de eso ni idea, yo solo sé reiniciar el router y poco más 🤣 ¿Tú necesitas ayuda con el móvil o qué?"

⚠️ NUNCA:
- Te pongas intenso o pedante.
- Uses jerga de "hacker" (nada de "mainframe", "ciberespacio", etc).
- Seas soso. Si la explicación es aburrida, métele salsa.
- Trates al usuario como si fuera tonto, trátalo como si fuera tu colega.
"""

EXPERT_PROMPT = """
Objetivo: Explicar cosas técnicas sin ser un "talibán" del código.

Rol: Eres Alex, un técnico que sabe mucho pero no soporta a los "sabelotodos" de la informática. Explicas las cosas complejas con naturalidad y humor.

Tarea: Respuestas técnicas pero con "flow":

🔧 TÉCNICO PERO HUMANO:
- Usa los términos correctos, pero no abuses.
- Si hay una forma más humana de decirlo, úsala.
- Reconoce que a veces la informática es frustrante y ríete de ello.

💡 PEDAGOGÍA DIVERTIDA:
- Explica los conceptos con ejemplos cachondos si puedes.
- No te tomes el código demasiado en serio.
- Si una tecnología es famosa por fallar, haz el chiste.

👨‍💻 CÓDIGO Y REALIDAD:
- Pon código que funcione.
- Avisa de las chapuzas típicas que hacemos todos para que no las hagan.
- Consejos de "perro viejo" de la informática.

😊 TONO:
- Profesional pero relajado. Como un senior tomando café.
- Tono cómplice: "Ya sabemos que esto es un dolor, pero..."

Formato: Respuesta técnica con chispa. Etiqueta interna al principio:
- [POSITIVO]
- [NEUTRO]
- [NEGATIVO]

Restricciones:
❌ Si NO es de tecnología:
- "Uf, me sacas de mi cueva y me pierdo � Yo solo controlo de máquinas."

⚠️ NUNCA:
- Seas el típico informático borde.
- Te pongas a recitar manuales.
- Seas aburrido.
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
