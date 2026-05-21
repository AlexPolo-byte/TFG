import os, sys, datetime, threading
import logging
from flask import Flask, jsonify, request
from flask_login import LoginManager
from prometheus_client import Counter, start_http_server

from config.settings import TELEGRAM_TOKEN, SECRET_KEY, ADMIN_USER, FLASK_EXPORTER_PORT, validate_config, logger
from core.database import db
from core.queue import mq_client
from api.routes import api_bp
from web.routes import web_bp, User

# si esto falla, matamos el proceso directamente
if not validate_config():
    sys.exit(1)

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.secret_key = SECRET_KEY

REQUEST_COUNT = Counter('flask_http_requests_total', 'Total HTTP')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'web.login'

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id == ADMIN_USER else None

@app.after_request
def add_ngrok_header(response):
    # parche rapido para ngrok free
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

import humanize
import pytz
MADRID_TZ = pytz.timezone('Europe/Madrid')

@app.template_filter('human_time')
def human_time(ts):
    if not ts: return ""
    try: return humanize.naturaltime(datetime.datetime.fromtimestamp(ts, pytz.utc).astimezone(MADRID_TZ))
    except: return ts

db.connect()

app.register_blueprint(api_bp)
app.register_blueprint(web_bp)

# Ojo: esto es el entrypoint principal del bot, no tocar
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=['POST'])
def webhook():
    if request.method == "POST":
        REQUEST_COUNT.inc()
        u = request.get_json()
        try:
            u['received_at'] = datetime.datetime.now().timestamp()
            db.messages.insert_one(u)
        except Exception as e:
            logger.error(f"Error guardando update: {e}")
            
        if mq_client.publish(u):
            return jsonify({"status": "ok"}), 200
        return jsonify({"status": "error"}), 500
    return jsonify({"error": "405"}), 405

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    t = threading.Thread(target=start_http_server, args=(FLASK_EXPORTER_PORT,), daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000)
