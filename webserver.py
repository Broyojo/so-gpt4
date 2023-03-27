from flask import Flask, redirect, render_template, request, url_for

from database import Database, Pair

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("first_page.html")


@app.route("/survey")
def survey():
    pass


app.run(debug=True)
