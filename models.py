class Lesson():
    def __init__(self, data_dict, school_num, date):
        self.data_dict = data_dict
        self.date = date
        self.school_num = school_num
        self.class_name = data_dict.get("class", "--")
        self.lesson = data_dict.get("lesson", "--")
        self.room = data_dict.get("room", "--")
        self.subject = data_dict.get("subject", "--")
        self.subject_name = data_dict.get("subject_name", "--")
        self.info = data_dict.get("info", "--")
        self.teacher = data_dict.get("teacher", "--")

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
    def __init__(self, lesson_dicts, school_num, date):
        self.lesson_dicts = lesson_dicts
        self.lessons = [Lesson(lesson_dict, school_num, date) for lesson_dict in lesson_dicts]
    
    def render(self):
        return sorted([lesson.render() for lesson in self.lessons], key=lambda x: x["lesson"])
