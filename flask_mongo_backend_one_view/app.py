from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
import time

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")  # MongoDB connection URL
db = client['image_db']  # Use or create a database called 'image_db'
collection = db['images']  # Use or create a collection called 'images'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename != '':
            # Save the uploaded image to a folder (optional)
            upload_folder = 'uploads'
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, image_file.filename)
            image_file.save(image_path)

            # Insert the image file path into MongoDB
            image_data = {'path': image_path}
            collection.insert_one(image_data)

            return jsonify(message='Image uploaded successfully.')

    return jsonify(message='No image uploaded.')

@app.route('/upload_webcam', methods=['POST'])
def upload_webcam_capture():
    if 'webcam_image' in request.files:
        webcam_image = request.files['webcam_image']
        if webcam_image.filename != '':
            # Generate a unique filename using a timestamp
            timestamp = int(time.time())
            image_filename = f'webcam_capture_{timestamp}.png'

            # Save the webcam capture to the 'uploads' folder with the unique filename
            upload_folder = 'uploads'
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, image_filename)
            webcam_image.save(image_path)

            # Insert the webcam capture into MongoDB as a binary file
            with open(image_path, 'rb') as image_file:
                image_data = {'webcam_capture': image_file.read()}
                collection.insert_one(image_data)

            return jsonify(message='Webcam capture saved successfully.')

    return jsonify(message='No webcam capture available.')


if __name__ == '__main__':
    app.run()