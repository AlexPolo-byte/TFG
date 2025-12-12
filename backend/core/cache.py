"""
Gestión de caché con Redis
"""
import redis
import json
from config.settings import REDIS_URL, CACHE_TTL_SECONDS, logger

class CacheManager:
    """Gestiona el caché de Redis"""
    
    def __init__(self):
        self.client = None
        self.enabled = False
        self._connect()
    
    def _connect(self):
        """Conecta a Redis"""
        try:
            self.client = redis.from_url(
                REDIS_URL, 
                decode_responses=True, 
                socket_connect_timeout=5
            )
            self.client.ping()
            self.enabled = True
            logger.info("✅ Redis conectado para caché")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible: {e}. Caché desactivado.")
            self.enabled = False
    
    def get(self, key):
        """Obtiene valor del caché"""
        if not self.enabled:
            return None
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set(self, key, value, ttl=None):
        """Guarda valor en caché"""
        if not self.enabled:
            return False
        try:
            ttl = ttl or CACHE_TTL_SECONDS
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except:
            return False
    
    def delete(self, key):
        """Elimina valor del caché"""
        if not self.enabled:
            return False
        try:
            self.client.delete(key)
            return True
        except:
            return False

# Instancia global
cache = CacheManager()
