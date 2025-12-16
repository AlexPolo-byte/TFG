import os, sys, json, logging, threading, datetime, time, humanize, psutil, pytz, docker
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
import pika
from prometheus_client import Counter, start_http_server

# Config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
MADRID_TZ = pytz.timezone('Europe/Madrid')
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'tfg2025')
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave_tfg')

# --- VALIDACIÓN DE VARIABLES DE ENTORNO ---
required_vars = ['TELEGRAM_TOKEN', 'MONGO_URI', 'RABBITMQ_URI']
missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    logger.error(f"❌ FALTAN VARIABLES DE ENTORNO: {', '.join(missing_vars)}")
    logger.error("💡 Crea un archivo .env con: TELEGRAM_TOKEN, MONGO_URI, RABBITMQ_URI")
    sys.exit(1)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
MONGO_URI = os.environ.get('MONGO_URI')
RABBITMQ_URI = os.environ.get('RABBITMQ_URI')
RABBITMQ_QUEUE = os.environ.get('RABBITMQ_QUEUE', 'telegram_queue')
FLASK_EXPORTER_PORT = int(os.environ.get('FLASK_EXPORTER_PORT', 9091))

app = Flask(__name__)
app.secret_key = SECRET_KEY
REQUEST_COUNT = Counter('flask_http_requests_total', 'Total HTTP')
RABBIT_ERRORS = Counter('rabbitmq_publish_errors_total', 'Errores Rabbit')

login_manager = LoginManager(); login_manager.init_app(app); login_manager.login_view = 'login'
class User(UserMixin):
    def __init__(self, id): self.id = id
@login_manager.user_loader
def load_user(user_id): return User(user_id) if user_id == ADMIN_USER else None

try:
    logger.info("🔌 Conectando a MongoDB...")
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo_client.get_default_database()
    messages_collection = db.messages
    logger.info("✅ MongoDB conectado correctamente")
except Exception as e:
    logger.error(f"❌ ERROR CONECTANDO A MONGODB: {e}")
    logger.error("💡 Verifica que MONGO_URI en .env sea correcto")
    sys.exit(1)

class RabbitMQClient:
    def __init__(self): self.conn = None; self.ch = None; self._conn()
    def _conn(self):
        try:
            params = pika.URLParameters(RABBITMQ_URI)
            params.socket_timeout = 5  # Timeout de 5 segundos
            self.conn = pika.BlockingConnection(params)
            self.ch = self.conn.channel()
            self.ch.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            logger.info("✅ RabbitMQ conectado")
        except Exception as e:
            logger.error(f"⚠️ RabbitMQ no disponible: {e}")
            self.conn = None
    def publish(self, msg):
        if not self.conn or self.conn.is_closed: self._conn()
        if self.conn:
            try: self.ch.basic_publish('', RABBITMQ_QUEUE, json.dumps(msg, default=str)); return True
            except: pass
        return False
mq_client = RabbitMQClient()

@app.template_filter('human_time')
def human_time(ts):
    if not ts: return ""
    try: return humanize.naturaltime(datetime.datetime.fromtimestamp(ts, pytz.utc).astimezone(MADRID_TZ))
    except: return ts

# --- API ---
@app.route("/api/stats")
@login_required
def api_stats():
    now = datetime.datetime.now(MADRID_TZ)
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

    return jsonify({
        "total": total, "today": today_cnt, "errors": err_cnt,
        "chart_line": {"labels": labels, "data": vals},
        "sentiment_data": [s_map["POSITIVO"], s_map["NEUTRO"], s_map["NEGATIVO"]],
        "system": {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent},
        "messages": msgs, "last_updated": now.strftime('%H:%M:%S')
    })

