from flask import Flask, render_template, request, jsonify, redirect
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import *
from bson.objectid import ObjectId
import os
import time
import webbrowser

app = Flask(__name__, static_url_path='/static')
app.config["SECRET_KEY"] = "SECRET_KEY"
app.config["UPLOAD_FOLDER"] = "static/uploads/"
app.config["MONGO_DBNAME"] = "one_view"
app.config["MONGO_URI"] = "mongodb://localhost:27017/one_view"

mongo = PyMongo(app)
ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg"]
host_details = mongo.db["host"]
event_data = mongo.db["events"]
event_gallery=mongo.db["gallery"]

event_data.drop()

@app.route('/')
def login_page():
    return render_template('login.html')


@app.route('/host_signup', methods=['GET', 'POST'])
def host_signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = host_details.find_one({'username': username})
        if user:
            flash('Username already exists', 'danger')
            return redirect('/host_signup')
        else:
            hashed_password = generate_password_hash(password)
            host_details.insert_one({'username': username, 'password': hashed_password})
            flash('Account created successfully', 'success')
            return redirect('/host_login')
    else:
        return render_template('host_signup.html')

@app.route('/host_login', methods=['GET', 'POST'])
def host_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = host_details.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            return redirect(f'/{username}/admin')
        else:
            flash('Invalid username or password', 'danger')
            return redirect('/host_login')
    else:
        return render_template('host_login.html')
    
@app.route('/<username>/admin')
def admin_page(username):
    user = host_details.find_one({'username': username})
    if user:
        return render_template('admin_page.html', username=username)
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/host_login')

@app.route('/attendee_page')
def attendee_page():
    # Add your code here
    pass

@app.route('/<username>/past_event')
def past_event(username):
    return render_template('past_event.html', username=username)

@app.route('/<username>/new_event', methods=['GET', 'POST'])
def new_event(username):
    user = host_details.find_one({'username': username})
    if user:
        if request.method == 'POST':
            # Get form data
            admin_name = request.form.get('adminName')
            event_name = request.form.get('eventName')
            photos = request.form.get('photos')
            duration = request.form.get('duration')
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")

            # Store data in the MongoDB database
            event_data.insert_one({
                'adminName': admin_name,
                'eventName': event_name,
                'photos': photos,
                'duration': duration,
                'createdOn': current_time,
                'status': "ongoing"
            })

            return redirect(f'/{username}/ongoing_event')
        else:
            return render_template('new_event.html', username=username)
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/host_login')

@app.route('/<username>/ongoing_event')
def ongoing_event(username):
    user = host_details.find_one({'username': username})
    if user:
        temp_event_data = event_data.find_one()
        return render_template('ongoing_event.html', event_data=temp_event_data, username=username)
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/host_login')

@app.route("/<username>/gallery/")
def gallery(username):
    user = host_details.find_one({'username': username})
    if user:
        images = event_gallery.find()
        return render_template("gallery.html", gallery=images, username=username)
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/host_login')

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

            event_gallery.insert_one({
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
    image = event_gallery.find_one({'_id': ObjectId(image_id)})

    if image:
        # Delete the image from the uploads directory
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], image["filename"]))

        # Delete the image document from the MongoDB database
        event_gallery.delete_one({'_id': ObjectId(image_id)})

        return jsonify({'message': 'Image deleted successfully'})
    else:
        return jsonify({'message': 'Image not found'}), 404


if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=True)