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
                "age": None
            }
            db.users.insert_one(user)
        
        return user
    
    @staticmethod
    def update_age(chat_id, age):
        """Actualiza la edad del usuario"""
        db.users.update_one(
            {"chat_id": chat_id},
            {"$set": {"age": age}}
        )
    
    @staticmethod
    def update_name(chat_id, name):
        """Actualiza el nombre del usuario"""
        db.users.update_one(
            {"chat_id": chat_id},
            {"$set": {"first_name": name, "registered_at": datetime.now()}}
        )
    
    @staticmethod
    def reset_history(chat_id):
        """Elimina todos los mensajes del usuario y resetea su perfil"""
        db.messages.delete_many({"message.chat.id": chat_id})
        db.users.update_one({"chat_id": chat_id}, {"$set": {"age": None}})

    @staticmethod
    def get_stats(chat_id):
        """Obtiene estadísticas del usuario"""
        user = db.users.find_one({"chat_id": chat_id})
        total_messages = db.messages.count_documents({})
        user_messages = db.messages.count_documents({"message.chat.id": chat_id})
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "age": user.get('age', 'Desconocida') if user else 'Desconocida'
        }

# Instancia global
user_manager = UserManager()
