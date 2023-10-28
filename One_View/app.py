from flask import Flask, render_template, request,send_file, jsonify, redirect
from pymongo import MongoClient
import os
import time
import webbrowser
import qrcode
import csv
from bson import ObjectId
from gridfs import GridFS


app = Flask(__name__, static_url_path='/static')
client = MongoClient("mongodb://localhost:27017/")
db = client['image_db']
collection = db['images']
app.secret_key = 'your_secret_key'
event_data={}
fs = GridFS(db)

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
        admin_name = request.form.get('adminName')
        event_name = request.form.get('eventName')
        photos = request.form.get('photos')
        duration = request.form.get('duration')

        # Store data in a text file along with date and time
        with open('event_data.txt', 'w') as txtfile:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            txtfile.write(f"{admin_name}\n{event_name}\n{photos}\n{duration}\n{current_time}")

        return redirect('/ongoing_event')
    else:
        return render_template('new_event.html')



@app.route('/ongoing_event')
def ongoing_event():
    event_data1 = {}
    try:
        with open('event_data.txt', 'r') as txtfile:
            data = txtfile.read()
            # Parse the data from the txt file
            lines = data.split('\n')
            if len(lines) == 5:
                event_data1['adminName'] = lines[0]
                event_data1['eventName'] = lines[1]
                event_data1['photos'] = lines[2]
                event_data1['duration'] = lines[3]
                event_data1['createdOn'] = lines[4]
    except FileNotFoundError:
        # If the file doesn't exist, create an empty one
        with open('event_data.txt', 'w') as txtfile:
            pass

    return render_template('ongoing_event.html', event_data=event_data1)

@app.route('/open_gallery')
def gallery():
     # Add your code to render the gallery page here
     return render_template('open_gallery.html')

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



@app.route('/gallery')
def gallery():
    image_data = []
    for file in fs.find():
        image_data.append({
            'image_id': str(file._id),
            'image_url': f"/image/{file._id}"
        })
    return render_template('gallery.html', image_data=image_data)


@app.route('/image/<image_id>')
def serve_image(image_id):
    try:
        image = fs.get(ObjectId(image_id))
        response = send_file(image, mimetype='image/jpeg')  # Adjust mimetype as per your image type
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as e:
        return str(e), 404

if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5000/admin')
    app.run()