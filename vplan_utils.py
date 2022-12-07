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
    new_vplan_data = []
    tmp_vplan_data = sorted(vplan_data, key=lambda d: d['subject'])
    tmp_vplan_data = sorted(tmp_vplan_data, key=lambda d: d['class'])
    tmp_vplan_data = sorted(tmp_vplan_data, key=lambda d: d['info'])
    for i in range(0, len(tmp_vplan_data), 2):
        if equal_dicts(tmp_vplan_data[i], tmp_vplan_data[i+1], ["lesson", "begin", "end"]):
            tmp_vplan_data[i]["lesson"] = str(int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1))
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
    date_string = datetime.datetime(year, month, day).strftime("%a %d.%m.%Y")
    translated_date_string = date_string.replace("Mon", "Mo.").replace("Tue", "Di.").replace("Wed", "Mi.").replace("Thu", "Do.").replace("Fri", "Fr.")
    return translated_date_string

