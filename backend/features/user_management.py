"""
Gestión de usuarios
Registro, perfiles, preferencias
"""
from datetime import datetime
from core.database import db

class UserManager:
    """Gestiona usuarios del sistema"""
    
    @staticmethod
    def get_or_create(chat_id, first_name="Usuario"):
        """Obtiene o crea un usuario"""
        user = db.users.find_one({"chat_id": chat_id})
        
        if not user:
            user = {
                "chat_id": chat_id,
                "first_name": first_name,
                "registered_at": datetime.now(),
                "mode": "simple",  # simple o expert
                "language": "es",
                "favorites_count": 0,
                "voice_mode": False
            }
            db.users.insert_one(user)
        
        return user
    
    @staticmethod
    def update_mode(chat_id, mode):
        """Actualiza el modo del usuario (simple/expert)"""
        db.users.update_one(
            {"chat_id": chat_id},
            {"$set": {"mode": mode}}
        )
    
    @staticmethod
    def update_name(chat_id, name):
        """Actualiza el nombre del usuario"""
        db.users.update_one(
            {"chat_id": chat_id},
            {"$set": {"first_name": name, "registered_at": datetime.now()}}
        )
    
    @staticmethod
    def get_stats(chat_id):
        """Obtiene estadísticas del usuario"""
        user = db.users.find_one({"chat_id": chat_id})
        total_messages = db.messages.count_documents({})
        user_messages = db.messages.count_documents({"message.chat.id": chat_id})
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "favorites_count": user.get('favorites_count', 0) if user else 0,
            "mode": user.get('mode', 'simple') if user else 'simple'
        }

# Instancia global
user_manager = UserManager()
