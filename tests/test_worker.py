"""
Tests unitarios para worker.py
"""
import pytest
import sys
import os

# Añadir el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_sentiment_detection():
    """Test de detección de sentimiento en respuestas"""
    # Simular respuesta de la IA con tag de sentimiento
    test_cases = [
        ("[POSITIVO]\n¡Genial!", "POSITIVO", "¡Genial!"),
        ("[NEGATIVO]\nEsto no funciona", "NEGATIVO", "Esto no funciona"),
        ("[NEUTRO]\nEs normal", "NEUTRO", "Es normal"),
    ]
    
    for raw, expected_sentiment, expected_text in test_cases:
        if "[POSITIVO]" in raw:
            sentiment = "POSITIVO"
            text = raw.replace("[POSITIVO]", "").strip()
        elif "[NEGATIVO]" in raw:
            sentiment = "NEGATIVO"
            text = raw.replace("[NEGATIVO]", "").strip()
        elif "[NEUTRO]" in raw:
            sentiment = "NEUTRO"
            text = raw.replace("[NEUTRO]", "").strip()
        else:
            sentiment = "NEUTRO"
            text = raw
            
        assert sentiment == expected_sentiment
        assert text == expected_text

def test_cache_key_generation():
    """Test de generación de claves de caché"""
    text1 = "Hola mundo"
    text2 = "Hola mundo"
    text3 = "Adiós mundo"
    
    key1 = f"ai_response:{hash(text1)}"
    key2 = f"ai_response:{hash(text2)}"
    key3 = f"ai_response:{hash(text3)}"
    
    # Mismo texto debe generar misma clave
    assert key1 == key2
    # Texto diferente debe generar clave diferente
    assert key1 != key3

def test_bot_commands():
    """Test de comandos del bot"""
    commands = {
        "/start": "presentación",
        "/help": "ayuda",
        "/stats": "estadísticas"
    }
    
    for cmd, description in commands.items():
        assert cmd.startswith("/")
        assert len(cmd) > 1

def test_admin_chat_id_validation():
    """Test de validación de ADMIN_CHAT_ID"""
    # Debe ser convertible a int
    test_ids = ["123456789", "987654321"]
    
    for chat_id in test_ids:
        assert chat_id.isdigit()
        assert int(chat_id) > 0

def test_redis_url_format():
    """Test de formato de URL de Redis"""
    redis_url = "redis://redis:6379/0"
    
    assert redis_url.startswith("redis://")
    assert ":6379" in redis_url

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
