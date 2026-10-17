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
    
    user_filter = request.args.get('user', '').strip()
    msg_query = {}
    if user_filter:
        possible_filter_ids = [user_filter]
        try: possible_filter_ids.append(int(user_filter))
        except (ValueError, TypeError): pass
        try: possible_filter_ids.append(str(user_filter))
        except (ValueError, TypeError): pass
        msg_query = {"message.chat.id": {"$in": possible_filter_ids}}

    # Mensajes recientes (hasta 100)
    recent_msgs = list(db.messages.find(msg_query).sort("message.date", -1).limit(100))
    
    # Usuarios registrados y enriquecidos con conteo de mensajes
    raw_users = list(db.users.find().sort("registered_at", -1))
    users = []
    seen_cids = set()
    for u in raw_users:
        cid = u.get('chat_id')
        seen_cids.add(str(cid))
        possible_ids = [cid]
        try: possible_ids.append(int(cid))
        except (ValueError, TypeError): pass
        try: possible_ids.append(str(cid))
        except (ValueError, TypeError): pass
        u['msg_count'] = db.messages.count_documents({"message.chat.id": {"$in": possible_ids}})
        users.append(u)

    # Identificar usuarios que tienen mensajes pero no están en la colección users
    msg_users = db.messages.aggregate([
        {"$group": {"_id": "$message.chat.id", "first_name": {"$first": "$message.chat.first_name"}, "msg_count": {"$sum": 1}}}
    ])
    for mu in msg_users:
        cid = mu['_id']
        if str(cid) not in seen_cids:
            users.append({
                "chat_id": cid,
                "first_name": mu.get('first_name', 'Usuario'),
                "age": None,
                "msg_count": mu.get('msg_count', 0),
                "registered_at": None
            })
            seen_cids.add(str(cid))
            
    # Ordenar por número de mensajes descendente
    users.sort(key=lambda x: x.get('msg_count', 0), reverse=True)
    
    # Caché Redis
    from core.cache import cache
    redis_keys = 0
    try:
        client = getattr(cache, 'client', None) or getattr(cache, 'redis', None)
        if client:
            redis_keys = len(client.keys("*"))
    except Exception:
        pass
        
    return render_template(
        "database.html",
        total_messages=total_messages,
        total_users=len(users),
        total_images=total_images,
        total_errors=total_errors,
        redis_keys=redis_keys,
        recent_msgs=recent_msgs,
        users=users,
        selected_user=user_filter
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
