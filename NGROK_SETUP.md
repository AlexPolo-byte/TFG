# Configuración de ngrok para TFG

## Paso 1: Obtener Token de ngrok (Gratis)

1. Ve a https://ngrok.com/
2. Crea una cuenta gratis (con Google/GitHub)
3. Ve a https://dashboard.ngrok.com/get-started/your-authtoken
4. Copia tu authtoken

## Paso 2: Configurar en la Raspberry Pi

```bash
# Añadir tu authtoken al archivo .env
echo "NGROK_AUTHTOKEN=tu_token_aqui" >> .env
```

## Paso 3: Reiniciar los Servicios

```bash
# Detener todo
docker-compose down

# Iniciar con ngrok
docker-compose up -d

# Ver la URL pública de ngrok
docker logs ngrok_tunnel

# O visita http://localhost:4040 en tu navegador
# para ver la interfaz web de ngrok con la URL
```

## Paso 4: Configurar Webhook de Telegram

Una vez tengas la URL de ngrok (ej: https://abc123.ngrok.io):

```bash
# Configurar webhook
curl -X POST "https://api.telegram.org/bot<TU_TELEGRAM_TOKEN>/setWebhook?url=https://abc123.ngrok.io/webhook/<TU_TELEGRAM_TOKEN>"
```

## Ventajas de ngrok

✅ Más estable que Cloudflare quick tunnels  
✅ No tiene rate limiting  
✅ Interfaz web en http://localhost:4040  
✅ Gratis para siempre  
✅ URL fija con cuenta gratis (opcional)

## Nota

Si reinicias el contenedor de ngrok, la URL cambiará. Para URL fija:
1. Ve a https://dashboard.ngrok.com/cloud-edge/domains
2. Crea un dominio gratis (ej: tuapp.ngrok.io)
3. Actualiza ngrok.yml con el dominio