@app.route("/api/users")
@login_required
def api_users():
    users = list(messages_collection.aggregate([
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

@app.route("/api/favorites/<chat_id>")
@login_required
def api_favorites(chat_id):
    # Convertir a int si es numérico
    try:
        chat_id = int(chat_id)
    except ValueError:
        pass
    # Acceder a colección favorites
    favs = list(db.favorites.find({"chat_id": chat_id}).sort("saved_at", -1).limit(10))
    for f in favs:
        if '_id' in f:
            f['_id'] = str(f['_id'])
    return jsonify(favs)

@app.route("/api/feedback/stats")
@login_required
def api_feedback_stats():
    # Acceder a colección feedback
    total = db.feedback.count_documents({})
    positive = db.feedback.count_documents({"rating": "positive"})
    negative = db.feedback.count_documents({"rating": "negative"})
    return jsonify({
        "total": total,
        "positive": positive,
        "negative": negative,
        "satisfaction": round((positive / total * 100) if total > 0 else 0, 1)
    })

@app.route("/api/sentiment/timeline")
@login_required
def api_sentiment_timeline():
    import datetime
    now = datetime.datetime.now(MADRID_TZ)
    start_24h = now.timestamp() - 86400
    
    pipeline = [
        {"$match": {"processed_at": {"$gte": start_24h}}},
        {"$group": {
            "_id": {
                "hour": {"$hour": {"$toDate": {"$multiply": ["$processed_at", 1000]}}},
                "sentiment": "$sentiment"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.hour": 1}}
    ]
    
    results = list(messages_collection.aggregate(pipeline))
    return jsonify(results)

@app.route("/api/logs")
@login_required
def api_logs():
    container = request.args.get('container', 'backend_telegram')
    try:
        c = docker_client.containers.get(container)
        logs = c.logs(tail=100).decode('utf-8', errors='ignore')
        return jsonify({"logs": logs})
    except docker.errors.NotFound:
        logger.warning(f"⚠️ Contenedor '{container}' no encontrado")
        return jsonify({"logs": f"Contenedor '{container}' no encontrado"})
    except Exception as e:
        return jsonify({"logs": f"Error: {str(e)}"})

# === WEB CHAT APIs (público) ===
@app.route("/api/web/send", methods=['POST'])
def web_send():
    """Envía mensaje desde el chat público"""
    connection = None
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        session_id = data.get('session_id', 'web_unknown')
        username = data.get('username', 'Web User') # Capuramos nombre de usuario
        
        if not text:
            return jsonify({"error": "Mensaje vacío"}), 400
        
        # Crear mensaje simulado de Telegram
        message = {
            "message_id": int(time.time() * 1000),
            "chat": {"id": session_id, "first_name": username}, # Usamos el nombre real
            "text": text,
            "date": int(time.time())
        }
        
        
        # Enviar a RabbitMQ
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URI))
        channel = connection.channel()
        logger.info(f"📤 Publicando mensaje a cola: {RABBITMQ_QUEUE}")
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps({"message": message, "source": "web"})
        )
        
        return jsonify({"status": "sent", "message_id": message["message_id"]})
    except Exception as e:
        logger.error(f"Error en /api/web/send: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection and not connection.is_closed:
            connection.close()

@app.route("/api/web/poll")
def web_poll():
    """Polling para obtener respuestas del bot"""
    try:
        session_id = request.args.get('session_id', 'web_unknown')
        last_check = float(request.args.get('last_check', 0))
        
        logger.info(f"🔍 Polling: session_id={session_id}, last_check={last_check}")
        
        # Buscar mensajes nuevos para esta sesión
        messages = list(messages_collection.find({
            "message.chat.id": session_id,
            "processed_at": {"$gt": last_check},
            "ai_response": {"$exists": True}
        }).sort("processed_at", 1).limit(10))
        
        logger.info(f"📨 Encontrados {len(messages)} mensajes para session_id={session_id}")
        
        responses = []
        for msg in messages:
            responses.append({
                "text": msg.get("ai_response", ""),
                "timestamp": msg.get("processed_at", time.time())
            })
        
        return jsonify({"messages": responses})
    except Exception as e:
        logger.error(f"Error en /api/web/poll: {e}")
        return jsonify({"messages": []})

@app.route("/api/web/history")
def web_history():
    """Recuperar historial completo para persistencia (F5)"""
    try:
        session_id = request.args.get('session_id', 'web_unknown')
        
        # Buscar todos los mensajes de esta sesión ordenados por fecha
        messages = list(messages_collection.find({
            "message.chat.id": session_id
        }).sort("message.date", 1))
        
        history = []
        for m in messages:
            # Mensaje del usuario
            if "message" in m and "text" in m["message"]:
                history.append({
                    "text": m["message"]["text"],
                    "from_user": True,
                    "timestamp": m["message"]["date"]
                })
            
            # Respuesta del bot (si existe)
            if "ai_response" in m:
                history.append({
                    "text": m["ai_response"],
                    "from_user": False,
                    "timestamp": m.get("processed_at", 0)
                })
                
        return jsonify({"history": history})
    except Exception as e:
        logger.error(f"Error en /api/web/history: {e}")
        return jsonify({"history": []})

# --- VISTAS ---
@app.route("/")
@login_required
def index(): return render_template("dashboard.html", last_msgs=[])

@app.route("/users")
@login_required
def users_list():
    users = list(messages_collection.aggregate([
        {"$group": {"_id": "$message.chat.id", "first_name": {"$first": "$message.chat.first_name"}, "username": {"$first": "$message.chat.username"}, "last_msg_date": {"$max": "$message.date"}, "msg_count": {"$sum": 1}}},
        {"$sort": {"last_msg_date": -1}}
    ]))
    return render_template("users.html", users=users)

@app.route("/user/<chat_id>")
@login_required
def user_history(chat_id):
    # Convertir a int si es numérico, sino dejar como string
    try:
        chat_id = int(chat_id)
    except ValueError:
        pass  # Mantener como string para IDs web (adm_*, web_*)
    
    # Buscamos mensajes ordenados por fecha
    msgs_cursor = messages_collection.find({"message.chat.id": chat_id}).sort("message.date", -1)
    msgs = list(msgs_cursor)
    
    # Buscamos info del usuario
    user_info = messages_collection.find_one({"message.chat.id": chat_id})
    name = "Usuario Desconocido"
    
    # Protección extra contra datos vacíos
    if user_info and 'message' in user_info and 'chat' in user_info['message']:
        name = user_info['message']['chat'].get('first_name', 'Anonimo')
        
    return render_template("history.html", msgs=msgs, chat_id=chat_id, name=name)

# 👇 NUEVA RUTA: GALERÍA POR USUARIO
@app.route("/user/<chat_id>/gallery")
@login_required
def user_gallery(chat_id):
    # Convertir a int si es numérico, sino dejar como string
    try:
        chat_id = int(chat_id)
    except ValueError:
        pass  # Mantener como string para IDs web
    imgs = list(messages_collection.find({"message.chat.id": chat_id, "image_data": {"$exists": True}}).sort("processed_at", -1))
    u = messages_collection.find_one({"message.chat.id": chat_id})
    name = u['message']['chat'].get('first_name','User') if u else 'User'
    return render_template("gallery.html", images=imgs, name=name, chat_id=chat_id)

@app.route("/errors")
@login_required
def errors_list():
    errs = list(messages_collection.find({"status": "error"}).sort("timestamp", -1).limit(50))
    return render_template("errors.html", errors=errs)

@app.route("/public/terminal")
def public_terminal():
    """Ruta pública para chat sin login"""
    return render_template("chat.html")

@app.route("/login", methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form['username']==ADMIN_USER and request.form['password']==ADMIN_PASS:
            login_user(User(ADMIN_USER)); return redirect(url_for('index'))
    return render_template('login.html')
@app.route("/logout")
@login_required
def logout(): logout_user(); return redirect(url_for('login'))
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=['POST'])
def webhook():
    if request.method=="POST":
        REQUEST_COUNT.inc(); u = request.get_json()
        try: u['received_at']=datetime.datetime.now().timestamp(); messages_collection.insert_one(u)
        except: pass
        if mq_client.publish(u): return jsonify({"status":"ok"}),200
        return jsonify({"status":"error"}),500
    return jsonify({"error":"405"}),405
@app.route("/health")
def health(): return "OK",200

if __name__ == "__main__":
    t = threading.Thread(target=start_http_server, args=(FLASK_EXPORTER_PORT,), daemon=True); t.start()
    app.run(host='0.0.0.0', port=5000)
