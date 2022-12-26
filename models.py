# Namenserklärungen:
# group: Klasse, z.B. JG12, 6/1
# course: Kurs, z.B. eth1, lat
import json
import urllib
from flask import url_for


class Lesson():
    def __init__(self, data_dict, school_num, date):
        self.data_dict = data_dict
        self.date = date
        self.school_num = school_num
        self.course_id = data_dict.get("course_id", "--")
        self.class_name = data_dict.get("class", "--")
        self.lesson = data_dict.get("lesson", "--")
        self.room = data_dict.get("room", "--")
        self.subject = data_dict.get("subject", "--")
        self.subject_name = data_dict.get("subject_name", "--")
        self.info = data_dict.get("info", "--")
        self.teacher = data_dict.get("teacher", "--")

        self.subject_changed = data_dict.get("subject_changed", False)
        self.teacher_changed = data_dict.get("teacher_changed", False)
        self.room_changed = data_dict.get("room_changed", False)

        self.time_data = data_dict.get("time_data", {}).get(self.lesson, None)
        if not self.time_data:
            with open("default_time_data.json", "r") as f:
                self.time_data = json.load(f).get(self.lesson, "?")
        self.begin = self.time_data.get("begin", "?")
        self.end = self.time_data.get("end", "?")

    
    def render(self):
        return {
            "class": self.class_name,
            "lesson": self.lesson,
            "room": self.room,
            "subject": self.subject,
            "subject_name": self.subject_name,
            "info": self.info,
            "teacher": self.teacher,
            "subject_changed": self.subject_changed,
            "teacher_changed": self.teacher_changed,
            "room_changed": self.room_changed,
            "room_link": self.get_room_link(),
            "teacher_link": self.get_teacher_link(),
            "class_link": self.get_class_link(),
            "begin": self.begin,
            "end": self.end
        }
    
    def get_class_link(self):
        if self.class_name == "--":
            return "#"
        return url_for('handle_plan', schulnummer=self.school_num, date=self.date, type="klasse", value=self.class_name)
    
    def get_teacher_link(self):
        if self.teacher == "--":
            return "#"
        return url_for('handle_plan', schulnummer=self.school_num, date=self.date, type="teacher", value=self.teacher)
    
    def get_room_link(self):
        if self.room == "--":
            return "#"
        return url_for('handle_plan', schulnummer=self.school_num, date=self.date, type="room", value=self.room)
    

class Zusatzinfo():
    def __init__(self, zusatzinfo_lst):
        self.zusatzinfo_lst = zusatzinfo_lst
    
    def render(self):
        return self.zusatzinfo_lst

class Plan():
    def __init__(self, school_num, date, lesson_dicts, zusatzinfo_lst, **kwargs):
        self.school_num = school_num
        self.lesson_dicts = lesson_dicts
        self.lessons = [Lesson(lesson_dict, school_num, date) for lesson_dict in lesson_dicts]
        self.zusatzinfo_lst = zusatzinfo_lst
        self.new_dates = [
            kwargs.get("date_before", date),
            date,
            kwargs.get("date_after", date),
        ]
    
    def render(self):
        return {
            "lessons": sorted([lesson.render() for lesson in self.lessons], key=lambda x: x["lesson"]),
            "zusatzinfo": Zusatzinfo(self.zusatzinfo_lst).render(),
            "new_dates": self.new_dates
        }


class SharedCourse():
    def __init__(self, school_num, course_dict):
        self.school_num = school_num
        self.course_dict = course_dict
        self.course_name = course_dict.get("course", "")
        self.teacher = course_dict.get("teacher", "")

    def render(self):
        return {
            "course": self.course_name,
            "teacher": self.teacher
        }

class Course():
    def __init__(self, school_num, course_dict):
        self.school_num = school_num
        self.course_dict = course_dict
        self.id = course_dict.get("id", "")
        self.teacher = course_dict.get("teacher", "")
        self.subject = course_dict.get("subject", "")
        self.course = course_dict.get("course", "")
        self.shared_course = SharedCourse(self.school_num, {"course": self.course, "teacher": self.teacher}) if self.course else {}

    def render(self):
        return {
            "id": self.id,
            "teacher": self.teacher,
            "subject": self.subject,
            "course": self.course,
            "shared_course": self.shared_course.render() if self.shared_course else {}
        }

class Group():
    def __init__(self, school_num, course_dicts):
        self.school_num = school_num
        self.course_dicts = course_dicts
        self.courses = [Course(school_num, course_dict) for course_dict in self.course_dicts]

    def render(self):
        return [course.render() for course in self.courses]