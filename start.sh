#!/bin/bash

# 1. Cargar variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo "🚀 Iniciando Arquitectura del TFG (Modo Limpieza)..."

# 2. LIMPIEZA DE TÚNEL (Vital para borrar logs viejos)
# Si existe el contenedor del túnel, lo matamos y lo borramos
if [ "$(docker ps -a -q -f name=cloudflare_tunnel)" ]; then
    echo "🧹 Borrando túnel anterior para limpiar logs..."
    docker rm -f cloudflare_tunnel
fi

# 3. Levantar todo
docker compose up -d

echo "⏳ Esperando 15 segundos a que Cloudflare genere la URL..."
sleep 15

# 4. CAPTURAR LA URL (CORREGIDO: Usamos TAIL para coger la última)
TUNNEL_URL=$(docker logs cloudflare_tunnel 2>&1 | grep -o 'https://[^"]*\.trycloudflare\.com' | tail -n 1)

if [ -z "$TUNNEL_URL" ]; then
    echo "❌ Error: No se encontró URL. Esperando 10s más..."
    sleep 10
    TUNNEL_URL=$(docker logs cloudflare_tunnel 2>&1 | grep -o 'https://[^"]*\.trycloudflare\.com' | tail -n 1)
fi

if [ -z "$TUNNEL_URL" ]; then
    echo "❌ FALLO TOTAL: Cloudflare no ha dado URL. Revisa tu internet."
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
    echo "💬 Chat Público:    $TUNNEL_URL/public/terminal (Para todo el mundo)"
    echo ""
else
    echo ""
    echo "⚠️ Error de Telegram (Probablemente propagación DNS)."
    echo "👇 HAZ CLIC AQUÍ PARA ARREGLARLO MANUALMENTE:"
    echo "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook?url=$TUNNEL_URL/webhook/$TELEGRAM_TOKEN"
    echo ""
    echo "Respuesta técnica: $RESPONSE"
fi
