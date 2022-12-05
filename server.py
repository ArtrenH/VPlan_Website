import json
from flask import Flask, redirect, render_template

from methods import get_plan, find_free_rooms, room_lessons, teacher_lessons, get_plan_normal, get_plan_filtered_courses

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/name/<schulname>')
def schulname(schulname):
    print(schulname)
    with open("creds.json", "r") as f:
        creds = json.load(f)
    cur_schulnummer = [creds[elem]["school_number"] for elem in creds if creds[elem]["school_name"] == schulname]
    if len(cur_schulnummer) == 0:
        return {"error": "no school with this name found"}
    return redirect("/"+ cur_schulnummer[0], code=302)

@app.route('/<schulnummer>')
def schulnummer(schulnummer):
    return schulnummer


@app.route('/<schulnummer>/<date>')
def schulplan(schulnummer, date):
    return get_plan(school_num=schulnummer, date=date).content


@app.route('/<schulnummer>/<date>/lehrerplan/<kuerzel>')
def lehrerplan(schulnummer, date, kuerzel):
    data = teacher_lessons(schulnummer, date, kuerzel)
    return render_template('plan.html', title=f"Plan für Datum '{date}' und Lehrer '{kuerzel}':", plan=data)

@app.route('/<schulnummer>/<date>/raumplan/<room_num>')
def raumplan(schulnummer, date, room_num):
    data = room_lessons(schulnummer, date, room_num)
    return render_template('plan.html', title=f"Plan für Datum '{date}' und Raum '{room_num}':", plan=data)

@app.route('/<schulnummer>/<date>/klassenplan/<klasse>')
def klassenplan(schulnummer, date, klasse):
    print(klasse)
    klasse = klasse.replace("_", "/")
    data = get_plan_normal(schulnummer, date, klasse)
    return render_template('plan.html', title=f"Plan für Datum '{date}' und Klasse '{klasse}':", plan=data)

@app.route('/<schulnummer>/<date>/plan/<klasse>/<kurse>')
def plan(schulnummer, date, klasse, kurse):
    print(klasse)
    klasse = klasse.replace("_", "/")
    kurse = kurse.split(",")
    print(kurse)
    data = get_plan_filtered_courses(schulnummer, date, klasse, kurse)
    return render_template('plan.html', title=f"Plan für Datum '{date}' und Klasse '{klasse}':", plan=data)





app.run(port=5010)