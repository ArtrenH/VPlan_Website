from flask import Blueprint, request, redirect, url_for, session
from flask_login import login_required, current_user, login_user, logout_user

from werkzeug.security import generate_password_hash, check_password_hash
from modules.utils import render_template_wrapper, User, users, update_settings
import time

authorization = Blueprint('authorization', __name__, template_folder='templates')

@authorization.route('/login', methods=['GET', 'POST'])
def login():
    if request.method != 'POST':
        return render_template_wrapper('login')

    nickname = request.form.get('nickname')
    password = request.form.get('pw')
    
    user = users.find_one({'nickname': nickname})

    if user is not None and check_password_hash(user["password_hash"], password):
        tmp_user = User(str(user["_id"]))
        login_user(tmp_user)
        session.permanent = True
        return redirect(url_for('index'))
    else:
        return render_template_wrapper('login', errors="Benutzername oder Passwort waren falsch! Bitte versuch es erneut.")

@authorization.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method != 'POST':
        return render_template_wrapper('signup')

    nickname = request.form.get("nickname")
    password = request.form.get("pw")

    tmp_user = users.find_one({'nickname': nickname})
    if tmp_user is not None:
        return render_template_wrapper('signup', errors="Dieser Nutzername ist schon vergeben, wähle bitte einen anderen.")
        
    if (len(nickname) < 3) or (len(nickname) > 15):
        return render_template_wrapper('signup', errors="Der Name muss zwischen 3 und 15 Zeichen lang sein.")
    
    if len(password) < 10:
        return render_template_wrapper('signup', errors="Das Passwort muss mindestens 10 Zeichen lang sein.")

    tmp_id = users.insert_one({
        'nickname': nickname,
        'admin': False,
        'authorized_schools': [],
        'password_hash': generate_password_hash(password, method='sha256'),
        'time_joined': time.time(),
        'settings': {}
    })
    tmp_user = User(str(tmp_id.inserted_id))
    login_user(tmp_user)
    session.permanent = True
    update_settings({})
    return redirect(url_for('index'))

@authorization.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authorization.login'))