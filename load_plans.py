# coding=utf-8

import requests
import json
from tqdm import tqdm
import time
import os
from methods import DateExtractor, MetaExtractor
from vplan_utils import sort_klassen


class PlanLoader():
    def __init__(self, school_number):
        self.school_number = school_number
        with open("creds.json", "r", encoding="utf-8") as f:
            self.creds = json.load(f)
        if self.school_number not in self.creds:
            raise Exception("School number not found in creds.json")
        self.data_folder = f"data/{self.school_number}_plans"
        os.makedirs(self.data_folder, exist_ok=True)
        self.creds = self.creds[self.school_number]
        self.api_server = self.creds["api_server"]
        self.headers = {"authorization": self.creds["authorization"]}
        self.plan_txt = ""
    
    def vpdir(self):
        headers = self.headers
        hex_num = "0"
        bound_thing = f"---------Embt-Boundary--{hex_num}"
        data = f'{bound_thing}\nContent-Disposition: form-data; name="pw"\n\nI N D I W A R E\n{bound_thing}\nContent-Disposition: form-data; name="art"\n\nmobk\n{bound_thing}--\n'
        data_url = f"https://{self.api_server}/{self.school_number}/mobil/_phpmob/vpdir.php"
        headers["content-type"] = f"multipart/form-data; boundary=-------Embt-Boundary--{hex_num}"
        r = requests.post(data_url, headers=headers, data=data)
        if r.text != self.plan_txt:
            self.plan_txt = r.text
            return True
        return False
    
    def get_plans(self):
        if not self.plan_txt:
            print("first run")
            self.vpdir()
        with open(f"{self.data_folder}/vpdir.php", "w+", encoding="utf-8") as f:
            f.write(self.plan_txt)
        plan_files = [elem for elem in self.plan_txt.split(";")[::2] if elem]
        print(plan_files)
        for plan_file in tqdm(plan_files):
            self.get_plan(plan_file)
    
    def get_plan(self, plan_file):
        plan_url = f"https://{self.api_server}/{self.school_number}/mobil/mobdaten/{plan_file}"
        r = requests.get(plan_url, headers=self.headers)
        with open(f"{self.data_folder}/{plan_file}", "w", encoding="utf-8") as f:
            f.write(r.text)
    
    def check_infinite(self):
        while True:
            try: cur_val = self.vpdir()
            except:
                print("error")
                cur_val = False
            if cur_val:
                self.get_plans()
                self.aktualisiere_files()
            else: print("no change")
            time.sleep(30)
    
    def load_dates(self):
        def format_date(filename):
            date_str = filename[6:-4]
            return [
                date_str,
                f"{date_str[6:8]}.{date_str[4:6]}.{date_str[:4]}"
            ]
        filenames = [format_date(filename) for filename in os.listdir(self.data_folder) if filename.startswith("PlanKl") and filename.endswith(".xml")]
        return filenames

    def aktualisiere_files(self):
        date_data = DateExtractor(self.school_number)
        #dates = date_data.read_data()
        dates = self.load_dates()
        other_data = MetaExtractor(self.school_number)
        klassen = other_data.course_list()
        klassen_grouped = sort_klassen(klassen)
        teachers = other_data.teacher_list()
        rooms = other_data.room_list()
        default_times = other_data.default_times()
        data = {
            "dates": dates,
            "klassen": klassen,
            "klassen_grouped": klassen_grouped,
            "teachers": teachers,
            "rooms": rooms,
            "default_times": default_times
        }
        with open(f"{self.data_folder}/meta.json", "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("Metadaten aktualisiert")

if __name__ == "__main__":
    p = PlanLoader("10001329")
    p.check_infinite()
