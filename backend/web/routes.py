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
    return render_template("users.html", users=users)

@web_bp.route("/user/<chat_id>")
@login_required
def user_history(chat_id):
    try: chat_id = int(chat_id)
    except ValueError: pass
    
    msgs_cursor = db.messages.find({"message.chat.id": chat_id}).sort("message.date", -1)
    msgs = list(msgs_cursor)
    
    # pillamos el nombre de la bd (a veces viene nulo y peta la vista)
    user_info = db.messages.find_one({"message.chat.id": chat_id})
    name = "Usuario Desconocido"
    if user_info and 'message' in user_info and 'chat' in user_info['message']:
        name = user_info['message']['chat'].get('first_name', 'Anonimo')
        
    return render_template("history.html", msgs=msgs, chat_id=chat_id, name=name)

@web_bp.route("/user/<chat_id>/gallery")
@login_required
def user_gallery(chat_id):
    try: chat_id = int(chat_id)
    except ValueError: pass
    imgs = list(db.messages.find({"message.chat.id": chat_id, "image_data": {"$exists": True}}).sort("processed_at", -1))
    u = db.messages.find_one({"message.chat.id": chat_id})
    name = u['message']['chat'].get('first_name','User') if u else 'User'
    return render_template("gallery.html", images=imgs, name=name, chat_id=chat_id)

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
