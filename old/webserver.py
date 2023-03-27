import ast
import json
import random
from datetime import datetime
from threading import Lock

from alive_progress import alive_it
from flask import Flask, Markup, app, redirect, render_template, request, url_for

from so_gpt4 import Config, StackOveflowDatabase

app = Flask(__name__)

mutex = Lock()

config = Config(
    cutoff_date=datetime.fromisoformat("2021-09-30"),
    posts_path="./data/stackoverflow/Posts.xml",
    total=58329357,
    time_format="%Y-%m-%dT%H:%M:%S.%f",
    raw_pairs_path="./json/raw_pairs.json",
    pairs_path="./json/pairs.json",
    gpt_prompt="You are a helpful assistant which specializes in answering Stack Overflow questions on the Stack Overflow forum.",
    gpt_model="gpt-3.5-turbo",
    threads=16,
)


def write_json(pairs, config, path):
    formatted_pairs = []

    for pair in alive_it(pairs.values(), title="Formatting pairs..."):
        formatted_pairs.append(pair.to_json(config))

    print("Writing pairs...")

    with open(path, "w") as f:
        json.dump(formatted_pairs, f)


random.seed(69420)

raw_pairs_database = StackOveflowDatabase(config)

write_json(
    raw_pairs_database.filter_by_tags(["cobol"]),
    raw_pairs_database.config,
    "json/cobol.json",
)

quit()


@app.route("/", methods=["GET", "POST"])
def first_page():
    if request.method == "GET":
        language_options = request.values.getlist("option")
        if len(language_options) != 0:
            print("language_options", language_options)
            return redirect(url_for("survey_page", language_options=language_options))
    return render_template("first_page.html")


@app.route("/survey_page/<language_options>", methods=["GET", "POST"])
def survey_page(language_options=None):
    language_options = ast.literal_eval(language_options)
    print("received language options:", language_options)
    return render_template(
        "survey_page.html",
        languages=", ".join(language_options[:-1] + ["and " + language_options[-1]]),
    )


if __name__ == "__main__":
    app.run(debug=True)
