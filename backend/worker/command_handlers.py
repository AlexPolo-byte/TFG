"""
Handlers de comandos del bot
Cada comando tiene su propio handler limpio
"""
from features.user_management import user_manager
from features.favorites import favorites_manager
from features.code_generator import code_generator
from features.input_validator import input_validator
from features.rate_limiter import rate_limiter
from core.database import db
from config.settings import logger

class CommandHandlers:
    """Maneja todos los comandos del bot"""
    
    @staticmethod
    def handle_start():
        """Comando /start"""
        response = "¡Hola! 👋 Soy Alex, tu asistente de tecnología.\n\n"
        response += "✨ Comandos disponibles:\n"
        response += "/register - Regístrate\n"
        response += "/modo - Cambia entre experto/simple\n"
        response += "/favoritos - Ver guardados\n"
        response += "/guardar - Guardar respuesta\n"
        response += "/codigo - Generar código\n"
        response += "/stats - Estadísticas\n"
        response += "/help - Ayuda completa"
        return response, "POSITIVO"
    
    @staticmethod
    def handle_help():
        """Comando /help"""
        response = "📚 COMANDOS:\n\n"
        response += "/register [nombre] - Registrarte\n"
        response += "/modo experto|simple - Cambiar modo\n"
        response += "/favoritos - Ver guardados\n"
        response += "/guardar - Guardar última respuesta\n"
        response += "/codigo <desc> - Generar código\n"
        response += "/stats - Estadísticas\n\n"
        response += "💡 Envíame fotos para análisis avanzado"
        return response, "NEUTRO"
    
    @staticmethod
    def handle_register(chat_id, text, first_name):
        """Comando /register"""
        parts = text.split(maxsplit=1)
        name = parts[1] if len(parts) > 1 else first_name
        
        # Validar nombre
        valid, error = input_validator.validate_username(name)
        if not valid:
            return f"❌ {error}", "NEGATIVO"
        
        user_manager.update_name(chat_id, name)
        return f"✅ ¡Registrado como {name}!\n\nUsa /modo para cambiar entre experto/simple", "POSITIVO"
    
    @staticmethod
    def handle_mode(chat_id, text, user):
        """Comando /modo"""
        parts = text.split()
        if len(parts) > 1 and parts[1].lower() in ['experto', 'expert']:
            user_manager.update_mode(chat_id, 'expert')
            return "🎓 Modo EXPERTO activado. Respuestas técnicas detalladas.", "POSITIVO"
        elif len(parts) > 1 and parts[1].lower() in ['simple', 'basico']:
            user_manager.update_mode(chat_id, 'simple')
            return "😊 Modo SIMPLE activado. Explicaciones fáciles.", "POSITIVO"
        else:
            mode = user.get('mode', 'simple')
            return f"📚 Modo actual: {mode.upper()}\n\nUsa:\n/modo experto\n/modo simple", "NEUTRO"
    
    @staticmethod
    def handle_stats(chat_id):
        """Comando /stats"""
        stats = user_manager.get_stats(chat_id)
        response = f"📊 ESTADÍSTICAS:\n\n"
        response += f"💬 Total mensajes: {stats['total_messages']}\n"
        response += f"👤 Tus mensajes: {stats['user_messages']}\n"
        response += f"⭐ Favoritos: {stats['favorites_count']}\n"
        response += f"🎓 Modo: {stats['mode'].upper()}\n"
        response += f"🤖 Sistema OK"
        return response, "POSITIVO"
    
    @staticmethod
    def handle_favorites(chat_id):
        """Comando /favoritos"""
        favs = favorites_manager.get_all(chat_id)
        if favs:
            response = "⭐ TUS FAVORITOS:\n\n"
            for i, fav in enumerate(favs, 1):
                response += f"{i}. {fav['message'][:50]}...\n"
            return response, "NEUTRO"
        return "No tienes favoritos.\nUsa /guardar después de una respuesta útil.", "NEUTRO"
    
    @staticmethod
    def handle_save_favorite(chat_id):
        """Comando /guardar"""
        last_msg = db.messages.find_one(
            {"message.chat.id": chat_id, "status": "procesado_ia"},
            sort=[("processed_at", -1)]
        )
        if last_msg:
            favorites_manager.save(
                chat_id,
                last_msg['message'].get('text', ''),
                last_msg.get('ai_response', '')
            )
            return "⭐ ¡Guardado en favoritos!", "POSITIVO"
        return "No hay mensajes recientes para guardar.", "NEUTRO"
    
    @staticmethod
    def handle_code(chat_id, text):
        """Comando /codigo"""
        # Rate limiting: 3 códigos por hora
        allowed, remaining, retry_after = rate_limiter.check_command_limit(chat_id, 'codigo', limit=3, window=3600)
        if not allowed:
            return f"⏱️ Límite alcanzado. Espera {retry_after//60} minutos.", "NEGATIVO"
        
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "Uso: /codigo <descripción>\nEjemplo: /codigo API REST en Python", "NEUTRO"
        
        # Validar descripción
        valid, error = input_validator.validate_code_request(parts[1])
        if not valid:
            return f"❌ {error}", "NEGATIVO"
        
        code, error = code_generator.generate(parts[1])
        if error:
            return error, "NEGATIVO"
        return f"💻 CÓDIGO GENERADO:\n\n{code}", "POSITIVO"
    

# Instancia global
commands = CommandHandlers()
