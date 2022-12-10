import json
from flask import Flask, redirect, render_template, make_response
import datetime
from methods import Plan_Extractor
from vplan_utils import add_spacers, remove_duplicates, convert_date_readable

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
    return Plan_Extractor(schulnummer, date).r.content

@app.route('/<schulnummer>/<date>/lehrerplan/<kuerzel>')
def lehrerplan(schulnummer, date, kuerzel):
    data, zusatzinfo = Plan_Extractor(schulnummer, date).teacher_lessons(kuerzel)
    return render_template('plan.html', plan_type="Lehrer", plan_value=kuerzel, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(data)), zusatzinfo=zusatzinfo)

@app.route('/<schulnummer>/<date>/raumplan/<room_num>')
def raumplan(schulnummer, date, room_num):
    data, zusatzinfo = Plan_Extractor(schulnummer, date).room_lessons(room_num)
    return render_template('plan.html', plan_type="Raum", plan_value=room_num, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(data)), zusatzinfo=zusatzinfo)

@app.route('/<schulnummer>/<date>/klassenplan/<klasse>')
def klassenplan(schulnummer, date, klasse):
    klasse = klasse.replace("_", "/")
    data, zusatzinfo = Plan_Extractor(schulnummer, date).get_plan_normal(klasse)
    return render_template('plan.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(data)), zusatzinfo=zusatzinfo)

@app.route('/<schulnummer>/<date>/plan/<klasse>/<kurse>')
def plan(schulnummer, date, klasse, kurse):
    kurse = kurse.split(",")
    data, zusatzinfo = Plan_Extractor(schulnummer, date).get_plan_filtered_courses(klasse, kurse)
    return render_template('plan.html', plan_type="Klasse", plan_value=klasse, date=convert_date_readable(date), plan=add_spacers(remove_duplicates(data)), zusatzinfo=zusatzinfo)

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


print("http://127.0.0.1:5010/10001329/20221209/klassenplan/JG12")


app.run(port=5010)
#app.run(host='0.0.0.0', port=5010)