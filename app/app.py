from database import reports_collection
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

reports = []

@app.route("/")
def home():
    return render_template("index.html", reports=reports)

@app.route("/add", methods=["POST"])
def add_report():

    title = request.form["title"]
    description = request.form["description"]

    print("Saving to MongoDB:", title, description)

    reports_collection.insert_one({
        "title": title,
        "description": description
    })

    return redirect("/")

@app.route("/delete/<title>")
def delete_report(title):

    global reports
    reports = [r for r in reports if r["title"] != title]

    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)