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
cart=mongo.db["cart"]
vendor_colection=mongo.db["vendor"]

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
        items = []
        quantities = []
        preparation_times = []

        for item, quantity, preparation_time in zip(request.form.getlist("item"), request.form.getlist("quantity"), request.form.getlist("preparation_time")):
            if int(quantity) > 0:
                items.append(item)
                quantities.append(quantity)
                preparation_times.append(preparation_time)

        cart_data = {
            "student_prn": prn,
            "items": items,
            "quantities": quantities,
            "preparation_times": preparation_times
        }
        cart.insert_one(cart_data)

    return redirect(url_for("dashboard", prn=prn))

@app.route("/view_cart", methods=["GET"])
def view_cart():
    prn = request.args.get("prn")
    student = students_collection.find_one({"prn": prn})
    if student:
        # Fetch cart items from MongoDB based on student's PRN
        cart_items = list(cart.find({"student_prn": prn}))  # Convert cursor to list
        items = [item["items"] for item in cart_items]
        quantities = [item["quantities"] for item in cart_items]
        preparation_times = [item["preparation_times"] for item in cart_items]
        return render_template("view_cart.html", student=student, items=items, quantities=quantities, preparation_times=preparation_times)
    else:
        error_message = "Student data not found."
        return render_template("student_login.html", error=error_message)
    
@app.route("/payment_gateway", methods=["GET", "POST"])
def payment_gateway():
    prn = request.args.get("prn")
    student = students_collection.find_one({"prn": prn})
    if student:
        if request.method == "POST":
            # Fetch cart items from MongoDB based on student's PRN
            cart_items = list(cart.find({"student_prn": prn}))  # Convert cursor to list
            for item in cart_items:
                item["status"] = "open"
                orders_collection.insert_one(item)
            cart.delete_many({"student_prn": prn})
            return redirect(url_for("dashboard", prn=prn))
        else:
            # Fetch cart items from MongoDB based on student's PRN
            cart_items = list(cart.find({"student_prn": prn}))  # Convert cursor to list
            items = [item["items"] for item in cart_items]
            quantities = [item["quantities"] for item in cart_items]
            preparation_times = [item["preparation_times"] for item in cart_items]
            return render_template("payment_gateway.html", student=student, items=items, quantities=quantities, preparation_times=preparation_times)
    else:
        error_message = "Student data not found."
        return render_template("student_login.html", error=error_message)

if __name__ == "__main__":
    webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=True)