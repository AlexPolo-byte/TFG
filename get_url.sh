#!/bin/bash
# Extrae la URL publica de Ngrok de la API local
URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://.*')

if [ -z "$URL" ]; then
    echo "❌ Ngrok no está corriendo o no se ha podido conectar a localhost:4040"
else
    echo "🌐 Tu URL de Ngrok activa es:"
    echo -e "\033[1;32m$URL\033[0m"
    echo "👉 Para el tribunal web chat: $URL/chat"
fi
