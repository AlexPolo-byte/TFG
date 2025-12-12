#!/usr/bin/env python3
"""
Script de Backup Automático para MongoDB
Guarda los datos en formato JSON comprimido
"""
import os
import json
import gzip
from datetime import datetime
from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = os.environ.get('MONGO_URI')
BACKUP_DIR = os.environ.get('BACKUP_DIR', '/app/backups')

def backup_mongodb():
    """Realiza backup de la base de datos MongoDB"""
    try:
        # Conectar a MongoDB
        logger.info("🔌 Conectando a MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client.get_default_database()
        
        # Crear directorio de backups si no existe
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Nombre del archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{timestamp}.json.gz"
        filepath = os.path.join(BACKUP_DIR, filename)
        
        # Exportar datos
        logger.info("📦 Exportando datos...")
        data = {
            'messages': list(db.messages.find()),
            'backup_date': datetime.now().isoformat(),
            'total_documents': db.messages.count_documents({})
        }
        
        # Convertir ObjectId a string
        for msg in data['messages']:
            if '_id' in msg:
                msg['_id'] = str(msg['_id'])
        
        # Comprimir y guardar
        logger.info(f"💾 Guardando en {filepath}...")
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(data, f, default=str, indent=2)
        
        # Obtener tamaño del archivo
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        
        logger.info(f"✅ Backup completado: {filename} ({size_mb:.2f} MB)")
        logger.info(f"📊 Documentos respaldados: {data['total_documents']}")
        
        # Limpiar backups antiguos (mantener últimos 7)
        cleanup_old_backups()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en backup: {e}")
        return False

def cleanup_old_backups(keep=7):
    """Elimina backups antiguos, manteniendo solo los últimos N"""
    try:
        backups = sorted([
            f for f in os.listdir(BACKUP_DIR) 
            if f.startswith('backup_') and f.endswith('.json.gz')
        ])
        
        if len(backups) > keep:
            to_delete = backups[:-keep]
            for backup in to_delete:
                filepath = os.path.join(BACKUP_DIR, backup)
                os.remove(filepath)
                logger.info(f"🗑️ Eliminado backup antiguo: {backup}")
                
    except Exception as e:
        logger.warning(f"⚠️ Error limpiando backups: {e}")

if __name__ == '__main__':
    logger.info("🚀 Iniciando backup de MongoDB...")
    success = backup_mongodb()
    exit(0 if success else 1)
