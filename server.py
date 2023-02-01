# coding=utf-8

import json
from bson import ObjectId
from flask import redirect, make_response, send_from_directory, url_for, request, jsonify
from methods import Plan_Extractor, MetaExtractor, extract_metadata, get_default_date
from vplan_utils import add_spacers, remove_duplicates, convert_date_readable, sort_klassen
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv

load_dotenv()

from modules.utils import render_template_wrapper, User, AddStaticFileHashFlask, get_user, set_user_preferences, users, update_settings
from modules.authorization import authorization

app = AddStaticFileHashFlask(__name__)
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

csrf = CSRFProtect(app)
csrf.init_app(app)


@login_manager.user_loader
def user_loader(user_id):
    tmp_user = get_user(user_id)
    if tmp_user is None:
        return
    tmp_user = User(user_id)
    return tmp_user

app.register_blueprint(authorization)
@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("authorization.login"))

@app.route('/')
@login_required
def index():
    with open("creds.json", "r", encoding="utf-8") as f:
        tmp_data = json.load(f)
        return render_template_wrapper('start', available_schools=[[item["school_name"], item["display_name"], key] for key, item in tmp_data.items()])

@app.route('/about')
def about():
    return render_template_wrapper('about', devs=[
        {
            "name": "_qrtrenH#4634",
            "pfp": url_for('static', filename='images/about/_qrtrenH.jpeg'),
            "bereal_link": "https://bere.al/artrenh"
            
        },
        {
            "name": "B̴͌͘r̸̛̐ö̴́̎t̵̤̋#5090",
            "pfp": url_for('static', filename='images/about/Brot.png'),
            "bereal_link": "https://bere.al/officialbrot"
        }
    ])

# Find school by name
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

