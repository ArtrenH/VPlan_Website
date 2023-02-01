# coding=utf-8

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
        if k1 not in ignored and (k1 not in d2 or d2[k1] != v1) and k1 != "info":
            return False
    for k2, _ in d2.items():
        if k2 not in ignored and k2 not in d1 and k2 != "info":
            return False
    if set(d1["info"].split("; ")) == set(d2["info"].split("; ")):
        return True
    elif ("verlegt" in d1["info"]) or ("statt" in d1["info"]) or ("gehalten am" in d1["info"]):
        tmp_split1 = d1["info"].split(" ")
        tmp_split2 = d2["info"].split(" ")
        for i, word in enumerate(tmp_split1):
            if word.startswith("St."):
                tmp_st_word = f"{int((int(int(word[3:].replace(';', ''))) - 1)/2 + 1)}. Block{';' if word[-1:] == ';' else ''}"
                tmp_split1[i] = tmp_st_word
                tmp_split2[i] = tmp_st_word
        d1["info"] = ' '.join(tmp_split1)
        d2["info"] = ' '.join(tmp_split2)
        return True
    else:
        return False

def remove_duplicates(vplan_data):
    if len(vplan_data) < 2:
        return vplan_data
    new_vplan_data = []
    tmp_vplan_data = list(vplan_data)

    for i in range(0, len(tmp_vplan_data)):
        for j in range(0, len(tmp_vplan_data)):
            if (
                    # Um Duplikate zu verhindern
                    (not ("used" in tmp_vplan_data[i])) and 
                    (not ("used" in tmp_vplan_data[j]))
                ) and (
                    # Stunden sind maximal 1 voneinander entfernt
                    abs(int(tmp_vplan_data[i]["lesson"]) - int(tmp_vplan_data[j]["lesson"])) == 1
                ) and (
                    # Damit nicht z.B. Stunde 2 und 3 zusammengefasst werden können
                    (int(tmp_vplan_data[j]["lesson"]) < int(tmp_vplan_data[i]["lesson"]) and int(tmp_vplan_data[i]["lesson"]) % 2 == 0) or 
                    (int(tmp_vplan_data[i]["lesson"]) < int(tmp_vplan_data[j]["lesson"]) and int(tmp_vplan_data[j]["lesson"]) % 2 == 0)
                ):
                if equal_dicts(tmp_vplan_data[i], tmp_vplan_data[j], ["lesson", "begin", "end"]):
                    if tmp_vplan_data[i]["lesson"] < tmp_vplan_data[j]["lesson"]:
                        tmp_vplan_data[i]["lesson"] = str(int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1))
                        tmp_vplan_data[i]["end"] = tmp_vplan_data[j]["end"]
                        new_vplan_data.append(tmp_vplan_data[i])
                    else:
                        tmp_vplan_data[j]["lesson"] = str(int((int(tmp_vplan_data[j]["lesson"]) - 1)/2 + 1))
                        tmp_vplan_data[j]["end"] = tmp_vplan_data[i]["end"]
                        new_vplan_data.append(tmp_vplan_data[j])
                    tmp_vplan_data[i]["used"] = True
                    tmp_vplan_data[j]["used"] = True
    for i in range(0, len(tmp_vplan_data)):
        for j in range(0, len(tmp_vplan_data)):
            if ((not ("used" in tmp_vplan_data[i])) and (not ("used" in tmp_vplan_data[j]))) and (int(tmp_vplan_data[i]["lesson"]) - int(tmp_vplan_data[j]["lesson"]) == 1 or int(tmp_vplan_data[i]["lesson"]) - int(tmp_vplan_data[j]["lesson"]) == -1):
                tmp_vplan_data[i]["lesson"] = f'{int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1)} - 1'
                tmp_vplan_data[j]["lesson"] = f'{int((int(tmp_vplan_data[j]["lesson"]) - 1)/2 + 1)} - 2'
                new_vplan_data.append(tmp_vplan_data[i])
                new_vplan_data.append(tmp_vplan_data[j])
                tmp_vplan_data[i]["used"] = True
                tmp_vplan_data[j]["used"] = True
    for i in range(0, len(tmp_vplan_data)):
        if not "used" in tmp_vplan_data[i]:
            tmp_vplan_data[i]["lesson"] = f'{int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1)} - 1'
            new_vplan_data.append(tmp_vplan_data[i])
            tmp_vplan_data[i]["used"] = True

    sorted_data = sorted(new_vplan_data, key=lambda d: d['lesson'])
    return sorted_data

def convert_date_readable(date):
    time = ""
    try:
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:])
    except Exception:
        year = int(date[6:10])
        month = int(date[3:5])
        day = int(date[:2])
        time = " - " + date[12:17]
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
    return date_string + time

def sort_klassen(klassen_original):
    klassen = list(klassen_original)
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
                klassen.remove(elem)
        groups.append(cur_group)
    return groups


def classify_rooms(rooms):
    def get_house(room):
        return [char for char in room if char != "-"][0]
    def house_einteilung(rooms):
        houses = {}
        for room in rooms:
            if room == "Aula":
                houses["Aula"] = ["Aula"]
                continue
            if room.startswith("TH"):
                houses["TH"] = ["TH1", "TH2", "TH3"]
                continue
            if get_house(room) not in houses:
                houses[get_house(room)] = []
            houses[get_house(room)].append(room)
        return houses
    def get_floor_and_number(room_str):
        room = room_str
        vorzeichen = ""
        if room.startswith("-"):
            vorzeichen = "-"
            room = room[1:]
        if len(room) == 3:
            return (vorzeichen + "0", room[-2:])
        if len(room) == 4:
            return (vorzeichen + room[1], room[-2:])
        return [][0]
    def floor_einteilung(rooms):
        if rooms == ["Aula"]:
            return {"Aula": ["Aula"]}
        if rooms == ["TH1", "TH2", "TH3"]:
            return {"TH": ["TH1", "TH2", "TH3"]}
        floors = {}
        for room in rooms:
            floor, number = get_floor_and_number(room)
            if floor not in floors:
                floors[floor] = []
            floors[floor].append((number, room))
        return floors
    data = house_einteilung(rooms)
    for house in data:
        data[house] = floor_einteilung(data[house])
        for floor in data[house]:
            data[house][floor] = sorted(data[house][floor])
    new_keys = sorted(data.keys(), key=lambda x: int(x) if x not in ["Aula", "TH"] else 10)
    return {key: data[key] for key in new_keys}
