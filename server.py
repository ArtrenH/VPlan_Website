import json
from flask import Flask, redirect, render_template, make_response, url_for, request, session
import datetime
from methods import MetaExtractor, Plan_Extractor, DateExtractor
from vplan_utils import add_spacers, remove_duplicates, convert_date_readable
from errors import DayOnWeekend, CredentialsNotFound
from flask_login import LoginManager, UserMixin, login_required, logout_user, login_user
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") if os.getenv("SECRET_KEY") else "DEBUG_KEY"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 32140800

login_manager = LoginManager()
login_manager.init_app(app)

users = {'schueler': {'pw': 'IsfibeT'}}

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return
    user = User()
    user.id = username
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in users:
        return
    user = User()
    user.id = username

    if request.form['pw'] == users[username]['pw']:
        user.is_authenticated = True

    return user

@app.route('/')
@login_required
def index():
    return render_template('start.html')
    return redirect(url_for('handle_plan', schulnummer="10001329"))

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("login"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            if request.form.get('pw') == users[username]['pw']:
                user = User()
                user.id = username
                login_user(user)
                session.permanent = True
                return redirect(url_for('index'))
            else:
                return render_template('login.html', errors="Benutzername oder Passwort waren inkorrekt! Bitte versuchen Sie es erneut.", hide_logout=True)
        except Exception:
            return render_template('login.html', errors="Benutzername oder Passwort waren inkorrekt! Bitte versuchen Sie es erneut.", hide_logout=True)
    return render_template('login.html', hide_logout=True)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/<schulnummer>')
@login_required
def handle_plan(schulnummer):
    if not schulnummer.isdigit():
        return redirect("/name/" + schulnummer, code=302)
    dates = DateExtractor(schulnummer).read_data()
    other_data = MetaExtractor(schulnummer)
    teachers = other_data.teacher_list()
    rooms = other_data.room_list()
    klassen = other_data.course_list()
    if len(request.args) == 0:
        with open("creds.json", "r") as f:
            creds = json.load(f)
        if schulnummer not in creds:
            return redirect(url_for('handle_plan', schulnummer="10001329"))
            #return {"error": "no school with this number found"}
        return render_template('index.html', dates=dates, teachers=teachers, rooms=rooms, klassen=klassen, school_name=creds[schulnummer]["school_name"])
    if "type" not in request.args:
        return "type fehlt"
    if request.args["type"] == "klasse":
        return handle_klasse(schulnummer, request.args)
    if request.args["type"] == "teacher":
        return handle_teacher(schulnummer, request.args)
    if request.args["type"] == "room":
        return handle_room(schulnummer, request.args)
    return "ok"

@app.route('/name/<schulname>')
@login_required
def schulname(schulname):
    print(schulname)
    with open("creds.json", "r") as f:
        creds = json.load(f)
    cur_schulnummer = [creds[elem]["school_number"] for elem in creds if creds[elem]["school_name"] == schulname]
    if len(cur_schulnummer) == 0:
        return redirect(url_for('handle_plan', schulnummer="10001329"))
        #return {"error": "no school with this name found"}
    return redirect("/"+ cur_schulnummer[0], code=302)

@app.route('/<schulnummer>/<date>')
@login_required
def schulplan(schulnummer, date):
    return Plan_Extractor(schulnummer, date).r.content

### LEHRERPLAN ###
def handle_teacher(schulnummer, args):
    if "date" in args and "teacher" in args:
        return lehrerplan(schulnummer, args["date"], args["teacher"])
    # http://127.0.0.1:5010/10001329?date=20221221&type=teacher
    if "teacher" in args:
        return "not yet implemented..."
    return lehrerliste(schulnummer)
    #return render_template('index.html')

def lehrerplan(schulnummer, date, kuerzel):
    data = Plan_Extractor(schulnummer, date).teacher_lessons(kuerzel)
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    return render_template('plan.html', plan_type="Lehrer", plan_value=kuerzel, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo)

def lehrerliste(schulnummer):
    data = MetaExtractor(schulnummer).teacher_list()
    print(data)
    return "ok"

### RAUMPLAN ###
def handle_room(schulnummer, args):
    if "date" in args and "room" in args:
        return raumplan(schulnummer, args["date"], args["room"])
    return render_template('index.html')

def raumplan(schulnummer, date, room_num):
    data = Plan_Extractor(schulnummer, date).room_lessons(room_num)
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    return render_template('plan.html', plan_type="Raum", plan_value=room_num, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo)



### KLASSENPLAN ###
def handle_klasse(schulnummer, args):
    if "date" in args and "klasse" in args:
        # 10001329?date=20221221&type=klasse&klasse=5%2F1
        # 10001329?date=20221221&type=klasse&klasse=JG12
        return klassenplan(schulnummer, args["date"], args["klasse"])
    if "date" not in args and "klasse" not in args:
        # 10001329?type=klasse
        return klassenliste(schulnummer)
    if "klasse" in args:
        # 10001329?type=klasse&klasse=JG12
        return klassenplan_daten(schulnummer, args["klasse"])
    return "?"


def klassenliste(schulnummer):
    print(schulnummer)
    lst = MetaExtractor(schulnummer).course_list()
    links = [{
        "name": elem,
        "link": "/"+schulnummer+"/klassenplan/"+elem.replace("/", "_")
    } for elem in lst]
    return render_template('links.html', links=links)

def klassenplan_daten(schulnummer, klasse):
    #klasse = klasse.replace("_", "/")
    dates = MetaExtractor(schulnummer).current_school_days_str()
    dates = [{
        "name": elem[0],
        "link": "/"+schulnummer+"/"+elem[1]+"/klassenplan/"+klasse
    } for elem in dates]
    return render_template('links.html', links=dates)

def klassenplan(schulnummer, date, klasse):
    klasse = klasse.replace("_", "/")
    try:
        data = Plan_Extractor(schulnummer, date).get_plan_normal(klasse)
    except CredentialsNotFound:
        return "no credentials for your school"
    except DayOnWeekend:
        return "day is on the weekend"
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    print(data["new_dates"])
    return render_template('plan.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo)


### Gefilterter Klassenplan ###
@app.route('/<schulnummer>/<date>/plan/<klasse>/<kurse>')
@login_required
def plan(schulnummer, date, klasse, kurse):
    kurse = kurse.split(",")
    data = Plan_Extractor(schulnummer, date).get_plan_filtered_courses(klasse, kurse)
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    return render_template('plan.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo)

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

"""@app.route('/<schulnummer>/<date>/plan/<klasse>')
def courses(schulnummer, date, klasse):
    klasse = klasse.replace("_", "/")
    data = methods.load_courses(schulnummer, klasse)
    return render_template('courses.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), courses=add_spacers(remove_duplicates(data)))"""

#@app.route("/<schulnummer>/<group>")
#def courses(schulnummer, group):
    #return load_courses(sch)


if __name__ == '__main__':
    app.run(port=5010)
#app.run(host='0.0.0.0', port=5010)