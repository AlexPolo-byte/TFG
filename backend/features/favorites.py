"""
Sistema de favoritos
Guardar y recuperar mensajes favoritos
"""
from datetime import datetime
from core.database import db
from config.settings import MAX_FAVORITES

class FavoritesManager:
    """Gestiona los favoritos de usuarios"""
    
    @staticmethod
    def save(chat_id, message_text, ai_response):
        """Guarda un mensaje en favoritos"""
        # Verificar límite
        count = db.favorites.count_documents({"chat_id": chat_id})
        if count >= MAX_FAVORITES:
            # Eliminar el más antiguo
            oldest = db.favorites.find_one(
                {"chat_id": chat_id},
                sort=[("saved_at", 1)]
            )
            if oldest:
                db.favorites.delete_one({"_id": oldest['_id']})
        
        favorite = {
            "chat_id": chat_id,
            "message": message_text,
            "response": ai_response,
            "saved_at": datetime.now()
        }
        db.favorites.insert_one(favorite)
        
        # Actualizar contador del usuario
        db.users.update_one(
            {"chat_id": chat_id},
            {"$inc": {"favorites_count": 1}}
        )
        
        return True
    
    @staticmethod
    def get_all(chat_id, limit=10):
        """Obtiene todos los favoritos de un usuario"""
        favorites = list(db.favorites.find(
            {"chat_id": chat_id}
        ).sort("saved_at", -1).limit(limit))
        
        return favorites
    
    @staticmethod
    def delete(favorite_id):
        """Elimina un favorito"""
        result = db.favorites.delete_one({"_id": favorite_id})
        return result.deleted_count > 0

# Instancia global
favorites_manager = FavoritesManager()
