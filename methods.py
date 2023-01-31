# coding=utf-8

import json
import os
from datetime import datetime, timedelta, date
import requests
from bs4 import BeautifulSoup
from pprint import pprint
from models import Plan
from errors import DayOnWeekend, CredentialsNotFound
from vplan_utils import sort_klassen

"""
needs something like this:
<Std>
    <St>4</St>
    <Beginn>10:35</Beginn>
    <Ende>11:20</Ende>
    <Fa FaAe="FaGeaendert">---</Fa>
    <Ku2>ph1</Ku2>
    <Le LeAe="LeGeaendert"></Le>
    <Ra RaAe="RaGeaendert"></Ra>
    <Nr>713</Nr>
    <If>ph1 Frau Riedel fällt aus</If>
</Std>
"""
def extract_data(std_soup):
    cur_extract_data = {
        new_name: std_soup.find(code).text.strip() if std_soup.find(code) else "" for new_name, code in zip(["course_id", "lesson", "begin", "end", "subject", "subject_name", "teacher", "room", "info"], ["Nr", "St", "Beginn", "Ende", "Fa", "Ku2", "Le", "Ra", "If"])
    }
    for name, key in zip(["subject", "teacher", "room"], ["Fa", "Le", "Ra"]):
        cur_part = std_soup.find(key)
        cur_extract_data[f"{name}_changed"] = False
        if cur_part.get(f"{key}Ae") == f"{key}Geaendert":
            cur_extract_data[f"{name}_changed"] = True
    return cur_extract_data

def find_zusatzinfo(soup):
    return [elem.text.strip() for elem in soup.find("ZusatzInfo").find_all("ZiZeile")] if soup.find("ZusatzInfo") else []

def find_times(plan, course):
    course_data = find_course(plan, course)
    time_data = course_data.find("KlStunden")
    if not time_data: return {}
    time_data = {tag.text: {"lesson": tag.text, "begin": tag.get("ZeitVon", "?"), "end": tag.get("ZeitBis", "?")} for tag in time_data.find_all("KlSt")}
    return time_data

def find_course(plan, course):
    for kl in plan.find_all("Kl"):
        if kl.find("Kurz").text.strip() == course:
            return kl
    return {"error": "chosen class has not been found"}


