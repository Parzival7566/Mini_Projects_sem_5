from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
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
vendor_collection=mongo.db["vendor"]

vendor_collection.drop()

vendor_data = [
    {"username": "freeraj", "password": "1234"}
]

vendor_collection.insert_many(vendor_data)

# Sample menu data
'''sample_menu = [
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
'''
@app.route("/vendor_login", methods=["GET", "POST"])
def vendor_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Check the provided username and password against data in the "vendors" collection
        vendor = vendor_collection.find_one({"username": username, "password": password})
        
        if vendor:
            # Redirect to the vendor dashboard upon successful login
            return redirect(url_for("vendor_dashboard"))
        else:
            error_message = "Invalid username or password. Please try again."
            return render_template("vendor_login.html", error=error_message)
    
    return render_template("vendor_login.html")

@app.route("/vendor_dashboard")
def vendor_dashboard():
    # Retrieve analytics data
    total_orders = orders_collection.count_documents({})
    # You can calculate 'most_ordered_item' here

    # Retrieve current and completed orders
    current_orders = orders_collection.find({"status": "open"})
    completed_orders = orders_collection.find({"status": "completed"})
    menu_items = list(menu_collection.find())
    # Calculate earnings
    # You can calculate 'total_earnings' here

    return render_template("vendor_dashboard.html", total_orders=total_orders,
                           menu_items=menu_items,
                          # most_ordered_item=most_ordered_item, current_orders=current_orders,
                           #completed_orders=completed_orders, total_earnings=total_earnings)
    )

@app.route("/edit_menu", methods=["GET", "POST"])
def edit_menu():
    if request.method == "POST":
        food_item_name = request.form["food_item_name"]
        price = request.form["price"]
        preparation_time = request.form["preparation_time"]

        # Create a dictionary with the menu item data
        menu_item = {
            "name": food_item_name,
            "price": price,
            "preparation_time": preparation_time
        }

        # Insert the new menu item into the menu collection in MongoDB
        menu_collection.insert_one(menu_item)

        # Redirect back to the vendor dashboard or another appropriate page
        return redirect(url_for("vendor_dashboard"))

    return render_template("edit_menu.html")

@app.route("/delete_menu_item/<menu_item_id>", methods=["POST"])
def delete_menu_item(menu_item_id):
    # Convert menu_item_id to ObjectId
    menu_item_id = ObjectId(menu_item_id)

    # Delete the menu item from the menu collection
    menu_collection.delete_one({"_id": menu_item_id})

    # Redirect back to the vendor dashboard or another appropriate page
    return redirect(url_for("vendor_dashboard"))

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
        uname=request.form["uname"]
        prn = request.form["prn"]
        password = request.form["password"]
        student = students_collection.find_one({"prn": prn})
        if student:
            error_message = "Account already exists for PRN. Please try again."
            return render_template("create_account.html", error=error_message)
        else:
            student_data = {
                "uname": uname, 
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

@app.route("/view_cart", methods=["GET", "POST"])
def view_cart():
    prn = request.args.get("prn")
    student = students_collection.find_one({"prn": prn})
    if student:
        if request.method == "POST":
            item_id = request.form.get("item_id")
            cart.delete_one({"_id": ObjectId(item_id)})
            return redirect(url_for("view_cart", prn=prn))
        else:
            cart_items = list(cart.find({"student_prn": prn}))
            return render_template("view_cart.html", student=student, cart_items=cart_items)
    else:
        error_message = "Student data not found."
        return render_template("student_login.html", error=error_message)
    
@app.route("/payment_gateway", methods=["GET", "POST"])
def payment_gateway():
    prn = request.args.get("prn")
    student = students_collection.find_one({"prn": prn})
    cart_items = list(cart.find({"student_prn": prn}))
    if student:
        if request.method == "POST":
            if not cart_items:
                flash("Cannot checkout an empty cart!")
                return redirect(url_for("dashboard", prn=prn))
            
            for item in cart_items:
                item["status"] = "open"
                orders_collection.insert_one(item)
            cart.delete_many({"student_prn": prn})
            return redirect(url_for("dashboard", prn=prn))
        else:
            items = []
            quantities = []
            preparation_times = []
            for cart_item in cart_items:
                for index in range(len(cart_item["items"])):
                    items.append(cart_item["items"][index])
                    quantities.append(cart_item["quantities"][index])
                    preparation_times.append(cart_item["preparation_times"][index])
            return render_template("payment_gateway.html", student=student, cart_items=cart_items, items=items, quantities=quantities, preparation_times=preparation_times)
    else:
        error_message = "Student data not found."
        return render_template("student_login.html", error=error_message)

if __name__ == "__main__":
    webbrowser.open('http://127.0.0.1:5000/')
    app.run()
