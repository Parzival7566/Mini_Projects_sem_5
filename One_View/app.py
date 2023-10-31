from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from flask import *
from flask import session
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
event_gallery = mongo.db["gallery"]

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
            session['username'] = username
            return redirect(f'/{username}/admin')
        else:
            flash('Invalid username or password', 'danger')
            return redirect('/host_login')
    else:
        return render_template('host_login.html')


@app.route('/<username>/admin')
def admin_page(username):
    # Access the username from the session
    session_username = session.get('username')
    if session_username and session_username == username:
        user = host_details.find_one({'username': session_username})
        if user:
            return render_template('admin_page.html', username=session_username)
        else:
            flash('Unauthorized access', 'danger')
            return redirect('/host_login')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/host_login')


@app.route('/attendee_page')
def attendee_page():
    # Add your code here
    pass

@app.route('/logout')
def logout():
    session['username'] = None
    return redirect('/')


@app.route('/<username>/past_event')
def past_event(username):
    # Access the username from the session
    session_username = session.get('username')
    if session_username and session_username == username:
        return render_template('past_event.html', username=session_username)
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/host_login')


@app.route('/<username>/new_event', methods=['GET', 'POST'])
def new_event(username):
    # Access the username from the session
    session_username = session.get('username')
    if session_username and session_username == username:
        user = host_details.find_one({'username': session_username})
        if user:
            if request.method == 'POST':
                # Get form data
                host_name = user['username']
                event_name = request.form.get('eventName')
                photos = request.form.get('photos')
                duration = request.form.get('duration')
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                # Store data in the MongoDB database
                event_data.insert_one({
                    'hostName': host_name,
                    'eventName': event_name,
                    'photos': photos,
                    'duration': duration,
                    'createdOn': current_time,
                    'status': "ongoing"
                })

                return redirect(f'/{username}/ongoing_event')
            else:
                return render_template('new_event.html', username=session_username)
        else:
            flash('Unauthorized access', 'danger')
            return redirect('/host_login')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/host_login')


@app.route('/<username>/ongoing_event')
def ongoing_event(username):
    # Access the username from the session
    session_username = session.get('username')
    if session_username and session_username == username:
        user = host_details.find_one({'username': session_username})
        if user:
            # Fetch the ongoing events for the logged-in user only
            ongoing_events = list(event_data.find({'hostName': session_username}))
            if ongoing_events == []:
                return render_template('ongoing_event.html', username=session_username)
            else:
                return render_template('ongoing_event.html', event_data=ongoing_events, username=session_username)
        else:
            flash('Unauthorized access', 'danger')
            return redirect('/host_login')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/host_login')


@app.route("/<username>/gallery/")
def gallery(username):
    # Access the username from the session
    session_username = session.get('username')
    if session_username and session_username == username:
        user = host_details.find_one({'username': session_username})
        if user:
            images = event_gallery.find({'username': session_username})
            return render_template("gallery.html", gallery=images, username=session_username)
        else:
            flash('Unauthorized access', 'danger')
            return redirect('/host_login')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/host_login')


@app.route('/camera_main')
def camera_main():
    username = session.get('username')
    return render_template('camera_main.html', username=username)


@app.route('/upload_webcam', methods=["GET", "POST"])
def upload_webcam_capture():
    username = session.get('username')
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
                    "username": username
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