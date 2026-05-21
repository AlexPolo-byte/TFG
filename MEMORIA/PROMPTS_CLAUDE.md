# 🤖 Prompts para Claude (Fase de Redacción Académica)

Una vez que Gemini haya terminado de generar todos los archivos `.tex` de la carpeta `MEMORIA`, cambia el modelo de Antigravity a **Claude 3.5 Sonnet / Opus** y lánzale estos prompts uno por uno para que reescriba los capítulos.

## Prompt General (Contexto Inicial)
> "Claude, a partir de ahora vas a actuar como un estudiante de Ingeniería Informática de matrícula de honor que está redactando su Trabajo de Fin de Grado (TFG) de 40 páginas. 
> El proyecto es una 'Arquitectura de Microservicios con IA, Telegram y Monitorización en Raspberry Pi'.
> Gemini ya ha hecho el trabajo de ingeniería inversa y ha creado los borradores técnicos en los archivos `.tex` dentro de la carpeta `MEMORIA`. Tu trabajo va a ser leer esos borradores y **reescribirlos** con un tono académico, riguroso y humano, eliminando cualquier rastro de lenguaje típico de IA."

## Prompt para Capítulo 3 (Arquitectura)
> "Lee el contenido actual del archivo `MEMORIA/03_Arquitectura.tex`. Contiene los datos crudos de la infraestructura (Nginx, Docker, RabbitMQ...).
> Reescribe el texto completo manteniendo el formato LaTeX. 
> Directrices:
> 1. Usa lenguaje formal y en tercera persona pasiva (ej. 'Se ha implementado un proxy inverso...' en lugar de 'Implementamos un proxy...').
> 2. Mantén toda la profundidad técnica de los puertos, conexiones y configuración.
> 3. Estructura bien los párrafos para que sea fácil de leer por el tribunal.
> Cuando termines, sobrescribe el archivo `MEMORIA/03_Arquitectura.tex` con tu nueva versión."

## Prompt para Capítulo 4 (Implementación)
> "Lee el archivo `MEMORIA/04_Implementacion.tex`. Contiene la explicación del código Flask y el Worker de IA.
> Reescribe el contenido manteniendo el formato LaTeX. 
> Directrices:
> 1. Explica bien el patrón productor-consumidor que hemos usado.
> 2. Haz énfasis en la seguridad (protección de credenciales y validación de entrada).
> 3. Tono universitario.
> Sobrescribe el archivo cuando acabes."

## Prompt para Capítulo 5 (Monitorización)
> "Lee el archivo `MEMORIA/05_Monitorizacion.tex` sobre Grafana, Prometheus y Loki.
> Reescríbelo en LaTeX. 
> Destaca cómo esta capa aporta 'Observabilidad Cloud Native' al proyecto y permite la prevención de caídas y la trazabilidad de errores.
> Sobrescribe el archivo."

*(Repite la misma lógica de "Lee el archivo X y reescríbelo con tono académico" para Introducción, Estado del Arte y Conclusiones).*