class Plan_Extractor():
    def __init__(self, school_num, date):
        self.school_num = school_num
        self.date = date
        with open('creds.json', encoding="utf-8") as f:
            self.credentials = json.load(f).get(school_num, None)
        if not self.credentials: raise CredentialsNotFound(school_num)
        year, month, day = int(date[:4]), int(date[4:6]), int(date[6:])
        self.d = datetime(year, month, day)
        if self.d.weekday() > 4: raise DayOnWeekend(date)
        self.data_folder = f"data/{self.school_num}_plans"
        os.makedirs(self.data_folder, exist_ok=True)
        self.get()
        self.zusatzinfo = find_zusatzinfo(self.day_data)
        self.freie_tage = self.parse_freie_tage()
        self.date_after = self.next_day()
        self.date_before = self.next_day(False)
    
    def get(self):
        if f"PlanKl{self.date}.xml" in os.listdir(self.data_folder):
            with open(f"{self.data_folder}/PlanKl{self.date}.xml", "r", encoding="utf-8") as f:
                self.day_data = BeautifulSoup(f.read(), "xml")
            return self.day_data
        plan_url = f"https://{self.credentials['api_server']}/{self.credentials['school_number']}/mobil/mobdaten/PlanKl{self.date}.xml"
        header_stripped = {"authorization": self.credentials["authorization"],}
        self.r = requests.get(plan_url, headers=header_stripped)
        if self.r.status_code == 404:
            print("error")
            return {"error": "plan not available"}
        with open("data/test2.xml", "w+", encoding="utf-8") as f:
            f.write(self.r.text)
        #self.day_data = BeautifulSoup(self.r.text, "html.parser")
        self.day_data = BeautifulSoup(self.r.text, "xml")
        return self.day_data
    
    def render(self, lessons):
        return Plan(self.school_num, self.date, lessons, self.zusatzinfo, date_after=self.date_after, date_before=self.date_before).render()
    
    def teacher_lessons(self, tag):
        teacher_lessons = []
        class_plans = self.day_data.find_all("Kl")
        for class_plan in class_plans:
            class_name = class_plan.find("Kurz").text.strip()
            class_lessons = class_plan.find_all("Std")
            for class_lesson in class_lessons:
                teacher = class_lesson.find("Le").text.strip()
                info = class_lesson.find("If").text.strip()
                if teacher == tag or tag in info:
                    teacher_lessons.append({**{"class": class_name}, **extract_data(class_lesson), "time_data": find_times(self.day_data, class_name)})
        return self.render(teacher_lessons)
    
    def room_lessons(self, room):
        room_lessons = []
        class_plans = self.day_data.find_all("Kl")
        for class_plan in class_plans:
            class_name = class_plan.find("Kurz").text.strip()
            class_lessons = class_plan.find_all("Std")
            for class_lesson in class_lessons:
                room_num = class_lesson.find("Ra").text.strip()
                info = class_lesson.find("If").text.strip()
                if room_num == room or room in info or room in room_num.split(" "): # last case: more than one room (example: "1208 1306")
                    room_lessons.append({**{"class": class_name}, **extract_data(class_lesson), "time_data": find_times(self.day_data, class_name)})
        return self.render(room_lessons)

    def get_plan_normal(self, course):
        course_data = find_course(self.day_data, course)
        time_data = find_times(self.day_data, course)
        pl = course_data.find("Pl")
        std_all = pl.find_all("Std")
        lessons = []
        for std in std_all:
            lessons.append({**{"class": course}, **extract_data(std), "time_data": time_data})
        return self.render(lessons)
    
    def set_preferences(self, preferences):
        self.preferences = preferences
    
    def get_plan_filtered_courses(self, course):
        group_list = MetaExtractor(self.school_num).group_list(course)
        unselected_courses = [elem[0] for elem in group_list if elem[0] not in self.preferences]
        normal_plan = self.get_plan_normal(course)
        return self.render([lesson for lesson in normal_plan["lessons"] if lesson["subject_name"] not in unselected_courses])
    
    def parse_freie_tage(self):
        datestamps = ["20" + elem.text for elem in self.day_data.find("FreieTage").find_all("ft")]
        return datestamps
    
    def next_day(self, forward=True):
        year, month, day = int(self.date[:4]), int(self.date[4:6]), int(self.date[6:])
        d = datetime(year, month, day)
        delta = 1 if forward else -1
        d += timedelta(days=delta)
        while d.strftime("%Y%m%d") in self.freie_tage or d.weekday() > 4:
            d += timedelta(days=delta)
        return d.strftime("%Y%m%d")
    
    def room_list(self):
        lessons_rooms = {}
        class_lessons = self.day_data.find_all("Std")
        for class_lesson in class_lessons:
            lesson_num = class_lesson.find("St")
            if not lesson_num: continue
            lesson_num = lesson_num.text.strip()
            info = class_lesson.find("If").text.strip()
            # there can be more than one room... (for example "1208 1306")
            room_nums = class_lesson.find("Ra").text.strip().split(" ")
            if not room_nums: continue
            if lesson_num not in lessons_rooms:
                lessons_rooms[lesson_num] = []
            for room_num in room_nums:
                if room_num not in lessons_rooms[lesson_num]:
                    lessons_rooms[lesson_num].append(room_num)
        self.lessons_rooms = lessons_rooms
        return lessons_rooms
    
    def free_rooms(self, all_rooms):
        free_rooms = self.room_list()
        for lesson_num in free_rooms:
            free_rooms[lesson_num] = [room for room in all_rooms if room not in free_rooms[lesson_num]]
        free_rooms_blocks = []
        for i in range(1, len(free_rooms)+1, 2):
            if str(i+1) in free_rooms:
                free_rooms_blocks.append(list(set(free_rooms[str(i)]) & set(free_rooms[str(i+1)])))
            else:
                free_rooms_blocks.append(free_rooms[str(i)])
        return free_rooms_blocks
    
    def get_timestamp(self):
        return self.day_data.find("zeitstempel").text.strip()
    
    def default_times(self):
        print("getting default times...")
        if not self.day_data.find("KlStunden"):
            return []
        klstunden = self.day_data.find("KlStunden").find_all("KlSt")
        klstunden = [{
            "lesson": elem.text.strip(),
            "start": elem.get("ZeitVon"),
            "end": elem.get("ZeitBis")
        } for elem in klstunden]
        return klstunden
    
    def current_lesson(self):
        current_time = datetime.now()
        cur_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        if current_time.strftime("%Y%m%d") != self.date:
            return 1
        # pause vor nem Block: nächster Block
        # im Block: aktueller Block
        current_time = datetime.now().strftime("%H:%M")
        default_times = self.default_times()
        lesson_ends_seconds = [int(time["end"].split(":")[0]) * 3600 + int(time["end"].split(":")[1]) * 60 for time in default_times]
        cur_lesson = 1
        for lesson in lesson_ends_seconds:
            if cur_seconds < lesson:
                break
            cur_lesson += 1
        return (cur_lesson+1) // 2

    def get_week(self):
        week_tag = self.day_data.find("woche")
        if not week_tag:
            return ""
        return {
            "1": "A",
            "2": "B"
        }.get(week_tag.text.strip(), "?")


