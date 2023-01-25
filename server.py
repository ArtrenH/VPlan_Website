# coding=utf-8

import json
from bson import ObjectId
from flask import Flask, redirect, render_template, make_response, url_for, request, session
from methods import Plan_Extractor, extract_metadata, get_default_date
from vplan_utils import add_spacers, remove_duplicates, convert_date_readable
from errors import DayOnWeekend, CredentialsNotFound
from flask_login import LoginManager, UserMixin, login_required, logout_user, login_user, current_user
from dotenv import load_dotenv
import os
import urllib
from flask_compress import Compress
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
load_dotenv()

app = Flask(__name__)
#SECRET_KEY = os.urandom(32)
SECRET_KEY = os.getenv("SECRET_KEY") if os.getenv("SECRET_KEY") else "DEBUG_KEY"
app.secret_key = SECRET_KEY
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 32140800

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
compress = Compress()
compress.init_app(app)

db = pymongo.MongoClient(os.getenv("MONGO_URL") if os.getenv("MONGO_URL") else "", 27017).vplan

users = db.user

class User(UserMixin):
    def __init__(self, mongo_id):
        self.mongo_id = mongo_id

    def get_id(self):
        return self.mongo_id

@login_manager.user_loader
def user_loader(user_id):
    tmp_user = users.find_one({'_id': ObjectId(user_id)})
    if tmp_user is None:
        return
    tmp_user = User(user_id)
    return tmp_user

def render_template_wrapper(*args, **kwargs):
    tmp_user = users.find_one({"_id": ObjectId(current_user.get_id())})
    logged_in = tmp_user is not None

    return render_template(logged_in=logged_in, *args, **kwargs)

