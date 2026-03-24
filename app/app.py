from flask import Flask, render_template, request, redirect, session, send_file
from database import reports_collection
from threat_detection import detect_threat

import logging
import csv
import io
import os

from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "devsecops_secret"

# Upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

logging.basicConfig(filename="security.log", level=logging.INFO)

# Users
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "analyst": {"password": "analyst123", "role": "analyst"}
}


# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:

            session["user"] = username
            session["role"] = users[username]["role"]

            logging.info(f"{username} logged in")

            return redirect("/")

        else:
            return render_template("login.html", error="Invalid login")

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():

    logging.info(f"{session.get('user')} logged out")

    session.clear()

    return redirect("/login")


# HOME
@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    query = request.args.get("search")

    if query:
        reports = list(reports_collection.find({
            "title": {"$regex": query, "$options": "i"}
        }))
    else:
        reports = list(reports_collection.find())

    high_threats = reports_collection.count_documents({"threat_level":"HIGH"})
    low_threats = reports_collection.count_documents({"threat_level":"LOW"})

    last_high_threat = reports_collection.find_one(
        {"threat_level":"HIGH"},
        sort=[("_id",-1)]
    )

    return render_template(
        "index.html",
        reports=reports,
        high_threats=high_threats,
        low_threats=low_threats,
        alert=last_high_threat,
        role=session["role"]
    )


# ADD INCIDENT
@app.route("/add", methods=["POST"])
def add_report():

    if session.get("role") != "admin":
        return "Access denied"

    title = request.form["title"]
    description = request.form["description"]

    threat_level = detect_threat(title + " " + description)

    # file upload
    file = request.files["evidence"]

    filename = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    timeline = [{
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "event": "Incident Created"
    }]

    reports_collection.insert_one({
        "title": title,
        "description": description,
        "threat_level": threat_level,
        "status": "New",
        "timeline": timeline,
        "evidence": filename
    })

    logging.info(f"Incident reported: {title}")

    return redirect("/?view=incidents")


# RESOLVE INCIDENT
@app.route("/resolve/<title>")
def resolve_incident(title):

    if session.get("role") != "admin":
        return "Access denied"

    incident = reports_collection.find_one({"title":title})

    timeline = incident.get("timeline",[])

    timeline.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "event": "Incident Resolved"
    })

    reports_collection.update_one(
        {"title":title},
        {"$set":{
            "status":"Resolved",
            "timeline":timeline
        }}
    )

    logging.info(f"Incident resolved: {title}")

    return redirect("/?view=incidents")


# DELETE INCIDENT
@app.route("/delete/<title>")
def delete_report(title):

    if session.get("role") != "admin":
        return "Access denied"

    reports_collection.delete_one({"title":title})

    logging.info(f"Incident deleted: {title}")

    return redirect("/?view=incidents")


# EXPORT CSV REPORT
@app.route("/export")
def export_csv():

    reports = list(reports_collection.find())

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Title","Description","Threat Level","Status","Evidence"])

    for r in reports:

        writer.writerow([
            r.get("title"),
            r.get("description"),
            r.get("threat_level"),
            r.get("status"),
            r.get("evidence")
        ])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        download_name="incident_report.csv",
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)