def extract_metadata(school_num):
    if os.path.exists(f"data/{school_num}_plans/meta.json"):
        with open(f"data/{school_num}_plans/meta.json", "r", encoding="utf-8") as f:
            meta_data = json.load(f)
        return meta_data
    date_data = DateExtractor(school_num)
    dates = date_data.read_data()
    other_data = MetaExtractor(school_num)
    klassen = other_data.course_list()
    klassen_grouped = sort_klassen(klassen)
    teachers = other_data.teacher_list()
    rooms = other_data.room_list()
    default_times = other_data.default_times()
    meta_data = {
        "dates": dates,
        "all_dates": dates,
        "klassen": klassen,
        "klassen_grouped": klassen_grouped,
        "teachers": teachers,
        "rooms": rooms,
        "default_times": default_times
    }
    return meta_data


class MetaExtractor():
    def __init__(self, school_num):
        self.school_num = school_num
        with open('creds.json', encoding="utf-8") as f:
            self.credentials = json.load(f).get(school_num, None)
        self.data_folder = f"data/{self.school_num}_plans"
        os.makedirs(self.data_folder, exist_ok=True)
        self.get()
    
    def get(self):
        if "Klassen.xml" in os.listdir(self.data_folder):
            with open(f"{self.data_folder}/Klassen.xml", encoding="utf-8") as f:
                klassen_xml = f.read()
        else:
            plan_url = f"https://{self.credentials['api_server']}/{self.credentials['school_number']}/mobil/mobdaten/Klassen.xml"
            header_stripped = {"authorization": self.credentials["authorization"],}
            self.r = requests.get(plan_url, headers=header_stripped)
            klassen_xml = self.r.text
        #with open("data/klassen.xml", "w+") as f:
        #    f.write(self.r.text)
        self.soup = BeautifulSoup(klassen_xml, "xml")
    
    def teacher_list(self):
        if f"{self.school_num}_teachers.json" in os.listdir("data"):
            with open(f"data/{self.school_num}_teachers.json", encoding="utf-8") as f:
                teachers = json.load(f)
            return list(teachers.values())
        teachers = {}
        for elem in self.soup.find_all("UeNr"):
            cur_teacher = elem.get("UeLe")
            cur_subject = elem.get("UeFa")
            cur_subject = cur_subject if cur_subject not in ["KL", "AnSt", "FÖ"] else ""
            if not cur_teacher: continue
            if cur_teacher not in teachers:
                teachers[cur_teacher] = {"kuerzel": cur_teacher, "faecher": []}
            if cur_subject and cur_subject not in teachers[cur_teacher]["faecher"]:
                teachers[cur_teacher]["faecher"].append(cur_subject)
        for elem in self.soup.find_all("KKz"):
            cur_teacher = elem.get("KLe")
            if cur_teacher and cur_teacher not in teachers:
                teachers[cur_teacher] = {"kuerzel": cur_teacher, "faecher": []}
        teachers = list(teachers.values())
        return teachers

    def room_list(self):
        if f"{self.school_num}_rooms.json" in os.listdir("data"):
            with open(f"data/{self.school_num}_rooms.json", encoding="utf-8") as f:
                rooms = json.load(f)
            return rooms
        rooms = list(set([elem.text for elem in self.soup.find_all("Ra") if elem.text]))
        return rooms
    
    def course_list(self):
        courses = [elem.text for elem in self.soup.find_all("Kurz")]
        return courses

    def group_list(self, course):
        kl = [elem for elem in self.soup.find_all("Kl") if elem.find("Kurz") and elem.find("Kurz").text.strip() == course]
        if not kl: return []
        else: kl = kl[0]
        kurse = kl.find("Kurse")
        kurse = [elem.find("KKz") for elem in kurse.find_all("Ku")]
        kurse = [(elem.text.strip(), elem.get("KLe", "")) for elem in kurse if elem]
        return kurse
        unterricht = kl.find("Unterricht")
        unterricht = [elem.find("UeNr") for elem in unterricht.find_all("Ue")]
        unterricht = [(elem.get("UeFa", ""), elem.get("UeLe", ""), elem.get("UeGr", ""), elem.text.strip()) for elem in unterricht if elem]
        return unterricht
    
    def default_times(self):
        if not self.soup.find("KlStunden"):
            return []
        klstunden = self.soup.find("KlStunden").find_all("KlSt")
        klstunden = [{
            "lesson": elem.text.strip(),
            "start": elem.get("ZeitVon"),
            "end": elem.get("ZeitBis")
        } for elem in klstunden]
        return klstunden    

