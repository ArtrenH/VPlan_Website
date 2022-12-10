import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from models import Plan
from pprint import pprint

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
        year, month, day = int(date[:4]), int(date[4:6]), int(date[6:])
        d = datetime(year, month, day)
        if d.weekday() > 4: raise ValueError("day is on the weekend")
        with open('creds.json') as f:
            self.credentials = json.load(f).get(school_num, None)
        if not self.credentials: raise ValueError("school number not found")
        print("we got here...")
        self.get()
        self.zusatzinfo = find_zusatzinfo(self.day_data)
    
    def get(self):
        plan_url = f"https://z1.stundenplan24.de/schulen/{self.credentials['school_number']}/mobil/mobdaten/PlanKl{self.date}.xml"
        header_stripped = {"authorization": self.credentials["authorization"],}
        self.r = requests.get(plan_url, headers=header_stripped)
        if self.r.status_code == 404:
            print("error")
            return {"error": "plan not available"}
        with open("data/test2.xml", "w+") as f:
            f.write(self.r.text)
        #self.day_data = BeautifulSoup(self.r.text, "html.parser")
        self.day_data = BeautifulSoup(self.r.text, "xml")
        return self.r
    
    def render(self, lessons):
        return Plan(self.school_num, self.date, lessons, self.zusatzinfo).render()
    
    def teacher_lessons(self, tag):
        teacher_lessons = []
        class_plans = self.day_data.find_all("Kl")
        print(len(class_plans))
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
    


if __name__ == "__main__":
    p = Plan_Extractor("10001329", "20221209").get_plan_filtered_courses("JG12", ["de2"])
    pprint(p)