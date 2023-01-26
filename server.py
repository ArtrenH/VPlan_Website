# coding=utf-8

import json
from bson import ObjectId
from flask import Flask, redirect, make_response, url_for, request, jsonify
from methods import Plan_Extractor, extract_metadata, get_default_date
from vplan_utils import add_spacers, remove_duplicates, convert_date_readable
from flask_login import LoginManager, login_required
import os
import contextlib
import hashlib
import urllib
from flask_compress import Compress
from werkzeug.security import safe_join
from dotenv import load_dotenv
load_dotenv()

from modules.utils import render_template_wrapper, User, users
from modules.authorization import authorization

class AddStaticFileHashFlask(Flask):
    def __init__(self, *args, **kwargs):
        super(AddStaticFileHashFlask, self).__init__(*args, **kwargs)
        self._file_hash_cache = {}
    def inject_url_defaults(self, endpoint, values):
        super(AddStaticFileHashFlask, self).inject_url_defaults(endpoint, values)
        if endpoint == "static" and "filename" in values:
            filepath = safe_join(self.static_folder, values["filename"])
            if os.path.isfile(filepath):
                cache = self._file_hash_cache.get(filepath)
                mtime = os.path.getmtime(filepath)
                if cache != None:
                    cached_mtime, cached_hash = cache
                    if cached_mtime == mtime:
                        values["h"] = cached_hash
                        return
                h = hashlib.md5()
                with contextlib.closing(open(filepath, "rb")) as f:
                    h.update(f.read())
                h = h.hexdigest()
                self._file_hash_cache[filepath] = (mtime, h)
                values["h"] = h

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

@login_manager.user_loader
def user_loader(user_id):
    tmp_user = users.find_one({'_id': ObjectId(user_id)})
    if tmp_user is None:
        return
    tmp_user = User(user_id)
    return tmp_user

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("authorization.login"))

app.register_blueprint(authorization)

@app.route('/')
@login_required
def index():
    with open("creds.json", "r", encoding="utf-8") as f:
        tmp_data = json.load(f)
        return render_template_wrapper('start.html', available_schools=[[item["school_name"], item["display_name"], key] for key, item in tmp_data.items()])

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

# Find school by name
@app.route('/name/<schulname>')
@login_required
def schulname(schulname):
    with open("creds.json", "r", encoding="utf-8") as f:
        creds = json.load(f)
    cur_schulnummer = [creds[elem]["school_number"] for elem in creds if creds[elem]["school_name"] == schulname]
    if len(cur_schulnummer) == 0:
        print(url_for('handle_plan', schulnummer="10001329"))
        return redirect(url_for('handle_plan', schulnummer="10001329"))
        #return {"error": "no school with this name found"}
    return redirect("/"+ cur_schulnummer[0], code=302)

# homepage for a school
@app.route('/<schulnummer>')
@login_required
def handle_plan(schulnummer):
    with open("creds.json", "r", encoding="utf-8") as f:
        creds = json.load(f)
    if schulnummer not in creds:
        return "Schule nicht gefunden!"
    if not schulnummer.isdigit():
        return redirect("/name/" + schulnummer, code=302)
    # data for selection
    meta_data = extract_metadata(schulnummer)
    default_date = get_default_date([elem[0] for elem in meta_data["dates"]])

    # sharable links that automatically load the plan
    no_args = False
    if request.args.get("share", False) == "true":
        new_string_args = dict(request.args)
        del new_string_args["share"]
        if len(new_string_args) > 0:
            return render_template_wrapper('index.html',
                **meta_data,
                school_number=schulnummer, default_date=default_date,
                var_vorangezeigt="true", var_angefragt_link=urllib.parse.urlencode(new_string_args))
        else:
            no_args = True
    # normal website
    if len(request.args) == 0 or no_args:
        return render_template_wrapper('index.html',
            **meta_data,
            school_number=schulnummer, default_date=default_date,
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
    # Freie Räume
    if args["type"] == "free_rooms":
        plan_data = Plan_Extractor(school_number, date)
        meta_data = extract_metadata(school_number)
        rooms = plan_data.free_rooms(meta_data["rooms"])
        timestamp = plan_data.get_timestamp()
        ctx_data = {"date": convert_date_readable(date), "lessons": rooms, "timestamp": timestamp}
        if return_json:
            return jsonify(ctx_data)
        return render_template_wrapper('free_rooms.html', **ctx_data)
    # check if value is given
    if "value" not in args:
        return "value fehlt"
    # Klasse, Lehrer, Raum -> get plan with the right function, return it alongside some metadata
    plan_data = Plan_Extractor(school_number, date)
    handlers = {
        "klasse": {"function": plan_data.get_plan_normal, "name": "Klasse"},
        "teacher": {"function": plan_data.teacher_lessons, "name": "Lehrer"},
        "room": {"function": plan_data.room_lessons, "name": "Raum"},
    }
    if args["type"] not in handlers:
        return "type unbekannt"
    function = handlers[args["type"]]["function"]
    data = function(args["value"])
    timestamp = plan_data.get_timestamp()
    plan_type = handlers[args["type"]]["name"]
    plan_value = args["value"]
    ctx_data = {
        "plan_type": plan_type,
        "plan_value": plan_value,
        "date": convert_date_readable(date),
        "plan": add_spacers(remove_duplicates(data["lessons"])),
        "zusatzinfo": data["zusatzinfo"],
        "timestamp": timestamp
    }
    if return_json:
        return jsonify(ctx_data)
    return render_template_wrapper(
        'plan.html',
        **ctx_data
    )

@app.route('/api/json/<school_number>')
@login_required
def api_response_json(school_number):
    return api_response(school_number, return_json=True)

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