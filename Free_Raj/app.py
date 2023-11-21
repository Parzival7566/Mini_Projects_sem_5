from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import webbrowser
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from datetime import datetime
import os
import recommendation

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


    # Calculate order status distribution
   
    order_statuses = orders_collection.aggregate([
    {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ])


    # Prepare data for visualization
    labels = []
    counts = []


    # Iterate through the results and populate labels and counts
    for status in order_statuses:
        labels.append(status["_id"])
        counts.append(status["count"])


    # Replace the existing code for creating the pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Distribution of Orders by Status')


    # Save the plot to a file instead of BytesIO
    chart_path = os.path.join(app.static_folder, "order_status_chart.png")
    plt.savefig(chart_path, format='png')
    plt.close()


    # Convert the chart image to base64
    with open(chart_path, "rb") as image_file:
        img_base64 = base64.b64encode(image_file.read()).decode('utf-8')




    # Calculate average order value
    average_order_value = round(total_price / total_orders ,2) if total_orders > 0 else 0


    order_times = [order["order_time"] for order in current_orders + completed_orders + collected_orders]


    # Convert order times to datetime objects
    order_times = [order_time.strftime("%H") for order_time in order_times]


    # Set popular_order_time to None by default
    popular_order_time = None


    # Analyze popular order times
#added a histogram
    if order_times:
        # Create a histogram for popular order times
        plt.figure(figsize=(10, 6))
        plt.hist(order_times, bins=24, edgecolor='black', alpha=0.7)
        plt.title('Distribution of Orders by Time')
        plt.xlabel('Time (HH:MM)')
        plt.ylabel('Number of Orders')
        plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
        plt.tight_layout()


        # Save the plot to a file
        chart_path_times = "order_time_histogram.png"
        plt.savefig(os.path.join(app.static_folder, chart_path_times), format='png')
        plt.close()


        # Convert the histogram plot to base64
        with open(os.path.join(app.static_folder, chart_path_times), 'rb') as image_file:
            img_base64_times = base64.b64encode(image_file.read()).decode('utf-8')
    else:
        img_base64_times = None


    #per item chart
    # Calculate the contribution of each item to the day's total orders
    item_contributions = {}
    for order in current_orders + completed_orders + collected_orders:
        for item, quantity in zip(order["item"], order["quantity"]):
            if item not in item_contributions:
                item_contributions[item] = 0
            item_contributions[item] += int(quantity)


    # Prepare data for the pie chart
    labels = list(item_contributions.keys())
    values = list(item_contributions.values())


    # Create a pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title("Contribution of Each Item to Total Orders")


    # Save the pie chart to a file
    chart_path_items = "item_contribution_chart.png"
    plt.savefig(os.path.join(app.static_folder, chart_path_items), format='png')
    plt.close()


    # Convert the pie chart image to base64
    with open(os.path.join(app.static_folder, chart_path_items), "rb") as image_file:
        img_base64_items = base64.b64encode(image_file.read()).decode('utf-8')


    return render_template("vendor_dashboard.html",
                           menu_items=menu_items, collected_orders=collected_orders, current_orders=current_orders,
                           completed_orders=completed_orders, total_orders=total_orders, total_price=total_price,
                           average_order_value=average_order_value, popular_order_time=popular_order_time,
                           order_status_chart=img_base64, order_times_chart=img_base64_times,
                           item_contribution_chart=img_base64_items)





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

@app.route("/recommendations")
def show_recommendations():
    username = request.args.get("username")
    recent_item = request.args.get("recent_item")

    # Your existing logic to fetch recommendations from the database
    recommendations = recommendation.recommend(recent_item)
    return render_template("recommendations.html", username=username, recent_item=recent_item, recommendations=recommendations)

menu_items = [menu_item["name"] for menu_item in menu_collection.find()]


@app.route("/recommendations/<prn>")
def get_recommendation(prn):
    student = students_collection.find_one({"prn": prn})
    # Fetch the most recent order for the student based on order_time
    most_recent_order = orders_collection.find_one(
        {"student_prn": prn},
        sort=[("order_time", -1)]
    )
    # Extract the most recent item from the order
    recent_item = most_recent_order.get("item") if most_recent_order else None
    # Call the recommend function with the most recent item name
    recommendations = recommendation.recommend(recent_item)
    # Filter recommendations to include only items present in the menu
    filtered_recommendations = [item for item in recommendations if item in menu_items]
    # Render the recommendations.html template with the relevant data
    return render_template("recommendations.html", student=student, recent_item=recent_item, recommendations=filtered_recommendations)

    
    

@app.route("/past_orders/<prn>")
def past_orders(prn):
    # Group orders by order number
    past_orders = orders_collection.aggregate([
        {"$match": {"student_prn": prn}},
        {"$group": {"_id": "$order_number", "orders": {"$push": "$$ROOT"}}}
    ])
    return render_template("past_orders.html", past_orders=past_orders)

        
@app.route("/place_order", methods=["POST"])#modified place orders for time analytics
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
    # Delete existing plots file
    if os.path.exists('static/order_status_chart.png'):
        os.remove('static/order_status_chart.png')

    if os.path.exists('static/order_time_histogram.png'):
        os.remove('static/order_time_histogram.png')
    
    if os.path.exists('static/item_contribution_chart.png'):
        os.remove('static/item_contribution_chart.png')

    pycache_dir = '__pycache__'
    if os.path.exists(pycache_dir):
        # Delete all files and subdirectories within pycache_dir
        for root, dirs, files in os.walk(pycache_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        # Delete the pycache_dir itself
        os.rmdir(pycache_dir)

    webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=True)