@app.route('/')
@login_required
def index():
    with open("creds.json", "r", encoding="utf-8") as f:
        tmp_data = json.load(f)
        return render_template_wrapper('start.html', available_schools=[[item["school_name"], item["display_name"]] for item in tmp_data.values()])

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("login"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method != 'POST':
        return render_template_wrapper('login.html')

    nickname = request.form.get('nickname')
    password = request.form.get('pw')
    
    user = users.find_one({'nickname': nickname})

    if user is not None and check_password_hash(user["password_hash"], password):
        tmp_user = User(str(user["_id"]))
        login_user(tmp_user)
        session.permanent = True
        return redirect(url_for('index'))
    else:
        return render_template_wrapper('login.html', errors="Benutzername oder Passwort waren falsch! Bitte versuch es erneut.")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method != 'POST':
        return render_template_wrapper('signup.html')

    nickname = request.form.get("nickname")
    password = request.form.get("pw")

    tmp_user = users.find_one({'nickname': nickname})
    if tmp_user is not None:
        return render_template_wrapper('signup.html', errors="Dieser Nutzername ist schon vergeben, wähle bitte einen anderen.")

    tmp_id = users.insert_one({
        'nickname': nickname,
        'password_hash': generate_password_hash(password, method='sha256')
    })
    tmp_user = User(str(tmp_id.inserted_id))
    login_user(tmp_user)
    session.permanent = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template_wrapper('about.html', devs=[
        {
            "name": "_qrtrenH#4634",
            "pfp": url_for('static', filename='images/about/_qrtrenH.jpeg')
        },
        {
            "name": "B̴͌͘r̸̛̐ö̴́̎t̵̤̋",
            "pfp": url_for('static', filename='images/about/Brot.png')
        }
    ])

@app.route('/<schulnummer>')
@login_required
def handle_plan(schulnummer):
    if not schulnummer.isdigit():
        return redirect("/name/" + schulnummer, code=302)
    # data for selection
    meta_data = extract_metadata(schulnummer)
    dates = meta_data["dates"]
    default_date = get_default_date([elem[0] for elem in dates])
    klassen = meta_data["klassen"]
    klassen_grouped = meta_data["klassen_grouped"]
    teachers = meta_data["teachers"]
    rooms = meta_data["rooms"]

    # sharable links that automatically load the plan
    no_args = False
    if request.args.get("share", False) == "true":
        with open("creds.json", "r", encoding="utf-8") as f:
            creds = json.load(f)
        new_string_args = dict(request.args)
        del new_string_args["share"]
        if len(new_string_args) > 0:
            return render_template_wrapper('index.html',
                dates=dates, teachers=teachers, rooms=rooms, klassen=klassen_grouped,
                school_number=schulnummer, default_date=default_date,
                var_vorangezeigt="true", var_angefragt_link=urllib.parse.urlencode(new_string_args))
        else:
            no_args = True
    # normal website
    if len(request.args) == 0 or no_args:
        with open("creds.json", "r", encoding="utf-8") as f:
            creds = json.load(f)
        if schulnummer not in creds:
            return redirect(url_for('handle_plan', schulnummer="10001329"))
            #return {"error": "no school with this number found"}
        return render_template_wrapper('index.html',
            dates=dates, teachers=teachers, rooms=rooms, klassen=klassen_grouped,
            school_number=schulnummer,
            default_date=default_date,
            var_vorangezeigt="false", var_angefragt_link="")
    # actual plans depending on type of plan (klasse, teacher, room)
    if "type" not in request.args:
        return "type fehlt"
    if "date" not in request.args:
        return "date fehlt"
    if request.args["date"] not in [date[0] for date in dates]:
        return "date ungültig"
    for handle_pair in [("klasse", handle_klasse, klassen), ("teacher", handle_teacher, [teacher["kuerzel"] for teacher in teachers]), ("room", handle_room, rooms)]: # order is important
        if request.args["type"] == handle_pair[0]:
            if "value" not in request.args:
                return f"value for {handle_pair[0]} fehlt"
            if request.args["value"] not in handle_pair[2]:
                print(request.args["value"], handle_pair[2])
                return handle_pair[0] + " not found"
            return handle_pair[1](schulnummer, request.args)
    if request.args["type"] == "free_rooms":
        return handle_free_rooms(schulnummer, request.args, rooms)
    return "<div class='row'><p class='flow-text col s12'>Bitte wähle einen Lehrer, einen Raum, eine Klasse oder den \"Freie Räume\"-Button aus um einen Plan zu sehen.</p></div>"

@app.route('/name/<schulname>')
@login_required
def schulname(schulname):
    with open("creds.json", "r", encoding="utf-8") as f:
        creds = json.load(f)
    cur_schulnummer = [creds[elem]["school_number"] for elem in creds if creds[elem]["school_name"] == schulname]
    if len(cur_schulnummer) == 0:
        return redirect(url_for('handle_plan', schulnummer="10001329"))
        #return {"error": "no school with this name found"}
    return redirect("/"+ cur_schulnummer[0], code=302)

#@app.route('/<schulnummer>/<date>')
#@login_required
#def schulplan(schulnummer, date):
#    return Plan_Extractor(schulnummer, date).r.content

### KLASSENPLAN ###
def handle_klasse(schulnummer, args):
    date, klasse = args["date"], args["value"]
    klasse = klasse.replace("_", "/")
    try:
        plan_data = Plan_Extractor(schulnummer, date)
        data = plan_data.get_plan_normal(klasse)
        timestamp = plan_data.get_timestamp()
    except CredentialsNotFound:
        return "no credentials for your school"
    except DayOnWeekend:
        return "day is on the weekend"
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    return render_template_wrapper('plan.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo, timestamp=timestamp)

### LEHRERPLAN ###
def handle_teacher(schulnummer, args):
    date, kuerzel = args["date"], args["value"]
    plan_data = Plan_Extractor(schulnummer, date)
    data = plan_data.teacher_lessons(kuerzel)
    timestamp = plan_data.get_timestamp()
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    return render_template_wrapper('plan.html', plan_type="Lehrer", plan_value=kuerzel, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo, timestamp=timestamp)

### RAUMPLAN ###
def handle_room(schulnummer, args):
    date, room_num = args["date"], args["value"]
    plan_data = Plan_Extractor(schulnummer, date)
    data = plan_data.room_lessons(room_num)
    timestamp = plan_data.get_timestamp()
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    return render_template_wrapper('plan.html', plan_type="Raum", plan_value=room_num, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo, timestamp=timestamp)

### FREE ROOMS ###
def handle_free_rooms(schulnummer, args, all_rooms):
    date = args["date"]
    plan_data = Plan_Extractor(schulnummer, date)
    rooms = plan_data.free_rooms(all_rooms)
    timestamp = plan_data.get_timestamp()
    return render_template_wrapper('free_rooms.html', date=convert_date_readable(date), lessons=rooms, timestamp=timestamp)

### Gefilterter Klassenplan ###
@app.route('/<schulnummer>/<date>/plan/<klasse>/<kurse>')
@login_required
def plan(schulnummer, date, klasse, kurse):
    kurse = kurse.split(",")
    plan_data = Plan_Extractor(schulnummer, date)
    data = plan_data.get_plan_filtered_courses(klasse, kurse)
    timestamp = plan_data.get_timestamp()
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    return render_template_wrapper('plan.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo)


@app.route('/sponsors')
def sponsors():
    with open("data/sponsors.json", "r", encoding="utf-8") as f:
        sponsors = json.load(f)
    return render_template_wrapper('sponsors.html', sponsors=sponsors)

@app.route('/sw.js')
def service_worker():
    response = make_response("""self.addEventListener ("fetch", function(event) {});""", 200)
    response.mimetype = "application/javascript"
    return response

@app.route('/robots.txt')
def robots():
    response = make_response("""User-agent: *\nDisallow: /""", 200)
    response.mimetype = "text/plain"
    return response

if __name__ == '__main__':
    app.run(port=5010)
    #app.run(host='0.0.0.0', port=5010)