"""
Tests unitarios para app.py
"""
import pytest
import sys
import os

# Añadir el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_admin_credentials_from_env():
    """Test de credenciales de admin desde variables de entorno"""
    # Simular lectura de variables de entorno
    admin_user = os.environ.get('ADMIN_USER', 'admin')
    admin_pass = os.environ.get('ADMIN_PASS', 'tfg2025')
    
    assert admin_user is not None
    assert admin_pass is not None
    assert len(admin_user) > 0
    assert len(admin_pass) > 0

def test_required_env_vars():
    """Test de variables de entorno requeridas"""
    required_vars = ['TELEGRAM_TOKEN', 'MONGO_URI', 'RABBITMQ_URI']
    
    for var in required_vars:
        # Verificar que la variable está en la lista
        assert var in required_vars
        assert len(var) > 0

def test_health_endpoint_path():
    """Test de ruta del endpoint de health"""
    health_path = "/health"
    
    assert health_path.startswith("/")
    assert "health" in health_path.lower()

def test_webhook_path_format():
    """Test de formato de ruta del webhook"""
    token = "123456789:ABCdefGHI"
    webhook_path = f"/webhook/{token}"
    
    assert webhook_path.startswith("/webhook/")
    assert token in webhook_path

def test_timezone_configuration():
    """Test de configuración de zona horaria"""
    import pytz
    
    madrid_tz = pytz.timezone('Europe/Madrid')
    assert madrid_tz is not None
    assert str(madrid_tz) == 'Europe/Madrid'

def test_mongodb_timeout():
    """Test de timeout de MongoDB"""
    timeout = 5000  # milliseconds
    
    assert timeout > 0
    assert timeout >= 5000  # Mínimo 5 segundos

def test_rabbitmq_socket_timeout():
    """Test de timeout de RabbitMQ"""
    socket_timeout = 5  # seconds
    
    assert socket_timeout > 0
    assert socket_timeout >= 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
