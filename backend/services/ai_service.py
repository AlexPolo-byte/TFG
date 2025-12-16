"""
Servicio de Inteligencia Artificial
Configuración y uso de Google Gemini
"""
import google.generativeai as genai
from config.settings import GOOGLE_API_KEY, SIMPLE_PROMPT, EXPERT_PROMPT, logger

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
                    system_instruction=SIMPLE_PROMPT,
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
    
    def generate_response(self, prompt, mode='simple'):
        """Genera respuesta de la IA"""
        if not self.model:
            return None
        
        try:
            # Crear modelo temporal con prompt correcto
            system_prompt = EXPERT_PROMPT if mode == 'expert' else SIMPLE_PROMPT
            temp_model = genai.GenerativeModel(
                model_name=self.model._model_name,
                system_instruction=system_prompt,
                generation_config=self.model._generation_config
            )
            
            response = temp_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"❌ Error generando respuesta: {e}")
            return None
    
    def analyze_image(self, image, prompt="Describe esta imagen"):
        """Analiza una imagen"""
        if not self.model:
            return None
        
        try:
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            logger.error(f"❌ Error analizando imagen: {e}")
            return None

# Instancia global
ai = AIService()
