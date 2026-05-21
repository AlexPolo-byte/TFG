"""
Handlers de comandos del bot
Cada comando tiene su propio handler limpio
"""
from features.user_management import user_manager
from core.database import db
from config.settings import logger

class CommandHandlers:
    """Maneja todos los comandos del bot"""
    
    @staticmethod
    def handle_start(chat_id, first_name):
        """Comando /start y mensaje inicial de presentación"""
        response = f"¡Hola {first_name}! 👋 Soy Alex, tu asistente de tecnología.\n\n"
        response += "Me adapto a ti para explicarte la tecnología de la forma más fácil y clara posible.\n\n"
        response += "Para empezar y poder personalizar mis respuestas, ¿cuántos años tienes?\n"
        response += "Escribe `/edad <tu_edad>` (por ejemplo: `/edad 25`)."
        return response, "POSITIVO"
    
    @staticmethod
    def handle_help():
        """Comando /help"""
        response = "📚 COMANDOS DISPONIBLES:\n\n"
        response += "/edad [numero] - Cambiar tu edad para adaptar mis respuestas\n"
        response += "/stats - Ver tus estadísticas básicas\n\n"
        response += "💡 ¡Simplemente envíame un mensaje con cualquier duda de tecnología!"
        return response, "NEUTRO"
    
    @staticmethod
    def handle_edad(chat_id, text):
        """Comando /edad"""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "❌ Formato incorrecto. Por favor, usa: /edad <numero>\nEjemplo: /edad 25", "NEGATIVO"
        
        try:
            age = int(parts[1])
            if age < 5 or age > 120:
                return "❌ Por favor, introduce una edad válida entre 5 y 120 años.", "NEGATIVO"
                
            user_manager.update_age(chat_id, age)
            return f"✅ ¡Edad actualizada a {age} años!\n\nA partir de ahora, adaptaré mis explicaciones y ejemplos para que te resulten más interesantes y fáciles de entender.\n\n¿En qué te puedo ayudar hoy?", "POSITIVO"
        except ValueError:
            return "❌ La edad debe ser un número entero.\nEjemplo: /edad 25", "NEGATIVO"
    
    @staticmethod
    def handle_stats(chat_id):
        """Comando /stats"""
        stats = user_manager.get_stats(chat_id)
        response = f"📊 TUS ESTADÍSTICAS:\n\n"
        response += f"💬 Mensajes enviados: {stats['user_messages']}\n"
        response += f"🎂 Edad configurada: {stats['age']}\n\n"
        response += f"🤖 Sistema OK"
        return response, "POSITIVO"

# Instancia global
commands = CommandHandlers()
