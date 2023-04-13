import random
import uuid

import jsonpickle
from flask import Flask, make_response, redirect, render_template, request, url_for

from pair import Pair

with open("pairs/cooking.json", "r") as f:
    pairs: dict[str, Pair] = jsonpickle.decode(f.read())


def get_random_pair(tags):
    if tags is None:
        return random.choice(list(pairs.values()))
    else:
        return random.choice(
            [
                pair
                for pair in pairs.values()
                if any(tag.lower() in pair.question.tags for tag in tags)
            ]
        )


# get existing cookie or create a new one
def get_user_id():
    user_id = request.cookies.get("user_id")
    if user_id is None:
        user_id = str(uuid.uuid4())
    return user_id


app = Flask(__name__)
app.debug = True


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        if request.form.get("consent") == "agree":
            return redirect(url_for("language_selection"))
        else:
            return render_template("no_consent.html")
    return render_template("consent_form.html")


@app.route("/language_selection", methods=["POST", "GET"])
def language_selection():
    return render_template("language_selection.html")


# @app.route("/task/<languages>")
# def task(languages):
#     languages_list = languages.split(",")
#     pair = get_random_pair(tags=languages_list)
#     return pair.question.body


app.run()
