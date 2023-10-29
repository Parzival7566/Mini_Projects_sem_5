from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
import webbrowser

app = Flask(__name__)
app.config["SECRET_KEY"] = "SECRET_KEY"
app.config["UPLOAD_FOLDER"] = "static/uploads/"
app.config["MONGO_DBNAME"] = "free_raj"
app.config["MONGO_URI"] = "mongodb://localhost:27017/free_raj"

mongo = PyMongo(app)
students_collection = mongo.db["students"]
menu_collection = mongo.db["menu"]
orders_collection = mongo.db["orders"]

# Sample menu data
sample_menu = [
    {"name": "Item 1", "preparation_time": "10 minutes"},
    {"name": "Item 2", "preparation_time": "15 minutes"},
    {"name": "Item 3", "preparation_time": "12 minutes"},
    {"name": "Item 4", "preparation_time": "8 minutes"},
    {"name": "Item 5", "preparation_time": "20 minutes"},
    {"name": "Item 6", "preparation_time": "7 minutes"},
    {"name": "Item 7", "preparation_time": "25 minutes"},
    {"name": "Item 8", "preparation_time": "11 minutes"},
    {"name": "Item 9", "preparation_time": "14 minutes"},
    {"name": "Item 10", "preparation_time": "18 minutes"},
]

# Automatically populate the menu data when the app starts
if menu_collection.count_documents({}) == 0:
    # Remove existing menu items
    menu_collection.delete_many({})
    # Populate the menu data
    menu_collection.insert_many(sample_menu)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        prn = request.form["prn"]
        student = students_collection.find_one({"prn": prn})
        if student:
            return redirect(url_for("dashboard", prn=prn))
        else:
            error_message = "Invalid PRN or Password. Please try again."
            return render_template("student_login.html", error=error_message)
    return render_template("student_login.html")

@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        prn = request.form["prn"]
        password = request.form["password"]
        student = students_collection.find_one({"prn": prn})
        if student:
            error_message = "Account already exists for PRN. Please try again."
            return render_template("create_account.html", error=error_message)
        else:
            student_data = {
                "prn": prn,
                "password": password
            }
            students_collection.insert_one(student_data)
            return redirect(url_for("login"))
    return render_template("create_account.html")

@app.route("/dashboard/<prn>", methods=["GET", "POST"])
def dashboard(prn):
    student = students_collection.find_one({"prn": prn})
    if student:
        menu = list(menu_collection.find())  # Fetch menu items from MongoDB
        return render_template("studentdashboard.html", student=student, menu=menu)
    else:
        error_message = "Student data not found."
        return render_template("student_login.html", error=error_message)

@app.route("/place_order", methods=["POST"])
def place_order():
    prn = request.form["prn"]
    student = students_collection.find_one({"prn": prn})
    if student:
        items = request.form.getlist("item")
        quantities = request.form.getlist("quantity")
        preparation_times = request.form.getlist("preparation_time")

        order_data = {
            "student_prn": prn,
            "items": items,
            "quantities": quantities,
            "preparation_times": preparation_times
        }
        orders_collection.insert_one(order_data)

    return redirect(url_for("dashboard", prn=prn))

if __name__ == "__main__":
    webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=True)