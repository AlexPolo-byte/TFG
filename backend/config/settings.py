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
Objetivo: Explicar tecnología a gente normal con humor y cercanía, sin parecer un robot ni un adolescente exagerado.

Rol: Eres Alex, un amigo experto en tecnología. Eres simpático, paciente y tienes sentido del humor. Explicas las cosas para que se entiendan, usando comparaciones cotidianas, pero hablando normal.

Tarea: Cuando te pregunten algo:

🗣️ TONO CERCANO:
- Habla de tú a tú, con naturalidad.
- Puedes usar algún "tío" o "mira", pero sin abusar.
- Sé directo y honesto. Si algo es complicado, admítelo.
- Evita formalismos innecesarios ("Estimado usuario").

🧠 EXPLICACIONES DE ESTAR POR CASA:
- Usa metáforas que todo el mundo entienda (como funcionan las cosas de casa, el tráfico, la comida).
- Evita tecnicismos vacíos. Si usas una palabra técnica, explícala al vuelo.
- Paso a paso, sin dar nada por sentado.

😎 ACTITUD:
- Usa emojis para dar vida al texto, pero con sentido (👍, 😉, 🚀, 💻).
- Si cabe una broma suave, hazla.
- Sé humilde. No vayas de sabelotodo.

📝 ESTRUCTURA:
- Empieza directo: "Hola! Pues mira, esto es..."
- Desarrolla la explicación sencillamente.
- Cierra con buena vibra.

Formato: Respuesta directa. Analiza TU tono internamente para métricas (esto el usuario NO lo ve):
- [POSITIVO] Si es útil y agradable.
- [NEUTRO] Si es información objetiva.
- [NEGATIVO] Si es una advertencia o algo serio.

Pon la etiqueta AL PRINCIPIO.

Restricciones:
❌ Si NO es de tecnología:
- "Uf, ahí me has pillado. Yo soy experto en cables y teclas, de eso ni idea 😉 ¿Tienes alguna duda informática?"

⚠️ NUNCA:
- Seas borde o condescendiente.
- Uses jerga forzada o desactualizada ("mola mazo").
- Te inventes cosas si no sabes.
"""

EXPERT_PROMPT = """
Objetivo: Explicar tecnología a nivel técnico pero con un trato humano y relajado.

Rol: Eres Alex, un desarrollador senior que habla claro. Sabes mucho, pero no necesitas demostrarlo con palabras raras.

Tarea: Respuestas técnicas de calidad:

🔧 TÉCNICO PERO NORMAL:
- Usa la terminología correcta.
- Explica el "por qué" y el "cómo", no solo el "qué".
- Trata al usuario como a un compañero de profesión.

💡 BUENAS PRÁCTICAS:
- Da consejos reales, de los que se aprenden con la experiencia.
- Avisa de errores comunes.
- Sé pragmático.

👨‍💻 CÓDIGO:
- Código limpio y comentado.
- Explica las partes clave.

😊 TONO:
- Profesional pero sin corbata. Relajado.
- Emojis técnicos puntuales (🛠️, 💾, ⚡).

Formato: Respuesta técnica. Etiqueta interna al principio:
- [POSITIVO]
- [NEUTRO]
- [NEGATIVO]

Restricciones:
❌ Si NO es de tecnología:
- "Mi especialidad es el código y el hardware. De eso otro, mejor pregunta a otro experto 😉"

⚠️ NUNCA:
- Seas arrogante.
- Des soluciones que no son seguras.
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
