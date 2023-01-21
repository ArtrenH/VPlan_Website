# coding=utf-8

class DayOnWeekend(Exception):
    def __init__(self, date):
        super().__init__(f"Your requested date {date} is on the weekend.")


class CredentialsNotFound(Exception):
    def __init__(self, school_num):
        super().__init__(f"No credentials found for school with number {school_num}")