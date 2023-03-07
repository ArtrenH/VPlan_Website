import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from vplan_utils import sort_klassen


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