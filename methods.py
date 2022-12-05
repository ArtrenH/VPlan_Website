import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import os

from models import Plan, Group


def get_plan(school_num, date):
    with open('creds.json') as f:
        credentials = json.load(f)
    print(school_num)
    if school_num not in credentials:
        return {"error": "School not found"}
    year, month, day = int(date[:4]), int(date[4:6]), int(date[6:])
    d = datetime(year, month, day)
    if d.weekday() > 4:
        return {"error": "day is on the weekend"}
    plan_url = f"https://z1.stundenplan24.de/schulen/{credentials[school_num]['school_number']}/mobil/mobdaten/PlanKl{date}.xml"
    header_stripped = {"authorization": credentials[school_num]["authorization"],}
    r = requests.get(plan_url, headers=header_stripped)
    if r.status_code == 404:
        print("error")
        return {"error": "plan not available"}
    return r


def get_latest_plans(school_num):
    with open('creds.json') as f:
        credentials = json.load(f)
    if school_num not in credentials:
        return {"error": "School not found"}
    plan_url = f"https://z1.stundenplan24.de/schulen/{credentials[school_num]['school_number']}/mobil/mobdaten/vpinfok.txt"
    header_stripped = {"authorization": credentials[school_num]["authorization"],}
    r = requests.get(plan_url, headers=header_stripped)
    return r


# extracts all rooms used in a certain hour from a BeautifulCoup object
def find_all_rooms_hour(day_data, lesson_num: str):
    rooms = []
    lessons = day_data.find_all("std")
    lessons = [lesson for lesson in lessons if lesson.find('st').text.strip() == lesson_num]
    for lesson in lessons:
        cur_room = lesson.find("ra").text.strip()
        info = lesson.find("if").text.strip()
        info_bad_keys = ["selbst. (v), Aufgaben wurden erteilt, bitte zu Hause erledigen"]
        if cur_room != '' and cur_room not in rooms and info not in info_bad_keys:
            rooms.append(cur_room)
    return [room for room in rooms if room != ""]

# finds rooms that are not being used in a lesson at a school based on a day
def find_free_rooms(school_num, day, lesson):
    if not school_num in os.listdir("data/schools"):
        return {"error": "requested school not in database"}
    c = get_plan(school_num=school_num, date=day)
    if "error" in c:
        return {"error": "API-Error"}
    if not "rooms" in os.listdir(f"data/schools/{school_num}"):
        return {"error": "missing room data"}
    if not f"room_list_{school_num}.json" in os.listdir(f"data/schools/{school_num}/rooms"):
        return {"error": "missing room data"}
    with open(f"data/schools/{school_num}/rooms/room_list_{school_num}.json", "r") as f:
        all_rooms = json.load(f)["rooms"]
    day_data = BeautifulSoup(c.text, features="xml")
    rooms_hour = find_all_rooms_hour(day_data=day_data, lesson_num=lesson)
    free_rooms = [room for room in all_rooms if room not in rooms_hour]
    return free_rooms

def room_lessons(school_num, day, room):
    c = get_plan(school_num=school_num, date=day)
    if "error" in c:
        return {"error": "error with getting the plan for the requested day and school"}
    day_data = BeautifulSoup(c.text, features="html.parser")
    room_lessons = []
    class_plans = day_data.find_all("kl")
    for class_plan in class_plans:
        class_name = class_plan.find("kurz").text.strip()
        class_lessons = class_plan.find_all("std")
        for class_lesson in class_lessons:
            room_num = class_lesson.find("ra").text.strip()
            info = class_lesson.find("if").text.strip()
            if room_num == room or room in info:
                room_lessons.append({**{"class": class_name}, **{
                    new_name: class_lesson.find(code).text.strip() if class_lesson.find(code) else "" for new_name, code in zip(["lesson", "begin", "end", "subject", "subject_name", "teacher", "room", "information"], ["st", "beginn", "ende", "fa", "ku2", "le", "ra", "if"])
                }})
    return Plan(school_num, day, room_lessons).render()

