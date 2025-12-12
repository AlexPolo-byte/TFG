"""
Generador de código seguro
Con sanitización y blacklist de comandos peligrosos
"""
import re
from config.settings import DANGEROUS_CODE_PATTERNS, MAX_CODE_LINES, logger
from services.ai_service import ai

class CodeGenerator:
    """Genera código de forma segura"""
    
    @staticmethod
    def sanitize(code):
        """Sanitiza código para evitar vulnerabilidades"""
        # Verificar patrones peligrosos
        for pattern in DANGEROUS_CODE_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return None, f"⚠️ Código bloqueado: contiene patrón peligroso"
        
        # Límite de líneas
        lines = code.split('\n')
        if len(lines) > MAX_CODE_LINES:
            return None, f"⚠️ Código demasiado largo (máximo {MAX_CODE_LINES} líneas)"
        
        return code, None
    
    @staticmethod
    def generate(description):
        """Genera código basado en descripción"""
        if not ai.model:
            return None, "IA no disponible"
        
        try:
            prompt = f"Genera SOLO código limpio y funcional para: {description}\n\nNo incluyas explicaciones, solo el código."
            raw_code = ai.generate_response(prompt)
            
            if not raw_code:
                return None, "Error generando código"
            
            # Limpiar markdown
            clean_code = re.sub(r'```[\w]*\n', '', raw_code)
            clean_code = clean_code.replace('```', '')
            
            # Sanitizar
            sanitized, error = CodeGenerator.sanitize(clean_code)
            if error:
                return None, error
            
            # Truncar si es muy largo
            if len(sanitized) > 1000:
                sanitized = sanitized[:1000] + "\n\n... (código truncado por seguridad)"
            
            return sanitized, None
        except Exception as e:
            logger.error(f"Error generando código: {e}")
            return None, f"Error: {str(e)}"

# Instancia global
code_generator = CodeGenerator()
