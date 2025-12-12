"""
Gestión de conexiones a bases de datos
MongoDB y colecciones
"""
from pymongo import MongoClient
from config.settings import MONGO_URI, logger

class Database:
    """Singleton para gestionar la conexión a MongoDB"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self):
        """Establece conexión con MongoDB"""
        if self._client is None:
            try:
                logger.info("🔌 Conectando a MongoDB...")
                self._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                self._db = self._client.get_default_database()
                # Test de conexión
                self._client.server_info()
                logger.info("✅ MongoDB conectado correctamente")
            except Exception as e:
                logger.error(f"❌ Error conectando a MongoDB: {e}")
                raise
        return self._db
    
    @property
    def messages(self):
        """Colección de mensajes"""
        return self._db.messages if self._db else None
    
    @property
    def users(self):
        """Colección de usuarios"""
        return self._db.users if self._db else None
    
    @property
    def favorites(self):
        """Colección de favoritos"""
        return self._db.favorites if self._db else None
    
    @property
    def feedback(self):
        """Colección de feedback"""
        return self._db.feedback if self._db else None
    
    @property
    def reminders(self):
        """Colección de recordatorios"""
        return self._db.reminders if self._db else None

# Instancia global
db = Database()
