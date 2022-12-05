# VPlan_Website
Flask Project for viewing data from stundenplan24 in a nice way

## How to use:

1. Clone the repo
2. create "creds.json" that looks like this
```json
{
    "{your school's number}": {
        "school_number": "{your school's number}",
        "school_name": "{your school's name}",
        "username": "{your login username}",
        "password": "{your login password}",
        "authorization": "Basic {b64encoded username:password}"
    }
}
```
3. create a venv
```bash
python3 -m venv venv
source venv/bin/activate
```
4. install requirements
```bash
pip3 install -r requirements.txt
```
5. run server
```bash
python3 server.py
```
6. try some urls (currently not documented)
