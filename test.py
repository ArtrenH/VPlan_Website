import requests, json
import gzip

url = "https://z1.stundenplan24.de/schulen/10001329/mobil/_phpmob/vpdir.php"
headers = {
    "user-agent": "Indiware",
}
with open("creds.json", "r") as f:
    creds = json.load(f)
headers["authorization"] = creds["10001329"]["authorization"]


def random_data(hex_num):
    bound_thing = f"---------Embt-Boundary--{hex_num}"
    return f'{bound_thing}\nContent-Disposition: form-data; name="pw"\n\nI N D I W A R E\n{bound_thing}\nContent-Disposition: form-data; name="art"\n\nmobk\n{bound_thing}--\n'
def random_content_type(hex_num):
    return f"multipart/form-data; boundary=-------Embt-Boundary--{hex_num}"

hex_num = "bitteerklaertmirwasdashierist" #(normally smth like 58D7EC262F37FAC6)
headers["content-type"] = random_content_type(hex_num)
data = random_data(hex_num)

r = requests.post(url, headers=headers, data=data)
from pprint import pprint
pprint(r.text.split(";"))