@app.route('/authorize/<school_number>', methods=['GET', 'POST'])
@login_required
def authorize_school(school_number):
    with open("creds.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        try:
            school_creds = data[school_number]
        except Exception:
            return render_template_wrapper('authorize_school', schulnummer=school_number, errors="Die angegebene Schule konnte nicht gefunden werden. Bitte überprüfe die Schulnummer und versuche es erneut. (Falls deine Schule im vorigen Schritt nicht zur Auswahl stand, schreib uns auf Discord)")
    
        if request.method != 'POST':
            return render_template_wrapper('authorize_school', schulnummer=school_number, schulname=school_creds["display_name"])

        username = request.form.get('username')
        pw = request.form.get('pw')
        if school_creds["username"] == username and school_creds["password"] == pw:
            tmp_user = get_user(current_user.get_id())
            tmp_authorized_schools = tmp_user.get("authorized_schools", [])
            if school_number not in tmp_authorized_schools:
                tmp_authorized_schools.append(school_number)
                users.update_one({'_id': ObjectId(current_user.get_id())}, {"$set": {'authorized_schools': tmp_authorized_schools}})
            return redirect(url_for('handle_plan', schulnummer=school_number))
        else:
            return render_template_wrapper('authorize_school', schulnummer=school_number, errors="Benutzername oder Passwort waren falsch! Bitte versuch es erneut.")

# homepage for a school
@app.route('/<school_number>')
@login_required
def handle_plan(school_number):
    with open("creds.json", "r", encoding="utf-8") as f:
        creds = json.load(f)
    if school_number not in creds:
        return "Schule nicht gefunden!"
    if not school_number.isdigit():
        return redirect("/name/" + school_number, code=302)
    tmp_user = get_user(current_user.get_id())
    if not (school_number in tmp_user.get("authorized_schools", []) or tmp_user.get("admin", False)):
        return redirect(url_for('authorize_school', schulnummer=school_number))
    # data for selection
    meta_data = extract_metadata(school_number)
    default_date = get_default_date([elem[0] for elem in meta_data["dates"]])

    # sharable links that automatically load the plan
    no_args = False
    if request.args.get("share", False) == "true":
        new_string_args = dict(request.args)
        del new_string_args["share"]
        if len(new_string_args) > 0:
            return render_template_wrapper('index',
                **meta_data,
                school_number=school_number, default_date=default_date,
                var_vorangezeigt="true", var_angefragt_values=new_string_args)
        else:
            no_args = True
    # normal website
    if len(request.args) == 0 or no_args:
        return render_template_wrapper('index',
            **meta_data,
            school_number=school_number, default_date=default_date,
            var_vorangezeigt="false", var_angefragt_link="")
    return "<div class='row'><p class='flow-text col s12'>Bitte wähle einen Lehrer, einen Raum, eine Klasse oder den \"Freie Räume\"-Button aus um einen Plan zu sehen.</p></div>"

# api for plans
@app.route("/api/<school_number>")
@login_required
def api_response(school_number, return_json=False):
    args = request.args
    # First validation
    if "type" not in args:
        return "type fehlt"
    if "date" not in args:
        return "date fehlt"
    date = args["date"]
    tmp_user = get_user(current_user.get_id())
    if not (school_number in tmp_user.get("authorized_schools", []) or tmp_user.get("admin", False)):
        return redirect(url_for('authorize_school', schulnummer=school_number))
    # Freie Räume
    if args["type"] == "free_rooms":
        plan_data = Plan_Extractor(school_number, date)
        meta_data = extract_metadata(school_number)
        rooms = plan_data.free_rooms(meta_data["rooms"])
        timestamp = convert_date_readable(plan_data.get_timestamp())
        default_lesson = plan_data.current_lesson()
        ctx_data = {"date": convert_date_readable(date), "lessons": rooms, "timestamp": timestamp, "default_lesson": default_lesson}
        if return_json:
            return jsonify(ctx_data)
        return render_template_wrapper('free_rooms', **ctx_data)
    # check if value is given
    if "value" not in args:
        return "value fehlt"
    # Klasse, Lehrer, Raum -> get plan with the right function, return it alongside some metadata
    plan_data = Plan_Extractor(school_number, date)
    handlers = {
        "klasse": {"function": plan_data.get_plan_normal, "name": "Klasse"},
        "klasse_preferences": {"function": plan_data.get_plan_filtered_courses, "name": "Klasse"},
        "teacher": {"function": plan_data.teacher_lessons, "name": "Lehrer"},
        "room": {"function": plan_data.room_lessons, "name": "Raum"},
    }
    # gespeicherte automatische Filterung
    if args["type"] == "klasse_preferences":
        preferences = tmp_user.get("preferences", {})
        preferences = preferences.get(school_number, {}).get(args["value"], {})
        if preferences != {}:
            plan_data.set_preferences(preferences)
        else:
            handlers["klasse_preferences"]["function"] = plan_data.get_plan_normal
    # Tatsächliches Laden des Plans
    if args["type"] not in handlers:
        return "Bitte wähle einen Lehrer, einen Raum, eine Klasse oder den \"Freie Räume\"-Button aus um einen Plan zu sehen."
    function = handlers[args["type"]]["function"]
    data = function(args["value"])
    ctx_data = {
        "plan_type": handlers[args["type"]]["name"],
        "plan_value": args["value"],
        "date": convert_date_readable(date),
        "plan": add_spacers(remove_duplicates(data["lessons"])),
        "zusatzinfo": data["zusatzinfo"],
        "timestamp": convert_date_readable(plan_data.get_timestamp()),
        "week": plan_data.get_week()
    }
    if return_json:
        return jsonify(ctx_data)
    return render_template_wrapper(
        'plan',
        **ctx_data
    )

@app.route('/api/json/<school_number>')
@login_required
def api_response_json(school_number):
    tmp_user = get_user(current_user.get_id())
    if not (school_number in tmp_user.get("authorized_schools", []) or tmp_user.get("admin", False)):
        return redirect(url_for('authorize_school', schulnummer=school_number))
    return api_response(school_number, return_json=True)

@app.route("/settings", methods=["POST"])
@login_required
def settings():
    # Preventing users from saving arbitrary data in their settings
    user_settings = request.get_json()
    return update_settings(user_settings)

@app.route("/preferences/<school_number>", methods=["GET", "POST"])
@login_required
def preferences(school_number):
    tmp_user = get_user(current_user.get_id())
    if not (school_number in tmp_user.get("authorized_schools", []) or tmp_user.get("admin", False)):
        return redirect(url_for('authorize_school', schulnummer=school_number))
    args = request.args
    if "course" not in args:
        # return list of courses
        if request.method == "GET":
            course_list = MetaExtractor(school_number).course_list()
            return jsonify(sort_klassen(course_list))
        else:
            return "Klasse fehlt"
    klasse = args["course"]
    user_preferences = tmp_user.get("preferences", {})
    current_preferences = user_preferences.get(school_number, {}).get(klasse, [])
    group_list = []
    for elem in MetaExtractor(school_number).group_list(klasse):
        if elem[0] in current_preferences:
            group_list.append(list(elem) + [True])
        else:
            group_list.append(list(elem) + [False])
    # return list of groups
    if request.method == "GET":
        group_list = sorted(group_list, key=lambda x: (x[0].upper() != x[0], x))
        return jsonify(group_list)
    #elif request.method == "POST":
    data = request.get_json()
    if not isinstance(data, list):
        return "invalid json"
    group_list = [elem[0] for elem in group_list]
    for item in data:
        if not item in group_list:
            return f"{item} is not a valid course!"
    data = list(set(data))
    user_preferences = tmp_user.get("preferences", {})
    if not school_number in user_preferences:
        user_preferences[school_number] = {}
    user_preferences[school_number][klasse] = data
    set_user_preferences(current_user.get_id(), user_preferences)
    return "Preferences saved!"


@app.route('/sponsors')
def sponsors():
    with open("data/sponsors.json", "r", encoding="utf-8") as f:
        sponsors = json.load(f)
    return render_template_wrapper('sponsors', sponsors=sponsors)

@app.route('/sw.js')
def service_worker():
    return send_from_directory("static", "js/sw.js")

@app.route('/robots.txt')
def robots():
    response = make_response("""User-agent: *\nDisallow: /""", 200)
    response.mimetype = "text/plain"
    return response

if __name__ == '__main__':
    app.run(port=5010)
    #app.run(host='0.0.0.0', port=5010)