# extracts all lessons a teacher gives at a certain day
def teacher_lessons(school_num, day, tag):
    c = get_plan(school_num=school_num, date=day)
    if "error" in c:
        return {"error": "error with getting the plan for the requested day and school"}
    day_data = BeautifulSoup(c.text, features="html.parser")
    teacher_lessons = []
    class_plans = day_data.find_all("kl")
    for class_plan in class_plans:
        class_name = class_plan.find("kurz").text.strip()
        class_lessons = class_plan.find_all("std")
        for class_lesson in class_lessons:
            teacher = class_lesson.find("le").text.strip()
            info = class_lesson.find("if").text.strip()
            if teacher == tag or tag in info:
                teacher_lessons.append({**{"class": class_name}, **{
                    new_name: class_lesson.find(code).text.strip() if class_lesson.find(code) else "" for new_name, code in zip(["lesson", "begin", "end", "subject", "subject_name", "teacher", "room", "information"], ["st", "beginn", "ende", "fa", "ku2", "le", "ra", "if"])
                }})
    return Plan(school_num, day, teacher_lessons).render()

# gets a plan for a whole class
def get_plan_normal(school_num, day, course):
    c = get_plan(school_num=school_num, date=day)
    print("hallloooo")
    if "error" in c:
        return {"error": "error with getting the plan for the requested day and school"}
    day_data = BeautifulSoup(c.text, features="html.parser")
    course_data = False
    for kl in day_data.find_all("kl"):
        if kl.find("kurz").text.strip() == course:
            course_data = kl
            break
    if not course_data:
        print("not found")
        return {"error": "chosen class has not been found"}
    pl = kl.find("pl")
    std_all = pl.find_all("std")
    lessons = []
    for std in std_all:
        lessons.append({**{"class": course}, **{
            new_name: std.find(code).text.strip() if std.find(code) else "" for new_name, code in zip(["lesson", "begin", "end", "subject", "subject_name", "teacher", "room", "information"], ["st", "beginn", "ende", "fa", "ku2", "le", "ra", "if"])
        }})
    print("fast fertig")
    return Plan(school_num, day, lessons).render()

# gets a plan for a class with only certain courses (for example: course="JG11", courses=["PH1", "MA4"])
def get_plan_filtered_courses(school_num, day, course, courses):
    normal_plan = get_plan_normal(school_num, day, course)
    if "error" in normal_plan:
        return normal_plan
    return Plan(school_num, day, [lesson for lesson in normal_plan if lesson["subject_name"] in courses or lesson["subject"] in courses]).render()


def get_classes(school_num):
    with open('creds.json') as f:
        credentials = json.load(f)
    if school_num not in credentials:
        return {"error": "School not found"}
    plan_url = f"https://z1.stundenplan24.de/schulen/{credentials[school_num]['school_number']}/mobil/mobdaten/Klassen.xml"
    header_stripped = {"authorization": credentials[school_num]["authorization"],}
    r = requests.get(plan_url, headers=header_stripped)
    soup = BeautifulSoup(r.content.decode("utf-8"), features="xml")
    classes = soup.find_all("Kl")
    class_data = {"kurse": {}, "unterricht": {}}
    for cur_class in classes:
        class_data["kurse"][cur_class.find("Kurz").text] = [
            {"course": ku.find("KKz").text,
            "teacher": ku.find("KKz").get("KLe", "")} for ku in cur_class.find("Kurse").find_all("Ku")
        ]
        class_data["unterricht"][cur_class.find("Kurz").text] = {ku.find("UeNr").text: {
        #c = {ku.find("UeNr").text: {
            "id": ku.find("UeNr").text,
            "teacher": ku.find("UeNr").get("UeLe", ""),
            "subject": ku.find("UeNr").get("UeFa", ""),
            "course": ku.find("UeNr").get("UeGr", "")
        } for ku in cur_class.find("Unterricht").find_all("Ue")}
    with open(f"data/{school_num}.json", "w+") as f:
        json.dump(class_data, f, indent=2, ensure_ascii=False)

    return r


def load_courses(school_num, group):
    with open(f"data/{school_num}.json", "r") as f:
        data = json.load(f)
    if group not in data["unterricht"]:
        return {"error": "Klasse nicht gefunden"}
    all_courses = data["unterricht"][group].values()
    return Group(school_num, all_courses).render()



if __name__ == "__main__":
    pass
    #print(load_courses("10001329", "JG12"))
    #print(get_plan_normal("10001329", "20221205", "JG12"))
    #print(get_plan_filtered_courses("10001329", "20221205", "JG12", ["MA1", "MA2", "MA3", "MA4"]))
    print(teacher_lessons("10001329", "20221205", "GLS"))
    #print(room_lessons("10001329", "20221205", "2312"))