class DateExtractor():
    def __init__(self, school_num):
        self.school_num = school_num
        with open('creds.json', encoding="utf-8") as f:
            self.credentials = json.load(f).get(school_num, None)
        self.data_folder = f"data/{self.school_num}_plans"
        os.makedirs(self.data_folder, exist_ok=True)
        self.get()

    def random_data(self):
        bound_thing = f"---------Embt-Boundary--{self.hex_num}"
        self.data = f'{bound_thing}\nContent-Disposition: form-data; name="pw"\n\nI N D I W A R E\n{bound_thing}\nContent-Disposition: form-data; name="art"\n\nmobk\n{bound_thing}--\n'
    def random_content_type(self):
        self.headers["content-type"] = f"multipart/form-data; boundary=-------Embt-Boundary--{self.hex_num}"

    def get(self):
        if "vpdir.php" in os.listdir(self.data_folder):
            with open(f"data/{self.school_num}_plans/vpdir.php", encoding="utf-8") as f:
                data = f.read()
            data = data.split(";")[::2]
        else:
            self.headers = {}
            self.hex_num = 0
            self.random_data()
            self.random_content_type()
            data_url = f"https://{self.credentials['api_server']}/{self.school_num}/mobil/_phpmob/vpdir.php"
            self.headers["authorization"] = self.credentials["authorization"]
            r = requests.post(data_url, headers=self.headers, data=self.data)
            data = r.text.split(";")[::2]
        data.remove("Klassen.xml")
        data.remove('')
        data.sort()
        data = [elem.split(".")[0][6:] for elem in data]
        self.data = data
        return self.data
    
    def read_data(self):
        self.formatted_dates = [datetime.strptime(elem, "%Y%m%d").strftime("%d.%m.%Y") for elem in self.data]
        return list(zip(self.data, self.formatted_dates))
        
def get_default_date(date_list):
    now = datetime.now()
    if now.hour > 17:
        now += timedelta(days=1)
    today = now.date()
    dates = [datetime.strptime(elem, "%Y%m%d").date() for elem in date_list]
    if today in dates:
        return [today.strftime("%Y%m%d"), today.strftime("%d.%m.%Y")]
    future = sorted([elem for elem in dates if elem > today])
    if len(future) > 0:
        return [future[0].strftime("%Y%m%d"), future[0].strftime("%d.%m.%Y")]
    past = sorted([elem for elem in dates if elem < today])
    if len(past) > 0:
        return [past[-1].strftime("%Y%m%d"), past[-1].strftime("%d.%m.%Y")]
    return None


if __name__ == "__main__":
    p = Plan_Extractor("10001329", "20230127")
    print(p.get_week())
    #m = MetaExtractor("10001329")
    #c = m.course_list()
    #c = m.group_list("JG12")
    #print(c)
    #c = MetaExtractor("10001329").current_school_days_str()
    #print(len(c))
    #c = DateExtractor("10001329").default_date()
    #print(c)
    #pprint([datetime.strftime(elem, "%d.%m.%Y") for elem in c])