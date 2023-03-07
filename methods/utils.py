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

def extract_klausur_data(klausur_soup):
    return { 
        tag[2:].lower(): klausur_soup.find(tag).text.strip() for tag in (
            "KlJahrgang", "KlKurs", "KlKursleiter", "KlStunde", "KlBeginn", "KlDauer", "KlKinfo"
        )
    }