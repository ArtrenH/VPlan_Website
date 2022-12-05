# Namenserklärungen:
# group: Klasse, z.B. Jg12, 6/1
# course: Kurs, z.B. eth1, lat



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
        self.teacher_changed = "mooorning"
        self.room_changed = data_dict.get("room_changed", False)

        self.link_start = f"/../{self.school_num}/{self.date}"

    
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
        }
    
    def get_room_link(self):
        if self.room == "--":
            return "#"
        return f"{self.link_start}/raumplan/{self.room}"
        #return f"../raumplan/{self.room}"
    
    def get_teacher_link(self):
        if self.teacher == "--":
            return "#"
        return f"{self.link_start}/lehrerplan/{self.teacher}"
        #return f"../lehrerplan/{self.teacher}"
    
    def get_class_link(self):
        if self.class_name == "--":
            return "#"
        return f"{self.link_start}/klassenplan/{self.class_name.replace('/', '_')}"
        #return f"../klassenplan/{self.class_name.replace('/', '_')}"

class Plan():
    def __init__(self, school_num, date, lesson_dicts):
        self.school_num = school_num
        self.lesson_dicts = lesson_dicts
        self.lessons = [Lesson(lesson_dict, school_num, date) for lesson_dict in lesson_dicts]
    
    def render(self):
        return sorted([lesson.render() for lesson in self.lessons], key=lambda x: x["lesson"])



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