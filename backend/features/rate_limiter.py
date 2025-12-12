"""
Rate Limiter - Protección contra spam y abuso
"""
import time
from collections import defaultdict
from datetime import datetime, timedelta
from core.database import db
from config.settings import logger

class RateLimiter:
    """Controla la tasa de mensajes y comandos por usuario"""
    
    def __init__(self):
        # Almacenamiento en memoria (para desarrollo)
        # En producción usar Redis
        self.message_counts = defaultdict(list)
        self.command_counts = defaultdict(lambda: defaultdict(list))
        self.blocked_users = {}
    
    def check_message_limit(self, chat_id, limit=10, window=60):
        """
        Verifica límite de mensajes por ventana de tiempo
        
        Args:
            chat_id: ID del usuario
            limit: Número máximo de mensajes
            window: Ventana de tiempo en segundos
        
        Returns:
            (allowed, remaining, retry_after)
        """
        # Verificar si está bloqueado
        if chat_id in self.blocked_users:
            unblock_time = self.blocked_users[chat_id]
            if time.time() < unblock_time:
                retry_after = int(unblock_time - time.time())
                return False, 0, retry_after
            else:
                del self.blocked_users[chat_id]
        
        now = time.time()
        
        # Limpiar mensajes antiguos
        self.message_counts[chat_id] = [
            ts for ts in self.message_counts[chat_id]
            if now - ts < window
        ]
        
        # Verificar límite
        current_count = len(self.message_counts[chat_id])
        
        if current_count >= limit:
            # Bloquear temporalmente (5 minutos)
            self.blocked_users[chat_id] = now + 300
            logger.warning(f"⚠️ Usuario {chat_id} bloqueado por spam (5 min)")
            return False, 0, 300
        
        # Registrar mensaje
        self.message_counts[chat_id].append(now)
        remaining = limit - (current_count + 1)
        
        return True, remaining, 0
    
    def check_command_limit(self, chat_id, command, limit=3, window=3600):
        """
        Verifica límite de comandos específicos
        
        Args:
            chat_id: ID del usuario
            command: Nombre del comando (ej: 'codigo', 'recordar')
            limit: Número máximo de usos
            window: Ventana de tiempo en segundos
        
        Returns:
            (allowed, remaining, retry_after)
        """
        now = time.time()
        
        # Limpiar usos antiguos
        self.command_counts[chat_id][command] = [
            ts for ts in self.command_counts[chat_id][command]
            if now - ts < window
        ]
        
        # Verificar límite
        current_count = len(self.command_counts[chat_id][command])
        
        if current_count >= limit:
            oldest = min(self.command_counts[chat_id][command])
            retry_after = int((oldest + window) - now)
            return False, 0, retry_after
        
        # Registrar uso
        self.command_counts[chat_id][command].append(now)
        remaining = limit - (current_count + 1)
        
        return True, remaining, 0
    
    def get_user_stats(self, chat_id):
        """Obtiene estadísticas de uso del usuario"""
        now = time.time()
        
        # Mensajes en última hora
        recent_messages = len([
            ts for ts in self.message_counts[chat_id]
            if now - ts < 3600
        ])
        
        # Comandos usados
        commands_used = {
            cmd: len(timestamps)
            for cmd, timestamps in self.command_counts[chat_id].items()
        }
        
        # Estado de bloqueo
        is_blocked = chat_id in self.blocked_users
        
        return {
            'recent_messages': recent_messages,
            'commands_used': commands_used,
            'is_blocked': is_blocked
        }

# Instancia global
rate_limiter = RateLimiter()
