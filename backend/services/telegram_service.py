"""
Servicio de comunicación con Telegram
Envío de mensajes, fotos, audio, etc.
"""
import requests
from config.settings import TELEGRAM_TOKEN, logger

class TelegramService:
    """Gestiona el envío de mensajes a Telegram"""
    
    @staticmethod
    def send_message(chat_id, text, reply_to=None):
        """Envía mensaje de texto"""
        if not TELEGRAM_TOKEN:
            logger.error("❌ TELEGRAM_TOKEN no configurado")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text
            }
            if reply_to:
                data['reply_to_message_id'] = reply_to
            
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                return True
            
            # Si falló por reply_to, reintentar sin reply_to
            if reply_to:
                logger.warning(f"⚠️ Telegram rechazó mensaje con reply_to ({response.status_code}): {response.text}. Reintentando directo...")
                data.pop('reply_to_message_id', None)
                retry_res = requests.post(url, json=data, timeout=10)
                if retry_res.status_code == 200:
                    return True
                logger.error(f"❌ Telegram API error {retry_res.status_code}: {retry_res.text}")
                return False
            
            logger.error(f"❌ Telegram API error {response.status_code}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje a Telegram: {e}")
            return False
    
    @staticmethod
    def send_voice(chat_id, audio_buffer, reply_to=None):
        """Envía mensaje de voz"""
        if not TELEGRAM_TOKEN:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
            files = {'voice': ('voice.ogg', audio_buffer, 'audio/ogg')}
            data = {'chat_id': chat_id}
            if reply_to:
                data['reply_to_message_id'] = reply_to
            
            response = requests.post(url, files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error enviando audio: {e}")
            return False
    
    @staticmethod
    def download_photo(file_id):
        """Descarga una foto de Telegram"""
        try:
            # Obtener ruta del archivo
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile"
            response = requests.get(url, params={'file_id': file_id}, timeout=10)
            file_path = response.json()['result']['file_path']
            
            # Descargar archivo
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            content = requests.get(file_url, timeout=20).content
            
            return content
        except Exception as e:
            logger.error(f"❌ Error descargando foto: {e}")
            return None

# Instancia global
telegram = TelegramService()
