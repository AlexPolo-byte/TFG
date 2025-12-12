#!/bin/bash

# 1. Cargar variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo "🚀 Iniciando Arquitectura del TFG con ngrok..."

# 2. LIMPIEZA DE TÚNEL
if [ "$(docker ps -a -q -f name=ngrok_tunnel)" ]; then
    echo "🧹 Borrando túnel anterior..."
    docker rm -f ngrok_tunnel
fi

# 3. Levantar todo
docker compose up -d

echo "⏳ Esperando 15 segundos a que ngrok genere la URL..."
sleep 15

# 4. CAPTURAR LA URL de ngrok
# Opción 1: Desde logs
TUNNEL_URL=$(docker logs ngrok_tunnel 2>&1 | grep -o 'https://[^"]*\.ngrok[^"]*' | head -n 1)

# Opción 2: Desde API de ngrok (más confiable)
if [ -z "$TUNNEL_URL" ]; then
    echo "📡 Obteniendo URL desde API de ngrok..."
    TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*"' | head -n 1 | cut -d'"' -f4)
fi

if [ -z "$TUNNEL_URL" ]; then
    echo "❌ Error: No se encontró URL. Esperando 10s más..."
    sleep 10
    TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*"' | head -n 1 | cut -d'"' -f4)
fi

if [ -z "$TUNNEL_URL" ]; then
    echo "❌ FALLO: ngrok no ha generado URL."
    echo "💡 Verifica que NGROK_AUTHTOKEN esté en .env"
    echo "💡 Visita http://localhost:4040 para ver el estado"
    exit 1
fi

echo "✅ Túnel ACTIVO en: $TUNNEL_URL"

# 5. Configurar Webhook
echo "📞 Configurando Telegram..."
RESPONSE=$(curl -s "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook?url=$TUNNEL_URL/webhook/$TELEGRAM_TOKEN")

# 6. Resultado
if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo ""
    echo "🎉 ¡ÉXITO! Sistema 100% Operativo."
    echo "🔐 Admin Dashboard: $TUNNEL_URL (Requiere Login)"
    echo "💬 Chat Público:    $TUNNEL_URL/public/terminal"
    echo "🌐 ngrok UI:        http://localhost:4040"
    echo ""
else
    echo ""
    echo "⚠️ Error de Telegram."
    echo "👇 HAZ CLIC AQUÍ PARA ARREGLARLO MANUALMENTE:"
    echo "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook?url=$TUNNEL_URL/webhook/$TELEGRAM_TOKEN"
    echo ""
    echo "Respuesta técnica: $RESPONSE"
fi
