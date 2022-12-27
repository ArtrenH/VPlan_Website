import datetime

def add_spacers(vplan_data):
    prev_lesson = 1
    for elem in vplan_data:
        converted_lesson = None
        try:
            converted_lesson = int(elem["lesson"])
        except Exception:
            if(elem["lesson"].split(" - ")[1] == "2"):
                continue
            converted_lesson = int(elem["lesson"].split(" - ")[0])
        
        if prev_lesson + 1 == converted_lesson:
            elem["spacer"] = True
        
        prev_lesson = converted_lesson

    return vplan_data

def equal_dicts(d1, d2, ignore_keys):
    ignored = set(ignore_keys)
    for k1, v1 in d1.items():
        if k1 not in ignored and (k1 not in d2 or d2[k1] != v1):
            return False
    for k2, v2 in d2.items():
        if k2 not in ignored and k2 not in d1:
            return False
    return True

def remove_duplicates(vplan_data):
    if len(vplan_data) < 2:
        return vplan_data
    new_vplan_data = []
    tmp_vplan_data = sorted(vplan_data, key=lambda d: d['subject'])
    tmp_vplan_data = sorted(tmp_vplan_data, key=lambda d: d['class'])
    tmp_vplan_data = sorted(tmp_vplan_data, key=lambda d: d['info'])
    for i in range(0, len(tmp_vplan_data), 2):
        if equal_dicts(tmp_vplan_data[i], tmp_vplan_data[i+1], ["lesson", "begin", "end"]):
            tmp_vplan_data[i]["lesson"] = str(int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1))
            tmp_vplan_data[i]["end"] = tmp_vplan_data[i+1]["end"]
            new_vplan_data.append(tmp_vplan_data[i])
        else:
            tmp_vplan_data[i]["lesson"] = f'{int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1)} - 1'
            tmp_vplan_data[i+1]["lesson"] = f'{int((int(tmp_vplan_data[i+1]["lesson"]) - 1)/2 + 1)} - 2'
            new_vplan_data.append(tmp_vplan_data[i])
            new_vplan_data.append(tmp_vplan_data[i+1])
    return sorted(new_vplan_data, key=lambda d: d['lesson'])

def convert_date_readable(date):
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:])
    date_string = datetime.datetime(year, month, day).strftime("%a %d. %B")
    translation_arr = [
        # Weekdays
        ["Mon", "Montag"],
        ["Tue", "Dienstag"],
        ["Wed", "Mittwoch"],
        ["Thu", "Donnerstag"],
        ["Fri", "Freitag"],
        # Months
        ["January", "Januar"],
        ["February", "Februar"],
        ["March", "März"],
        ["April", "April"],
        ["May", "Mai"],
        ["June", "Juni"],
        ["July", "Juli"],
        ["October", "Oktober"],
        ["December", "Dezember"],
    ]
    for translation in translation_arr:
        date_string = date_string.replace(translation[0], translation[1])
    return date_string

def sort_klassen(klassen):
    groups = []
    while len(klassen) > 0:
        cur_klasse = klassen[0]
        if "/" in cur_klasse:
            cur_group = [elem for elem in klassen if elem.split("/")[0] == cur_klasse.split("/")[0]]
        elif "-" in cur_klasse:
            cur_group = [elem for elem in klassen if elem.split("-")[0] == cur_klasse.split("-")[0]]
        elif cur_klasse.isdigit():
            cur_group = [elem for elem in klassen if elem.isdigit()]
        elif not cur_klasse[0].isdigit():
            identifier = "".join([char for char in cur_klasse if not char.isdigit()])
            cur_group = [elem for elem in klassen if elem.startswith(identifier)]
        elif cur_klasse[0].isdigit():
            identifier = "".join([char for char in cur_klasse if char.isdigit()])
            cur_group = [elem for elem in klassen if elem.startswith(identifier)]
        else:
            cur_group = [cur_klasse]
        for elem in cur_group:
            if elem in klassen:
                del klassen[klassen.index(elem)]
        groups.append(cur_group)
    return groups

def classify_rooms():
    return