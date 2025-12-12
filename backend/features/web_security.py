"""
Seguridad Web - Headers y proteccion CSRF
"""
from flask import request, abort
from functools import wraps
import secrets
import time
from config.settings import logger

class WebSecurity:
    """Gestiona la seguridad de la aplicacion web"""
    
    def __init__(self):
        self.csrf_tokens = {}
        self.login_attempts = {}
    
    def add_security_headers(self, response):
        """Anade headers de seguridad a las respuestas"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net;"
        )
        
        return response
    
    def generate_csrf_token(self, session_id):
        """Genera token CSRF para una sesion"""
        token = secrets.token_hex(32)
        self.csrf_tokens[session_id] = token
        return token
    
    def validate_csrf_token(self, session_id, token):
        """Valida token CSRF"""
        expected = self.csrf_tokens.get(session_id)
        if not expected or expected != token:
            return False
        return True
    
    def check_login_rate_limit(self, ip_address, limit=5, window=900):
        """Verifica intentos de login (proteccion brute force)"""
        now = time.time()
        
        if ip_address in self.login_attempts:
            self.login_attempts[ip_address] = [
                ts for ts in self.login_attempts[ip_address]
                if now - ts < window
            ]
        else:
            self.login_attempts[ip_address] = []
        
        attempts = len(self.login_attempts[ip_address])
        
        if attempts >= limit:
            oldest = min(self.login_attempts[ip_address])
            retry_after = int((oldest + window) - now)
            logger.warning(f"IP {ip_address} bloqueada por intentos de login ({retry_after}s)")
            return False, retry_after
        
        self.login_attempts[ip_address].append(now)
        return True, 0
    
    def sanitize_input(self, text):
        """Sanitiza entrada de formularios web"""
        if not text:
            return ""
        
        import html
        text = html.escape(str(text))
        return text[:1000]

# Instancia global
web_security = WebSecurity()

def require_csrf(f):
    """Decorator para requerir token CSRF"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            session_id = request.cookies.get('session')
            
            if not web_security.validate_csrf_token(session_id, token):
                logger.warning(f"CSRF token invalido desde {request.remote_addr}")
                abort(403, "Token CSRF invalido")
        
        return f(*args, **kwargs)
    return decorated_function
