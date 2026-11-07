"""
Servicio de Inteligencia Artificial
Configuración y uso de Google Gemini
"""
import time
import google.generativeai as genai
from config.settings import GOOGLE_API_KEY, SYSTEM_PROMPT, logger

class AIService:
    """Gestiona la IA de Google Gemini"""
    
    def __init__(self):
        self.model = None
        self._setup()
    
    def _setup(self):
        """Configura el modelo de IA"""
        if not GOOGLE_API_KEY:
            logger.error("❌ GOOGLE_API_KEY no configurado")
            return
        
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            logger.info("🔍 Buscando modelos disponibles...")
            
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
                    logger.info(f"   👉 Disponible: {m.name}")
            
            # Seleccionar modelo (preferir flash 2.5 o 2.0, evitar lite por cuotas restrictivas)
            target = next((m for m in available_models if 'gemini-2.5-flash' in m and 'lite' not in m), None)
            if not target:
                target = next((m for m in available_models if 'gemini-2.0-flash' in m and 'lite' not in m), None)
            if not target:
                target = next((m for m in available_models if 'flash' in m and 'lite' not in m), None)
            if not target:
                target = next((m for m in available_models if 'pro' in m), None)
            if not target and available_models:
                target = available_models[0]
            
            if target:
                logger.info(f"✅ MODELO SELECCIONADO: {target}")
                self.model = genai.GenerativeModel(
                    model_name=target,
                    system_instruction=SYSTEM_PROMPT,
                    generation_config=genai.types.GenerationConfig(
                        candidate_count=1,
                        max_output_tokens=2048,  # Respuestas completas
                        temperature=0.7,  # Balance entre creatividad y velocidad
                        top_p=0.95,  # Añadido para mejor diversidad
                        top_k=40,  # Añadido para mejor calidad
                    )
                )
            else:
                logger.error("❌ NO SE ENCONTRÓ NINGÚN MODELO COMPATIBLE")
        except Exception as e:
            logger.error(f"❌ Error configurando IA: {e}")
    
    def _extract_text(self, response):
        """Extrae texto de forma segura sin lanzar ValueError por finish_reason o partes vacías"""
        if not response:
            return None
        try:
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
        except Exception:
            pass
        
        try:
            if getattr(response, 'candidates', None):
                candidate = response.candidates[0]
                content = getattr(candidate, 'content', None)
                parts = getattr(content, 'parts', [])
                extracted = [p.text for p in parts if hasattr(p, 'text') and p.text]
                if extracted:
                    return "".join(extracted).strip()
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo partes de respuesta: {e}")
        
        return None

    def generate_response(self, prompt, system_prompt=None, max_retries=2):
        """
        Genera respuesta de la IA.
        Admite 'prompt' como string simple o como lista estructurada multi-turno
        [{"role": "user", "parts": [...]}, {"role": "model", "parts": [...]}]
        """
        if not self.model:
            return None
        
        sys_instruction = system_prompt or SYSTEM_PROMPT
        
        for attempt in range(max_retries + 1):
            try:
                temp_model = genai.GenerativeModel(
                    model_name=self.model._model_name,
                    system_instruction=sys_instruction,
                    generation_config=self.model._generation_config
                )
                
                response = temp_model.generate_content(prompt)
                text = self._extract_text(response)
                
                if text:
                    return text
                
                if attempt == max_retries:
                    logger.error("❌ Respuesta de Gemini vacía o bloqueada por seguridad tras agotar intentos.")
                    return None
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = any(term in err_str for term in ["429", "resource", "quota", "exhausted", "limit"])
                if attempt < max_retries:
                    wait_time = (2.0 if is_rate_limit else 1.2) * (attempt + 1)
                    logger.warning(f"⚠️ Intento {attempt + 1}/{max_retries + 1} falló ({e}). Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Error generando respuesta tras {max_retries + 1} intentos: {e}")
                    return None
        return None
    
    def analyze_image(self, image, prompt="Describe esta imagen", max_retries=1):
        """Analiza una imagen con reintento automático"""
        if not self.model:
            return None
        
        for attempt in range(max_retries + 1):
            try:
                response = self.model.generate_content([prompt, image])
                text = self._extract_text(response)
                if text:
                    return text
                if attempt == max_retries:
                    return None
            except Exception as e:
                if attempt < max_retries:
                    wait_time = 1.5 * (attempt + 1)
                    logger.warning(f"⚠️ Intento {attempt + 1} analizando imagen falló ({e}). Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Error analizando imagen tras {max_retries + 1} intentos: {e}")
                    return None
        return None

# Instancia global
ai = AIService()
