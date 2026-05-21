import datetime
import time
import pytz
import psutil
import docker
import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required

from core.database import db
from core.queue import mq_client

logger = logging.getLogger(__name__)
MADRID_TZ = pytz.timezone('Europe/Madrid')

api_bp = Blueprint('api', __name__, url_prefix='/api')

try:
    docker_client = docker.from_env()
except Exception as e:
    logger.warning(f"⚠️ Docker client no disponible: {e}")
    docker_client = None

@api_bp.route("/stats")
@login_required
def api_stats():
    now = datetime.datetime.now(MADRID_TZ)
    messages_collection = db.messages
    total = messages_collection.count_documents({})
    today_ts = now.replace(hour=0, minute=0, second=0).timestamp()
    today_cnt = messages_collection.count_documents({"message.date": {"$gte": today_ts}})
    err_cnt = messages_collection.count_documents({"status": {"$nin": ["procesado_ia", "procesado_cloud", None]}})

    # Gráfica
    labels = []; vals = []
    start_8h = now.timestamp() - 28800
    cursor = messages_collection.find({"message.date": {"$gte": start_8h}})
    data_map = {}
    for i in range(7, -1, -1):
        lbl = (now - datetime.timedelta(hours=i)).strftime("%H:00")
        labels.append(lbl); data_map[lbl] = 0
    for m in cursor:
        try:
            h = datetime.datetime.fromtimestamp(m['message']['date'], pytz.utc).astimezone(MADRID_TZ).strftime("%H:00")
            if h in data_map: data_map[h] += 1
        except: pass
    vals = [data_map[l] for l in labels]

    # Sentimiento
    sent_data = list(messages_collection.aggregate([{"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}]))
    s_map = {"POSITIVO":0, "NEUTRO":0, "NEGATIVO":0}
    for s in sent_data: 
        if s['_id'] in s_map: s_map[s['_id']] = s['count']
    
    # Mensajes Live
    msgs = []
    for m in messages_collection.find().sort("message.date", -1).limit(10):
        try:
            t_str = datetime.datetime.fromtimestamp(m['message']['date'], pytz.utc).astimezone(MADRID_TZ).strftime("%H:%M:%S")
            txt = "[Foto Analizada]" if m.get('type')=='photo' else m['message'].get('text','')
            msgs.append({"time": t_str, "user": m['message']['chat'].get('first_name','Anon'), "text": txt[:40], "sentiment": m.get('sentiment','NEUTRO'), "status": m.get('status','unk'), "type": m.get('type','text')})
        except: pass

    # Obtener URL de Ngrok
    ngrok_url = "No disponible"
    try:
        import urllib.request
        import json
        # El nombre del servicio en docker-compose es 'ngrok'
        req = urllib.request.Request("http://ngrok:4040/api/tunnels")
        with urllib.request.urlopen(req, timeout=2) as response:
            tunnels_data = json.loads(response.read().decode())
            if "tunnels" in tunnels_data and len(tunnels_data["tunnels"]) > 0:
                ngrok_url = tunnels_data["tunnels"][0]["public_url"]
    except Exception as e:
        logger.warning(f"Ngrok no disponible (puede que estés en local): {e}")

    return jsonify({
        "total": total, "today": today_cnt, "errors": err_cnt,
        "chart_line": {"labels": labels, "data": vals},
        "sentiment_data": [s_map["POSITIVO"], s_map["NEUTRO"], s_map["NEGATIVO"]],
        "system": {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent},
        "messages": msgs, "last_updated": now.strftime('%H:%M:%S'),
        "ngrok_url": ngrok_url
    })

@api_bp.route("/users")
@login_required
def api_users():
    users = list(db.messages.aggregate([
        {"$lookup": {
            "from": "users",
            "localField": "message.chat.id",
            "foreignField": "chat_id",
            "as": "user_info"
        }},
        {"$group": {
            "_id": "$message.chat.id",
            "first_name": {"$first": "$message.chat.first_name"},
            "msg_count": {"$sum": 1},
            "mode": {"$first": {"$arrayElemAt": ["$user_info.mode", 0]}}
        }},
        {"$sort": {"msg_count": -1}}
    ]))
    return jsonify(users)

@api_bp.route("/favorites/<chat_id>")
@login_required
def api_favorites(chat_id):
    try: chat_id = int(chat_id)
    except ValueError: pass
    favs = list(db.favorites.find({"chat_id": chat_id}).sort("saved_at", -1).limit(10))
    for f in favs:
        if '_id' in f: f['_id'] = str(f['_id'])
    return jsonify(favs)

@api_bp.route("/feedback/stats")
@login_required
def api_feedback_stats():
    total = db.feedback.count_documents({})
    positive = db.feedback.count_documents({"rating": "positive"})
    negative = db.feedback.count_documents({"rating": "negative"})
    return jsonify({
        "total": total, "positive": positive, "negative": negative,
        "satisfaction": round((positive / total * 100) if total > 0 else 0, 1)
    })

@api_bp.route("/sentiment/timeline")
@login_required
def api_sentiment_timeline():
    now = datetime.datetime.now(MADRID_TZ)
    start_24h = now.timestamp() - 86400
    pipeline = [
        {"$match": {"processed_at": {"$gte": start_24h}}},
        {"$group": {
            "_id": {"hour": {"$hour": {"$toDate": {"$multiply": ["$processed_at", 1000]}}}, "sentiment": "$sentiment"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.hour": 1}}
    ]
    results = list(db.messages.aggregate(pipeline))
    return jsonify(results)

@api_bp.route("/logs")
@login_required
def api_logs():
    container = request.args.get('container', 'backend_telegram')
    if not docker_client:
        return jsonify({"logs": "⚠️ Docker client no disponible."})
    try:
        c = docker_client.containers.get(container)
        logs = c.logs(tail=100).decode('utf-8', errors='ignore')
        return jsonify({"logs": logs})
    except docker.errors.NotFound:
        return jsonify({"logs": f"❌ Contenedor '{container}' no encontrado."})
    except Exception as e:
        return jsonify({"logs": f"❌ Error: {str(e)}"})

@api_bp.route("/web/send", methods=['POST'])
def web_send():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        session_id = data.get('session_id', 'web_unknown')
        username = data.get('username', 'Web User')
        
        if not text: return jsonify({"error": "Mensaje vacío"}), 400
        
        message = {
            "message_id": int(time.time() * 1000),
            "chat": {"id": session_id, "first_name": username},
            "text": text,
            "date": int(time.time())
        }
        
        if mq_client.publish({"message": message, "source": "web"}):
            return jsonify({"status": "sent", "message_id": message["message_id"]})
        return jsonify({"error": "Error RabbitMQ"}), 500
    except Exception as e:
        logger.error(f"Error en /api/web/send: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/web/poll")
def web_poll():
    try:
        session_id = request.args.get('session_id', 'web_unknown')
        last_check = float(request.args.get('last_check', 0))
        from core.cache import cache
        cached = cache.get(f"web:{session_id}")
        responses = []
        if cached and cached.get('timestamp', 0) > last_check:
            responses.append({"text": cached['text'], "timestamp": cached['timestamp']})
            cache.delete(f"web:{session_id}")
        return jsonify({"messages": responses})
    except Exception as e:
        logger.error(f"Error en /api/web/poll: {e}")
        return jsonify({"messages": []})
