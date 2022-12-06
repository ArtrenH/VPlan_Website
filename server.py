import json
from flask import Flask, redirect, render_template
import datetime

from methods import get_plan, find_free_rooms, room_lessons, teacher_lessons, get_plan_normal, get_plan_filtered_courses, load_courses

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

def add_spacers(vplan_data):
    prev_lesson = 1
    for elem in vplan_data:
        converted_lesson = None
        try:
            converted_lesson = int(elem["lesson"])
        except Exception:
            if(elem["lesson"].split(" - ")[1] == "2"):
                continue
            converted_lesson = int(elem["lesson"].split(" - ")[0])
        
        if prev_lesson + 1 == converted_lesson:
            elem["spacer"] = True
        
        prev_lesson = converted_lesson

    return vplan_data

def equal_dicts(d1, d2, ignore_keys):
    ignored = set(ignore_keys)
    for k1, v1 in d1.items():
        if k1 not in ignored and (k1 not in d2 or d2[k1] != v1):
            return False
    for k2, v2 in d2.items():
        if k2 not in ignored and k2 not in d1:
            return False
    return True

def remove_duplicates(vplan_data):
    new_vplan_data = []
    tmp_vplan_data = sorted(vplan_data, key=lambda d: d['subject'])
    tmp_vplan_data = sorted(tmp_vplan_data, key=lambda d: d['class'])
    tmp_vplan_data = sorted(tmp_vplan_data, key=lambda d: d['info'])
    for i in range(0, len(tmp_vplan_data), 2):
        if equal_dicts(tmp_vplan_data[i], tmp_vplan_data[i+1], ["lesson"]):
            tmp_vplan_data[i]["lesson"] = str(int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1))
            new_vplan_data.append(tmp_vplan_data[i])
        else:
            tmp_vplan_data[i]["lesson"] = f'{int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1)} - 1'
            tmp_vplan_data[i+1]["lesson"] = f'{int((int(tmp_vplan_data[i+1]["lesson"]) - 1)/2 + 1)} - 2'
            new_vplan_data.append(tmp_vplan_data[i])
            new_vplan_data.append(tmp_vplan_data[i+1])
    return sorted(new_vplan_data, key=lambda d: d['lesson'])

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
    return render_template('plan.html', plan_type="Lehrer", plan_value=kuerzel, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(data)))

@app.route('/<schulnummer>/<date>/raumplan/<room_num>')
def raumplan(schulnummer, date, room_num):
    data = room_lessons(schulnummer, date, room_num)
    return render_template('plan.html', plan_type="Raum", plan_value=room_num, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(data)))

@app.route('/<schulnummer>/<date>/klassenplan/<klasse>')
def klassenplan(schulnummer, date, klasse):
    klasse = klasse.replace("_", "/")
    data = get_plan_normal(schulnummer, date, klasse)
    return render_template('plan.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(data)))

@app.route('/<schulnummer>/<date>/plan/<klasse>/<kurse>')
def plan(schulnummer, date, klasse, kurse):
    kurse = kurse.split(",")
    data = get_plan_filtered_courses(schulnummer, date, klasse, kurse)
    print(data)
    return render_template('plan.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(data)))


@app.route('/<schulnummer>/<date>/plan/<klasse>')
def courses(schulnummer, date, klasse):
    klasse = klasse.replace("_", "/")
    data = load_courses(schulnummer, klasse)
    return render_template('courses.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), courses=add_spacers(remove_duplicates(data)))

#@app.route("/<schulnummer>/<group>")
#def courses(schulnummer, group):
    #return load_courses(sch)




app.run(port=5010)