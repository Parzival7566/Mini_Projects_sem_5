from io import StringIO
import csv
import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["free_raj"]
collection_name = "orders"
orders_collection = db[collection_name]

def export_data_to_table():
    # Retrieve data from the MongoDB collection
    orders = list(orders_collection.find())

    # Create a dictionary to store the count of each item for each user
    item_count = {}

    # Iterate through the orders and update the count
    for order in orders:
        user_id = order["student_prn"]
        item_name = order["item"]

        # If the user_id and item_name combination is not in item_count, add it with a count of 1
        if (user_id, item_name) not in item_count:
            item_count[(user_id, item_name)] = 1
        else:
            # If it is already in item_count, increment the count
            item_count[(user_id, item_name)] += 1

    # Write the data to the CSV-like buffer
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerow(["Item Name", "User ID", "Number of Times Ordered"])

    for (user_id, item_name), count in item_count.items():
        csv_writer.writerow([item_name, user_id, count])

    # Create a DataFrame from the CSV-like buffer
    csv_data.seek(0)
    rating_table = pd.read_csv(csv_data)

    # Return the DataFrame as a response
    return rating_table
