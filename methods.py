import json
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from pprint import pprint
from models import Plan
from errors import DayOnWeekend, CredentialsNotFound

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
        d = datetime(year, month, day)
        if d.weekday() > 4: raise DayOnWeekend(date)
        self.get()
        self.zusatzinfo = find_zusatzinfo(self.day_data)
        self.freie_tage = self.parse_freie_tage()
        self.date_after = self.next_day()
        self.date_before = self.next_day(False)
    
    def get(self):
        plan_url = f"https://z1.stundenplan24.de/schulen/{self.credentials['school_number']}/mobil/mobdaten/PlanKl{self.date}.xml"
        header_stripped = {"authorization": self.credentials["authorization"],}
        self.r = requests.get(plan_url, headers=header_stripped)
        if self.r.status_code == 404:
            print("error")
            return {"error": "plan not available"}
        with open("data/test2.xml", "w+", encoding="utf-8") as f:
            f.write(self.r.text)
        #self.day_data = BeautifulSoup(self.r.text, "html.parser")
        self.day_data = BeautifulSoup(self.r.text, "xml")
        return self.r
    
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
                if room_num == room or room in info:
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
    
    def get_plan_filtered_courses(self, course, courses):
        normal_plan= self.get_plan_normal(course)
        return self.render([lesson for lesson in normal_plan[0] if lesson["subject_name"] in courses or lesson["subject"] in courses])
    
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


class MetaExtractor():
    def __init__(self, school_num):
        self.school_num = school_num
        with open('creds.json') as f:
            self.credentials = json.load(f).get(school_num, None)
        self.get()
    
    def get(self):
        plan_url = f"https://z1.stundenplan24.de/schulen/{self.credentials['school_number']}/mobil/mobdaten/Klassen.xml"
        header_stripped = {"authorization": self.credentials["authorization"],}
        self.r = requests.get(plan_url, headers=header_stripped)
        print(self.r)
        #with open("data/klassen.xml", "w+") as f:
        #    f.write(self.r.text)
        self.soup = BeautifulSoup(self.r.text, "xml")
    
    def room_list(self):
        rooms = list(set([elem.text for elem in self.soup.find_all("Ra") if elem.text]))
        return rooms
    
    def course_list(self):
        courses = [elem.text for elem in self.soup.find_all("Kurz")]
        return courses
    
    def free_days(self):
        datestamps = ["20" + elem.text for elem in self.soup.find("FreieTage").find_all("ft")]
        datestamps = [datetime.strptime(datestamp, "%Y%m%d") for datestamp in datestamps]
        self.free_days_datetimes = datestamps
        return datestamps
    
    def weekends(self):
        self.free_days()
        min_free_day = min(self.free_days_datetimes)
        max_free_day = max(self.free_days_datetimes)
        weekends = []
        for i in range((max_free_day - min_free_day).days + 1):
            day = min_free_day + timedelta(days=i)
            if day.weekday() > 4:
                weekends.append(day)
        self.free_days_datetimes.extend(weekends)
        self.free_days_datetimes.sort()
        return weekends

    def all_free_days(self):
        self.weekends()
        return self.free_days_datetimes
    
    def school_days(self):
        self.all_free_days()
        min_free_day = min(self.free_days_datetimes)
        max_free_day = max(self.free_days_datetimes)
        school_days = [min_free_day + timedelta(days=i) for i in range((max_free_day - min_free_day).days + 1)]
        school_days = [elem for elem in school_days if elem not in self.free_days_datetimes]
        self.school_days_datetimes = school_days
        self.school_days_datetimes.sort()
        return self.school_days_datetimes
    
    def current_school_days(self):
        self.school_days()
        today = datetime.now()
        cur_day_lst = self.school_days_datetimes
        cur_day_lst.append(today)
        cur_day_lst.sort()
        ind = cur_day_lst.index(today)
        cur_day_lst.remove(today)
        return cur_day_lst[ind-5:ind+10]
    
    def current_school_days_str(self):
        return [[datetime.strftime(elem, "%d.%m.%Y"), datetime.strftime(elem, "%Y%m%d")] for elem in self.current_school_days()]

if __name__ == "__main__":
    #p = Plan_Extractor("10001329", "20221209").get_plan_filtered_courses("JG12", ["de2"])
    #pprint(p)
    c = MetaExtractor("10001329").current_school_days_str()
    #print(len(c))
    print(c)
    #pprint([datetime.strftime(elem, "%d.%m.%Y") for elem in c])