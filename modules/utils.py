import os
import re
import pymongo
from bson import ObjectId
from random import choice
from werkzeug.security import safe_join
import contextlib
import hashlib
import json

from flask import Flask, make_response, render_template
from flask_login import UserMixin, current_user

from dotenv import load_dotenv
load_dotenv()

db = pymongo.MongoClient(os.getenv("MONGO_URL") if os.getenv("MONGO_URL") else "", 27017).vplan
users = db.user

def update_settings(user_settings):
    new_settings = {}
    try:
        new_settings["show_plan_toasts"] = bool(user_settings.get("show_plan_toasts", False))
    except Exception:
        return make_response('Invalid value for show_plan_toasts', 400)
    try:
        new_settings["day_switch_keys"] = bool(user_settings.get("day_switch_keys", True))
    except Exception:
        return make_response('Invalid value for day_switch_keys', 400)
    new_settings["background_color"] = user_settings.get("background_color", "#121212")
    if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', new_settings["background_color"]):
        return make_response('Invalid Color for background_color', 400)
    new_settings["accent_color"] = user_settings.get("accent_color", "#BB86FC")
    if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', new_settings["accent_color"]):
        return make_response('Invalid Color for accent_color', 400)
    users.update_one({'_id': ObjectId(current_user.get_id())}, {"$set": {'settings': new_settings}})
    return make_response('success', 200)

def render_template_wrapper(template_name, *args, **kwargs):
    tmp_user = users.find_one({"_id": ObjectId(current_user.get_id())})
    logged_in = tmp_user is not None
    user_settings = {}
    random_greeting = "Startseite"
    greetings = [
        "Grüß Gott {name}!",
        "Moin {name}!",
        "Moinsen {name}!",
        "Yo Moinsen {name}!",
        "Servus {name}!",
        "Hi {name}!",
        "Hey {name}!",
        "Hallo {name}!",
        "Hallöchen {name}!",
        "Halli-Hallo {name}!",
        "Hey, was geht ab {name}?",
        "Tachchen {name}!",
        "Na, alles fit, {name}?",
        "Alles Klärchen, {name}?",
        "Jo Digga {name}!",
        "Heyho {name}!",
        "Ahoihoi {name}!",
        "Aloha {name}!",
        "Alles cool im Pool, {name}?",
        "Alles klar in Kanada, {name}?",
        "Alles Roger in Kambodscha, {name}?",
        "Hallöchen mit Öchen {name}!",
        "{name} joined the game",
        "Alles nice im Reis?",
        "Alles cool in Suhl?",
        "Howdy {name}!",
    ]

    if logged_in:
        user_settings = tmp_user.get("settings", {})
        random_greeting = choice(greetings).format(name=tmp_user["nickname"])

    return render_template(f"{template_name}.html", logged_in=logged_in, random_greeting=random_greeting, user_settings=json.dumps(user_settings), py_user_settings=user_settings, *args, **kwargs)

class User(UserMixin):
    def __init__(self, mongo_id):
        self.mongo_id = mongo_id

    def get_id(self):
        return self.mongo_id

class AddStaticFileHashFlask(Flask):
    def __init__(self, *args, **kwargs):
        super(AddStaticFileHashFlask, self).__init__(*args, **kwargs)
        self._file_hash_cache = {}
    def inject_url_defaults(self, endpoint, values):
        super(AddStaticFileHashFlask, self).inject_url_defaults(endpoint, values)
        if endpoint == "static" and "filename" in values:
            filepath = safe_join(self.static_folder, values["filename"])
            if os.path.isfile(filepath):
                cache = self._file_hash_cache.get(filepath)
                mtime = os.path.getmtime(filepath)
                if cache != None:
                    cached_mtime, cached_hash = cache
                    if cached_mtime == mtime:
                        values["h"] = cached_hash
                        return
                h = hashlib.md5()
                with contextlib.closing(open(filepath, "rb")) as f:
                    h.update(f.read())
                h = h.hexdigest()
                self._file_hash_cache[filepath] = (mtime, h)
                values["h"] = h

def get_user(user_id):
    try:
        return users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return


def set_user_preferences(user_id, preferences):
    users.update_one({'_id': ObjectId(user_id)}, {'$set': {'preferences': preferences}})
    return "Success"