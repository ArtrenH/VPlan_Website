import json
from flask import Flask, redirect, render_template
import datetime

from methods import get_plan, find_free_rooms, room_lessons, teacher_lessons, get_plan_normal, get_plan_filtered_courses, load_courses

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

def convert_date_readable(date):
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:])
    date_string = datetime.datetime(year, month, day).strftime("%a %d.%m.%Y")
    translated_date_string = date_string.replace("Mon", "Mo.").replace("Tue", "Di.").replace("Wed", "Mi.").replace("Thu", "Do.").replace("Fri", "Fr.")
    return translated_date_string

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
    return render_template('plan.html', title=f"Plan für Lehrer <span class='custom_badge'>{kuerzel}</span> am <span class='custom_badge'>{convert_date_readable(date)}</span>:", plan=data)

@app.route('/<schulnummer>/<date>/raumplan/<room_num>')
def raumplan(schulnummer, date, room_num):
    data = room_lessons(schulnummer, date, room_num)
    return render_template('plan.html', title=f"Plan für Raum <span class='custom_badge'>{room_num}</span> am <span class='custom_badge'>{convert_date_readable(date)}</span>:", plan=data)

@app.route('/<schulnummer>/<date>/klassenplan/<klasse>')
def klassenplan(schulnummer, date, klasse):
    klasse = klasse.replace("_", "/")
    data = get_plan_normal(schulnummer, date, klasse)
    return render_template('plan.html', title=f"Plan für Klasse <span class='custom_badge'>{klasse}</span> am <span class='custom_badge'>{convert_date_readable(date)}</span>:", plan=data)

@app.route('/<schulnummer>/<date>/plan/<klasse>/<kurse>')
def plan(schulnummer, date, klasse, kurse):
    kurse = kurse.split(",")
    data = get_plan_filtered_courses(schulnummer, date, klasse, kurse)
    print(data)
    return render_template('plan.html', title=f"Plan für Klasse <span class='custom_badge'>{klasse}</span> am <span class='custom_badge'>{convert_date_readable(date)}</span>:", plan=data)


@app.route('/<schulnummer>/<date>/plan/<klasse>')
def courses(schulnummer, date, klasse):
    klasse = klasse.replace("_", "/")
    data = load_courses(schulnummer, klasse)
    return render_template('courses.html', title=f"Plan für Klasse <span class='custom_badge'>{klasse}</span> am <span class='custom_badge'>{convert_date_readable(date)}</span>:", courses=data)

#@app.route("/<schulnummer>/<group>")
#def courses(schulnummer, group):
    #return load_courses(sch)




app.run(port=5010)