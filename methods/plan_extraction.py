import os
import json
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from .meta_extraction import MetaExtractor


from .utils import *
from models import *
from errors import *


class Plan_Extractor():
    def __init__(self, school_num, date, caching=True):
        self.school_num = school_num
        self.date = date
        self.caching = caching
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
        self.klausuren = []
        self.freie_tage = self.parse_freie_tage()
        self.date_after = self.next_day()
        self.date_before = self.next_day(False)
    
    def get(self):
        print("getting plan")
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
        return Plan(self.school_num, self.date, lessons, self.zusatzinfo, klausuren_lst=self.klausuren, date_after=self.date_after, date_before=self.date_before).render()
    
    def teacher_lessons(self, tag):
        if self.caching:
            if os.path.exists(f"data/{self.school_num}_plans/{self.date}/teachers.json"):
                with open(f"data/{self.school_num}_plans/{self.date}/teachers.json", "r") as f:
                    data = json.load(f)
                    if tag in data:
                        return data[tag]
        teacher_lessons = []
        teacher_name = None
        if os.path.exists(f"data/{self.school_num}_teachers.json"):
            with open(f"data/{self.school_num}_teachers.json", "r", encoding='utf-8') as f:
                teacher_name = json.load(f).get(tag, {}).get("name", None)
        class_plans = self.day_data.find_all("Kl")
        for class_plan in class_plans:
            class_name = class_plan.find("Kurz").text.strip()
            class_lessons = class_plan.find_all("Std")
            for class_lesson in class_lessons:
                teacher = class_lesson.find("Le").text.strip()
                info = class_lesson.find("If").text.strip()
                if teacher == tag or tag in info:
                    teacher_lessons.append({**{"class": class_name}, **extract_data(class_lesson), "time_data": find_times(self.day_data, class_name)})
                if teacher_name and teacher_name in info:
                    teacher_lessons.append({**{"class": class_name}, **extract_data(class_lesson), "time_data": find_times(self.day_data, class_name)})
        return self.render(teacher_lessons)
    
    def room_lessons(self, room):
        if self.caching:
            if os.path.exists(f"data/{self.school_num}_plans/{self.date}/rooms.json"):
                with open(f"data/{self.school_num}_plans/{self.date}/rooms.json", "r") as f:
                    data = json.load(f)
                    if room in data:
                        return data[room]
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
        if self.caching:
            if os.path.exists(f"data/{self.school_num}_plans/{self.date}/courses.json"):
                with open(f"data/{self.school_num}_plans/{self.date}/courses.json", "r") as f:
                    data = json.load(f)
                    if course in data:
                        return data[course]
        course_data = find_course(self.day_data, course)
        time_data = find_times(self.day_data, course)
        pl = course_data.find("Pl")
        std_all = pl.find_all("Std")
        lessons = []
        for std in std_all:
            lessons.append({**{"class": course}, **extract_data(std), "time_data": time_data})
        klausuren_tag = course_data.find("Klausuren")
        if klausuren_tag:
            self.klausuren = klausuren_tag.find_all("Klausur")
            self.klausuren = [extract_klausur_data(klausur) for klausur in self.klausuren]
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

