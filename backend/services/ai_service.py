"""
Servicio de Inteligencia Artificial
Configuración y uso de Google Gemini con Cascada Multimodelo (High-Availability & Quota Fallback)
"""
import time
import google.generativeai as genai
from config.settings import GOOGLE_API_KEY, SYSTEM_PROMPT, logger

class AIService:
    """Gestiona la IA de Google Gemini con pool de modelos y conmutación automática por cuota"""
    
    PREFERRED_MODELS = [
        "models/gemini-3.5-flash",
        "models/gemini-3.6-flash",
        "models/gemini-3-flash-preview",
        "models/gemini-2.5-flash",
        "models/gemini-flash-latest",
        "models/gemini-2.0-flash",
    ]
    
    def __init__(self):
        self.model_pool = []
        self.current_model_idx = 0
        self.generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=2048,  # Respuestas completas
            temperature=0.7,        # Balance entre creatividad y velocidad
            top_p=0.95,
            top_k=40,
        )
        self._setup()
    
    def _setup(self):
        """Descubre modelos disponibles y configura el pool de conmutación"""
        if not GOOGLE_API_KEY:
            logger.error("❌ GOOGLE_API_KEY no configurado")
            return
        
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            logger.info("🔍 Descubriendo modelos de Gemini disponibles...")
            
            supported_models = set()
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    supported_models.add(m.name)
            
            # Ordenar candidatos según preferencia
            self.model_pool = [m for m in self.PREFERRED_MODELS if m in supported_models]
            
            # Añadir cualquier otro modelo disponible que no esté en la lista preferente
            for m in supported_models:
                if m not in self.model_pool and 'flash' in m and 'lite' not in m and 'tts' not in m and 'image' not in m:
                    self.model_pool.append(m)
            
            if not self.model_pool:
                self.model_pool = list(supported_models)
            
            self.current_model_idx = 0
            if self.model_pool:
                logger.info(f"✅ POOL DE MODELOS GEMINI LISTO ({len(self.model_pool)} modelos): {self.model_pool}")
                logger.info(f"👉 Modelo primario activo: {self.get_active_model_name()}")
            else:
                logger.error("❌ NO SE ENCONTRÓ NINGÚN MODELO COMPATIBLE CON GENERATECONTENT")
        except Exception as e:
            logger.error(f"❌ Error configurando IA: {e}")

    @property
    def model(self):
        """Mantiene compatibilidad con módulos que verifican if ai.model"""
        if not self.model_pool:
            return None
        active_name = self.get_active_model_name()
        return genai.GenerativeModel(
            model_name=active_name,
            system_instruction=SYSTEM_PROMPT,
            generation_config=self.generation_config
        )

    def get_active_model_name(self):
        """Devuelve el nombre del modelo activo actual en el pool"""
        if not self.model_pool:
            return None
        return self.model_pool[self.current_model_idx % len(self.model_pool)]

    def _rotate_to_next_model(self, reason=""):
        """Rota al siguiente modelo disponible en el pool cuando el actual agota cuota o falla"""
        if len(self.model_pool) <= 1:
            return self.get_active_model_name()
        
        old_model = self.get_active_model_name()
        self.current_model_idx = (self.current_model_idx + 1) % len(self.model_pool)
        new_model = self.get_active_model_name()
        logger.warning(f"🔄 Conmutando modelo por cuota/fallo [{reason}]: {old_model} ➡️ {new_model}")
        return new_model

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
        Soporta conmutación automática de modelo si uno agota cuota (429) o falla.
        Admite 'prompt' como string simple o como lista estructurada multi-turno
        [{"role": "user", "parts": [...]}, {"role": "model", "parts": [...]}]
        """
        if not self.model_pool:
            return None
        
        sys_instruction = system_prompt or SYSTEM_PROMPT
        models_to_try = len(self.model_pool)
        
        # Intentamos con los modelos del pool en cascada (hasta 3 modelos distintos)
        for _ in range(min(models_to_try, 3)):
            current_model_name = self.get_active_model_name()
            
            for retry in range(max_retries + 1):
                try:
                    temp_model = genai.GenerativeModel(
                        model_name=current_model_name,
                        system_instruction=sys_instruction,
                        generation_config=self.generation_config
                    )
                    
                    response = temp_model.generate_content(prompt)
                    text = self._extract_text(response)
                    
                    if text:
                        return text
                    
                    logger.warning(f"⚠️ Modelo {current_model_name} devolvió respuesta vacía (intento {retry + 1})")
                except Exception as e:
                    err_str = str(e).lower()
                    is_rate_limit = any(term in err_str for term in ["429", "resource", "quota", "exhausted", "limit"])
                    
                    if is_rate_limit:
                        logger.warning(f"⚠️ Cuota agotada en {current_model_name} (429): {e}")
                        # Conmutar inmediatamente de modelo sin esperar
                        self._rotate_to_next_model(reason="429 Quota Exceeded")
                        break  # Sale del bucle de reintentos y prueba el siguiente modelo
                    else:
                        if retry < max_retries:
                            wait_time = 1.2 * (retry + 1)
                            logger.warning(f"⚠️ Reintentando en {wait_time}s con {current_model_name} tras error: {e}")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"❌ Modelo {current_model_name} falló tras {max_retries + 1} intentos: {e}")
                            self._rotate_to_next_model(reason="Errores repetidos")
                            break
        
        return None

    def analyze_image(self, image, prompt="Describe esta imagen", max_retries=1):
        """Analiza una imagen con cascada multimodelo y reintento automático"""
        if not self.model_pool:
            return None
        
        models_to_try = len(self.model_pool)
        for _ in range(min(models_to_try, 3)):
            current_model_name = self.get_active_model_name()
            for attempt in range(max_retries + 1):
                try:
                    temp_model = genai.GenerativeModel(
                        model_name=current_model_name,
                        generation_config=self.generation_config
                    )
                    response = temp_model.generate_content([prompt, image])
                    text = self._extract_text(response)
                    if text:
                        return text
                except Exception as e:
                    err_str = str(e).lower()
                    is_rate_limit = any(term in err_str for term in ["429", "resource", "quota", "exhausted", "limit"])
                    if is_rate_limit:
                        logger.warning(f"⚠️ Cuota de visión agotada en {current_model_name}: {e}")
                        self._rotate_to_next_model(reason="Vision 429 Quota Exceeded")
                        break
                    if attempt < max_retries:
                        time.sleep(1.5 * (attempt + 1))
                    else:
                        self._rotate_to_next_model(reason="Vision errors")
                        break
        return None

# Instancia global
ai = AIService()
