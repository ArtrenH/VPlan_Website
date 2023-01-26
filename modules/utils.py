import os
import pymongo
from bson import ObjectId
from random import choice

from flask import render_template
from flask_login import UserMixin, current_user

from dotenv import load_dotenv
load_dotenv()

db = pymongo.MongoClient(os.getenv("MONGO_URL") if os.getenv("MONGO_URL") else "", 27017).vplan
users = db.user


def render_template_wrapper(*args, **kwargs):
    tmp_user = users.find_one({"_id": ObjectId(current_user.get_id())})
    logged_in = tmp_user is not None
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
        "Alles cool in Suhl?"
    ]

    if logged_in:
        random_greeting = choice(greetings).format(name=tmp_user["nickname"])

    return render_template(logged_in=logged_in, random_greeting=random_greeting, *args, **kwargs)

class User(UserMixin):
    def __init__(self, mongo_id):
        self.mongo_id = mongo_id

    def get_id(self):
        return self.mongo_id