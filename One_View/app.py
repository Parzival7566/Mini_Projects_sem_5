from flask import Flask, render_template, request, jsonify, redirect
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
from flask import *
from bson.objectid import ObjectId
import os
import time
import webbrowser
import qrcode

app = Flask(__name__, static_url_path='/static')
app.config["SECRET_KEY"] = "SECRET_KEY"
app.config["UPLOAD_FOLDER"] = "static/uploads/"
app.config["MONGO_DBNAME"] = "one_view"
app.config["MONGO_URI"] = "mongodb://localhost:27017/one_view"

mongo = PyMongo(app)
ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg"]

event_data={}

with open('event_data.txt', 'w') as txtfile:
    txtfile.write('')


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
    generate_qr_code("http://127.0.0.1:5000/ongoing_event")
    return render_template('ongoing_event.html', event_data=event_data1)

@app.route("/gallery/")
def gallery():
    images = mongo.db.one_view.find()
    return render_template("gallery.html", gallery=images)

@app.route('/camera_main')
def camera_main():
    return render_template('camera_main.html')


@app.route('/upload_webcam',methods=["GET", "POST"])
def upload_webcam_capture():
    if 'webcam_image' in request.files:
        webcam_image = request.files['webcam_image']
        if webcam_image.filename != '':
            # Generate a unique filename using a timestamp
            timestamp = int(time.time())
            image_filename = f'webcam_capture_{timestamp}.jpeg'

        if image_filename.split(".")[-1].lower() in ALLOWED_EXTENSIONS:
            filename = secure_filename(image_filename)
            webcam_image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            mongo.db.one_view.insert_one({
                "filename": filename,
            })

            flash("Successfully uploaded image to gallery!", "success")
            return redirect(url_for("upload_webcam_capture"))
        else:
            flash("An error occurred while uploading the image!", "danger")
            return redirect(url_for("upload_webcam_capture"))
    return render_template("camera_main.html")


@app.route('/delete_image/<image_id>', methods=['DELETE'])
def delete_image(image_id):
    # Fetch the image document from the MongoDB database
    image = mongo.db.one_view.find_one({'_id': ObjectId(image_id)})

    if image:
        # Delete the image from the uploads directory
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], image["filename"]))

        # Delete the image document from the MongoDB database
        mongo.db.one_view.delete_one({'_id': ObjectId(image_id)})

        return jsonify({'message': 'Image deleted successfully'})
    else:
        return jsonify({'message': 'Image not found'}), 404


if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5000/admin')
    app.run(debug=True)