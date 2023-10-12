from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
import os
import time
import webbrowser
import qrcode
import csv


app = Flask(__name__, static_url_path='/static')
client = MongoClient("mongodb://localhost:27017/")
db = client['image_db']
collection = db['images']
app.secret_key = 'your_secret_key'
event_data={}

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    return img

@app.route('/')
def index():
    return admin_page()

@app.route('/admin')
def admin_page():
    return render_template('admin_page.html')

@app.route('/past_event')
def past_event():
    return render_template('past_event.html')

@app.route('/new_event', methods=['GET', 'POST'])
def new_event():
    if request.method == 'POST':
        # Get form data
        event_name = request.form.get('eventName')
        photos = request.form.get('photos')
        duration = request.form.get('duration')

        # Store data in a CSV file
        with open('event_data.csv', 'w', newline='') as csvfile:
            fieldnames = ['event_name', 'photos', 'duration']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerow({'event_name': event_name, 'photos': photos, 'duration': duration})

        return redirect('/ongoing_event')
    else:
        return render_template('new_event.html')

@app.route('/ongoing_event')
def ongoing_event():
    event_data1={}
    with open('event_data.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            event_data1 = row
    
    return render_template('ongoing_event.html', event_data=event_data1)

@app.route('/camera_main')
def camera_main():
    return render_template('camera_main.html')


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
    webbrowser.open('http://127.0.0.1:5000/admin')
    app.run()