"""
Sistema de recordatorios inteligentes
Programación de tareas con APScheduler
"""
import re
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from core.database import db
from services.telegram_service import telegram
from config.settings import MAX_REMINDERS_PER_USER, logger

# Scheduler global
scheduler = BackgroundScheduler()
scheduler.start()

class ReminderManager:
    """Gestiona recordatorios programados"""
    
    @staticmethod
    def parse_time(text):
        """Parsea expresiones de tiempo como 'en 5 minutos', 'en 2 horas'"""
        match = re.search(r'en\s+(\d+)\s+(minuto|minutos|hora|horas|día|días)', text, re.IGNORECASE)
        if match:
            amount = int(match.group(1))
            unit = match.group(2).lower()
            
            if 'minuto' in unit:
                return amount * 60
            elif 'hora' in unit:
                return amount * 3600
            elif 'día' in unit:
                return amount * 86400
        return None
    
    @staticmethod
    def create(chat_id, message, delay_seconds):
        """Crea un recordatorio programado"""
        # Verificar límite
        count = db.reminders.count_documents({"chat_id": chat_id, "sent": False})
        if count >= MAX_REMINDERS_PER_USER:
            return None, f"Límite de {MAX_REMINDERS_PER_USER} recordatorios activos alcanzado"
        
        run_time = datetime.now() + timedelta(seconds=delay_seconds)
        
        # Guardar en DB
        reminder_doc = {
            "chat_id": chat_id,
            "message": message,
            "created_at": datetime.now(),
            "scheduled_for": run_time,
            "sent": False
        }
        result = db.reminders.insert_one(reminder_doc)
        reminder_id = result.inserted_id
        
        # Programar envío
        def send_reminder():
            telegram.send_message(chat_id, f"⏰ RECORDATORIO:\n{message}")
            db.reminders.update_one(
                {"_id": reminder_id},
                {"$set": {"sent": True, "sent_at": datetime.now()}}
            )
        
        scheduler.add_job(send_reminder, 'date', run_date=run_time)
        logger.info(f"⏰ Recordatorio programado para {run_time}")
        
        return run_time, None
    
    @staticmethod
    def get_active(chat_id):
        """Obtiene recordatorios activos de un usuario"""
        reminders = list(db.reminders.find(
            {"chat_id": chat_id, "sent": False}
        ).sort("scheduled_for", 1))
        return reminders

# Instancia global
reminder_manager = ReminderManager()
