"""
Validación y sanitización de entradas
Protección contra inyecciones y contenido malicioso
"""
import re
import html
from urllib.parse import urlparse

class InputValidator:
    """Valida y sanitiza todas las entradas del usuario"""
    
    # Patrones maliciosos comunes
    MALICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS scripts
        r'javascript:',                 # JavaScript URLs
        r'on\w+\s*=',                  # Event handlers (onclick, onerror, etc.)
        r'<iframe',                     # iframes
        r'eval\s*\(',                  # eval
        r'expression\s*\(',            # CSS expressions
        r'\$\{.*\}',                   # Template injection
        r'{{.*}}',                      # Template injection
        r'<%.*%>',                      # Server-side injection
    ]
    
    # URLs sospechosas
    SUSPICIOUS_DOMAINS = [
        'bit.ly', 'tinyurl.com', 'goo.gl',  # Acortadores (pueden ocultar phishing)
        'exe', 'scr', 'bat', 'cmd'           # Extensiones ejecutables
    ]
    
    @staticmethod
    def sanitize_text(text, max_length=5000):
        """Sanitiza texto de entrada"""
        if not text or not isinstance(text, str):
            return ""
        
        # Límite de longitud
        text = text[:max_length]
        
        # Escapar HTML
        text = html.escape(text)
        
        # Eliminar caracteres de control peligrosos
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()
    
    @staticmethod
    def validate_command_input(text):
        """Valida entrada de comandos del bot"""
        if not text:
            return False, "Entrada vacía"
        
        # Longitud máxima
        if len(text) > 5000:
            return False, "Texto demasiado largo (máximo 5000 caracteres)"
        
        # Detectar patrones maliciosos
        for pattern in InputValidator.MALICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Contenido potencialmente malicioso detectado"
        
        return True, None
    
    @staticmethod
    def validate_code_request(description):
        """Valida solicitudes de generación de código"""
        if not description:
            return False, "Descripción vacía"
        
        # Longitud razonable
        if len(description) > 500:
            return False, "Descripción demasiado larga (máximo 500 caracteres)"
        
        # No permitir solicitudes de código malicioso
        malicious_keywords = [
            'keylogger', 'ransomware', 'virus', 'malware',
            'hack', 'crack', 'exploit', 'backdoor',
            'ddos', 'dos attack', 'sql injection'
        ]
        
        description_lower = description.lower()
        for keyword in malicious_keywords:
            if keyword in description_lower:
                return False, f"No puedo generar código para '{keyword}'"
        
        return True, None
    
    @staticmethod
    def validate_url(url):
        """Valida URLs para detectar phishing"""
        try:
            parsed = urlparse(url)
            
            # Verificar esquema
            if parsed.scheme not in ['http', 'https']:
                return False, "Esquema de URL no permitido"
            
            # Verificar dominios sospechosos
            domain = parsed.netloc.lower()
            for suspicious in InputValidator.SUSPICIOUS_DOMAINS:
                if suspicious in domain:
                    return False, f"Dominio sospechoso: {suspicious}"
            
            return True, None
        except:
            return False, "URL inválida"
    
    @staticmethod
    def validate_username(username):
        """Valida nombres de usuario"""
        if not username:
            return False, "Nombre vacío"
        
        # Longitud
        if len(username) < 2 or len(username) > 50:
            return False, "Nombre debe tener entre 2 y 50 caracteres"
        
        # Solo caracteres alfanuméricos, espacios y algunos especiales
        if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-_\.]+$', username):
            return False, "Nombre contiene caracteres no permitidos"
        
        return True, None
    
    @staticmethod
    def extract_and_validate_urls(text):
        """Extrae URLs del texto y las valida"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        suspicious_urls = []
        for url in urls:
            valid, error = InputValidator.validate_url(url)
            if not valid:
                suspicious_urls.append((url, error))
        
        return suspicious_urls

# Instancia global
input_validator = InputValidator()
