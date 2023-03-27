import ast
import hashlib
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for

from database import Database, Pair

app = Flask(__name__)
app.config["SECRET_KEY"] = hashlib.sha256("haha69420".encode()).digest()

db = Database.load_from_json("pairs.json")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        language_options = request.values.getlist("option")
        if len(language_options) != 0:
            print("language_options", language_options)
            session["language_options"] = language_options
            return redirect(url_for("survey"))
    return render_template("index.html")


@app.route("/survey", methods=["GET", "POST"])
def survey(language_options=None):
    language_options = session.get("language_options")
    print("received language options:", language_options)
    if language_options:
        if len(language_options) == 1:
            languages = language_options[0]
        else:
            languages = ", ".join(
                language_options[:-1] + ["and " + language_options[-1]]
            )
    else:
        languages = None
    pairs = db.filter(
        lambda p: any(
            [p.has_tags([language_option]) for language_option in language_options]
        )
    ).pairs
    return render_template("survey.html", languages=languages, things=pairs)


if __name__ == "__main__":
    app.run(debug=True)
