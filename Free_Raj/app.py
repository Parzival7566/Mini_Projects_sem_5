from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import webbrowser
import hashlib

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
past_orders_collection=mongo.db["past_orders"]
vendor_collection=mongo.db["vendor"]

vendor_collection.drop()

vendor_data = [
    {"username": "freeraj", "password": "1234"}
]

vendor_collection.insert_many(vendor_data)


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
    # Retrieve current orders
    current_orders = list(orders_collection.find({"status": "open"}))
    
    # Retrieve completed orders with a status of "closed"
    completed_orders = list(orders_collection.find({"status": "completed"}))

    # Retrieve completed orders with a status of "closed"
    collected_orders = list(orders_collection.find({"status": "collected"}))

    # Retrieve analytics data
    total_orders = orders_collection.count_documents({})
    # You can calculate 'most_ordered_item' here
    menu_items = list(menu_collection.find())
    # Calculate earnings
    # You can calculate 'total_earnings' here
    
    # Calculate total price of all orders
    total_price = sum(int(order["price"])*int(order["quantity"]) for order in current_orders + completed_orders + collected_orders)

    return render_template("vendor_dashboard.html",
                           menu_items=menu_items, collected_orders=collected_orders, current_orders=current_orders, completed_orders=completed_orders, total_orders=total_orders,
                           total_price=total_price)



@app.route("/mark_order_done", methods=["POST"])
def mark_order_done():
    if request.method == "POST":
        order_id = request.form.get("order_id")

        # Find the order in the 'orders_collection' by its ObjectId
        order = orders_collection.find_one({"_id": ObjectId(order_id)})

        if order:
            # Update the status to "completed"
            orders_collection.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "completed"}})

            # Redirect back to the vendor dashboard
            return redirect(url_for("vendor_dashboard"))

    # Handle errors or invalid requests
    return "Invalid request or order not found"


@app.route("/mark_order_collected", methods=["POST"])
def mark_order_collected():
    if request.method == "POST":
        order_id = request.form.get("order_id")

        # Find the order in the 'orders_collection' by its ObjectId
        order = orders_collection.find_one({"_id": ObjectId(order_id)})

        if order:
            # Check if the order is already collected
            if order.get("status") == "collected":
                return "Order is already collected"
            
            # Update the status to "collected"
            orders_collection.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "collected"}})

            order_data = {
            "order_id": str(order["_id"]),
            "items": order["item"],
            "quantities": order["quantity"],
            "prices": order["price"],
            "status": order["status"],
            "order_cost": sum(int(price) * int(quantity) for price, quantity in zip(order["price"], order["quantity"]))
            }
            # Add the order to the 'past_orders_collection' collection
            past_orders_collection.insert_one(order_data)

            # Redirect back to the vendor dashboard
            return redirect(url_for("vendor_dashboard"))
        else:
            error_message = "Order not found."
            return render_template("vendor_dashboard.html", error=error_message)
        

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
        uname = request.form["uname"]
        prn = request.form["prn"]
        password = request.form["password"]
        student = students_collection.find_one({"prn": prn})
        if student:
            error_message = "Account already exists for PRN. Please try again."
            return render_template("create_account.html", error=error_message)
        else:
            # Hash the password using SHA-256
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            student_data = {
                "uname": uname, 
                "prn": prn,
                "password": hashed_password,
                "order_number": 1
            }
            students_collection.insert_one(student_data)
            return redirect(url_for("login"))
    return render_template("create_account.html")


@app.route("/dashboard/<prn>", methods=["GET", "POST"])
def dashboard(prn):
    student = students_collection.find_one({"prn": prn})
    if student:
        menu = list(menu_collection.find())  # Fetch menu items from MongoDB
        closed_orders = list(orders_collection.find({"student_prn": prn, "status": "completed"}))  # Fetch closed orders for the student
        if closed_orders == []:
            return render_template("studentdashboard.html", student=student, menu=menu)
        else:
            return render_template("studentdashboard.html", student=student, menu=menu, closed_orders=closed_orders)
    else:
        error_message = "Student data not found."
        return render_template("student_login.html", error=error_message)
    

@app.route("/past_orders/<prn>")
def past_orders(prn):
    # Group orders by order number
    past_orders = orders_collection.aggregate([
        {"$match": {"student_prn": prn}},
        {"$group": {"_id": "$order_number", "orders": {"$push": "$$ROOT"}}}
    ])
    return render_template("past_orders.html", past_orders=past_orders)
        
@app.route("/place_order", methods=["POST"])
def place_order():
    if request.method == "POST":
        student_prn = request.form.get("prn")
        items = request.form.getlist("item")

        for item in items:
            quantity = request.form.get(f"quantity_{item}")
            preparation_time = request.form.get(f"preparation_time_{item}")
            price = request.form.get(f"price_{item}")

            if quantity != '0':
                cart_item = {
                    "student_prn": student_prn,
                    "item": item,
                    "quantity": quantity,
                    "preparation_time": preparation_time,
                    "price": price,
                    "order_time": datetime.now()  # Add the current date and time
                }
                cart.insert_one(cart_item)

        flash("Item(s) added to cart successfully!")
        if student_prn:
            return redirect(url_for("dashboard", prn=student_prn))



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
            if cart_items ==[]:
                return render_template("view_cart.html", student=student)
            else:
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
                item["order_time"] = datetime.now()
                item["order_number"] = student["order_number"]
                orders_collection.insert_one(item)
            cart.delete_many({"student_prn": prn})
            students_collection.update_one({"prn": prn}, {"$inc": {"order_number": 1}})
            return redirect(url_for("dashboard", prn=prn))
        else:
            items = []
            quantities = []
            preparation_times = []
            prices = []
            for cart_item in cart_items:
                items.append(cart_item["item"])
                quantities.append(cart_item["quantity"])
                preparation_times.append(cart_item["preparation_time"])
                prices.append(cart_item["price"])
            return render_template("payment_gateway.html", student=student, cart_items=cart_items, items=items, quantities=quantities, preparation_times=preparation_times)
    else:
        error_message = "Student data not found."
        return render_template("student_login.html", error=error_message)
    

if __name__ == "__main__":
    webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=True)