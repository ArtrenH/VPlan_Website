import json
from flask import Flask, redirect, render_template, make_response, url_for, request, session
import datetime
from methods import MetaExtractor, Plan_Extractor, DateExtractor
from vplan_utils import add_spacers, remove_duplicates, convert_date_readable
from errors import DayOnWeekend, CredentialsNotFound
from flask_login import LoginManager, UserMixin, login_required, logout_user, login_user
from dotenv import load_dotenv
import os
import urllib
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
    with open("creds.json", "r", encoding="utf-8") as f:
        tmp_data = json.load(f)
        return render_template('start.html', available_schools=[[item["school_name"], item["display_name"]] for item in tmp_data.values()])
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
    # data for selection
    date_data = DateExtractor(schulnummer)
    dates = date_data.read_data()
    default_date = date_data.default_date()
    other_data = MetaExtractor(schulnummer)
    klassen = other_data.course_list()
    teachers = other_data.teacher_list()
    rooms = other_data.room_list()
    # sharable links that automatically load the plan
    if request.args.get("share", False) == "true":
        with open("creds.json", "r", encoding="utf-8") as f:
            creds = json.load(f)
        new_string_args = dict(request.args)
        del new_string_args["share"]
        return render_template('index.html',
            dates=dates, teachers=teachers, rooms=rooms, klassen=klassen,
            school_name=creds[schulnummer]["school_name"], default_date=default_date,
            var_vorangezeigt="true", var_angefragt_link=urllib.parse.urlencode(new_string_args))
    # normal website
    if len(request.args) == 0:
        with open("creds.json", "r", encoding="utf-8") as f:
            creds = json.load(f)
        if schulnummer not in creds:
            return redirect(url_for('handle_plan', schulnummer="10001329"))
            #return {"error": "no school with this number found"}
        return render_template('index.html',
            dates=dates, teachers=teachers, rooms=rooms, klassen=klassen,
            school_name=creds[schulnummer]["school_name"],
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
            if handle_pair[0] not in request.args:
                return handle_pair[0] + " fehlt"
            if request.args[handle_pair[0]] not in handle_pair[2]:
                return handle_pair[0] + " not found"
            return handle_pair[1](schulnummer, request.args)
    return "ok"

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

@app.route('/<schulnummer>/<date>')
@login_required
def schulplan(schulnummer, date):
    return Plan_Extractor(schulnummer, date).r.content

### LEHRERPLAN ###
def handle_teacher(schulnummer, args):
    date, kuerzel = args["date"], args["teacher"]
    data = Plan_Extractor(schulnummer, date).teacher_lessons(kuerzel)
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    return render_template('plan.html', plan_type="Lehrer", plan_value=kuerzel, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo)

### RAUMPLAN ###
def handle_room(schulnummer, args):
    date, room_num = args["date"], args["room"]
    data = Plan_Extractor(schulnummer, date).room_lessons(room_num)
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
    return render_template('plan.html', plan_type="Raum", plan_value=room_num, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(lessons)), zusatzinfo=zusatzinfo)

### KLASSENPLAN ###
def handle_klasse(schulnummer, args):
    date, klasse = args["date"], args["klasse"]
    klasse = klasse.replace("_", "/")
    try:
        data = Plan_Extractor(schulnummer, date).get_plan_normal(klasse)
    except CredentialsNotFound:
        return "no credentials for your school"
    except DayOnWeekend:
        return "day is on the weekend"
    lessons = data["lessons"]
    zusatzinfo = data["zusatzinfo"]
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


@app.route('/sponsors')
def sponsors():
    with open("data/sponsors.json", "r") as f:
        sponsors = json.load(f)
    return render_template('sponsors.html', sponsors=sponsors)

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