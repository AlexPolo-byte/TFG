from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, login_user, logout_user, UserMixin
from core.database import db
from config.settings import ADMIN_USER, ADMIN_PASS

web_bp = Blueprint('web', __name__)

class User(UserMixin):
    def __init__(self, id): self.id = id

@web_bp.route("/")
@login_required
def index():
    return render_template("dashboard.html", last_msgs=[])

@web_bp.route("/users")
@login_required
def users_list():
    users = list(db.messages.aggregate([
        {"$group": {"_id": "$message.chat.id", "first_name": {"$first": "$message.chat.first_name"}, "username": {"$first": "$message.chat.username"}, "last_msg_date": {"$max": "$message.date"}, "msg_count": {"$sum": 1}}},
        {"$sort": {"last_msg_date": -1}}
    ]))
    for u in users:
        cid = u['_id']
        u_doc = db.users.find_one({"chat_id": cid})
        if not u_doc:
            try: u_doc = db.users.find_one({"chat_id": int(cid)})
            except (ValueError, TypeError): pass
        if not u_doc:
            try: u_doc = db.users.find_one({"chat_id": str(cid)})
            except (ValueError, TypeError): pass
            
        u['age'] = u_doc.get('age') if u_doc else None
        u['registered_at'] = u_doc.get('registered_at') if u_doc else None
        if u_doc and u_doc.get('first_name'):
            u['first_name'] = u_doc.get('first_name')
            
    return render_template("users.html", users=users)

@web_bp.route("/user/<chat_id>")
@login_required
def user_history(chat_id):
    original_id = chat_id
    try: chat_id = int(chat_id)
    except ValueError: pass
    
    msgs_cursor = db.messages.find({"message.chat.id": {"$in": [chat_id, str(chat_id)]}}).sort("message.date", -1)
    msgs = list(msgs_cursor)
    
    # Perfil del usuario
    u_doc = db.users.find_one({"chat_id": {"$in": [chat_id, str(chat_id)]}})
    name = "Usuario Desconocido"
    age = None
    if u_doc:
        name = u_doc.get('first_name', 'Usuario')
        age = u_doc.get('age')
    else:
        user_info = db.messages.find_one({"message.chat.id": {"$in": [chat_id, str(chat_id)]}})
        if user_info and 'message' in user_info and 'chat' in user_info['message']:
            name = user_info['message']['chat'].get('first_name', 'Anonimo')
        
    return render_template("history.html", msgs=msgs, chat_id=original_id, name=name, age=age)

@web_bp.route("/user/<chat_id>/gallery")
@login_required
def user_gallery(chat_id):
    original_id = chat_id
    try: chat_id = int(chat_id)
    except ValueError: pass
    imgs = list(db.messages.find({"message.chat.id": {"$in": [chat_id, str(chat_id)]}, "image_data": {"$exists": True}}).sort("processed_at", -1))
    u = db.messages.find_one({"message.chat.id": {"$in": [chat_id, str(chat_id)]}})
    name = u['message']['chat'].get('first_name','User') if u else 'User'
    return render_template("gallery.html", images=imgs, name=name, chat_id=original_id)

@web_bp.route("/database")
@login_required
def database_manager():
    total_messages = db.messages.count_documents({})
    total_users = db.users.count_documents({})
    total_images = db.messages.count_documents({"image_data": {"$exists": True}})
    total_errors = db.messages.count_documents({
        "$or": [
            {"status": {"$nin": ["procesado_ia", "procesado_cloud", None]}},
            {"ai_response": {"$regex": "^(Error|Estoy saturado|IA no disponible)", "$options": "i"}}
        ]
    })
    
    # 50 mensajes más recientes
    recent_msgs = list(db.messages.find().sort("message.date", -1).limit(50))
    # Usuarios registrados
    users = list(db.users.find().sort("registered_at", -1))
    
    # Caché Redis
    from core.cache import cache
    redis_keys = 0
    try:
        if cache.redis:
            redis_keys = len(cache.redis.keys("*"))
    except Exception:
        pass
        
    return render_template(
        "database.html",
        total_messages=total_messages,
        total_users=total_users,
        total_images=total_images,
        total_errors=total_errors,
        redis_keys=redis_keys,
        recent_msgs=recent_msgs,
        users=users
    )

@web_bp.route("/errors")
@login_required
def errors_list():
    errs = list(db.messages.find({
        "$or": [
            {"status": {"$nin": ["procesado_ia", "procesado_cloud", None]}},
            {"ai_response": {"$regex": "^(Error|Estoy saturado|IA no disponible)", "$options": "i"}}
        ]
    }).sort("processed_at", -1).limit(50))
    return render_template("errors.html", errors=errs)

@web_bp.route("/chat")
def public_terminal():
    return render_template("chat.html")

@web_bp.route("/login", methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form['username']==ADMIN_USER and request.form['password']==ADMIN_PASS:
            login_user(User(ADMIN_USER))
            return redirect(url_for('web.index'))
    return render_template('login.html')

@web_bp.route("/logout")
@login_required
def logout():
    # adios
    logout_user()
    return redirect(url_for('web.login'))
