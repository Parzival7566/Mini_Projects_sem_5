from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from clustering import load_and_encode_faces, cluster_faces
from flask_pymongo import PyMongo
from flask import *
from flask import session
from bson.objectid import ObjectId
import os
import time
import webbrowser

UPLOAD_FOLDER = "static/uploads/"

# Check if the directory exists, create it if necessary
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
            return redirect('/')
        else:
            hashed_password = generate_password_hash(password)
            host_details.insert_one({'username': username, 'password': hashed_password})
            flash('Account created successfully', 'success')
            return redirect('/')
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
            session['user_type'] = 'host'
            return redirect(f'/{username}/admin')
        else:
            flash('Invalid username or password', 'danger')
            return redirect('/')
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
            return redirect('/')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/')


@app.route('/attendee_login', methods=['GET', 'POST'])
def attendee_login():
    if request.method == 'POST':
        username = request.form.get('username')
        session['username'] = username
        session['user_type'] = 'attendee'
        # Fetch the ongoing event for the host
        ongoing_event = event_data.find_one({'hostName': username, 'status': 'ongoing'})
        if ongoing_event:
            session['event_name'] = ongoing_event['eventName']
        return redirect(f'/{username}/ongoing_event')
    
    else:
        return render_template('attendee_login.html')

@app.route('/logout')
def logout():
    session['username'] = None
    return redirect('/')


@app.route('/<username>/new_event', methods=['GET', 'POST'])
def new_event(username):
    user_type = session.get('user_type')
    if user_type != 'host':
        flash('Unauthorized access', 'danger')
        return redirect('/')

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

                session['event_name'] = event_name

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
            return redirect('/')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/')

@app.route('/<username>/past_event')
def past_event(username):
    user_type = session.get('user_type')
    session_username = session.get('username')
    if session_username and session_username == username:
        closed_events = list(event_data.find({'hostName': session_username, 'status': 'closed'}))
        return render_template('past_event.html', username=session_username, user_type=user_type, closed_events=closed_events)
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/')

@app.route('/<username>/ongoing_event')
def ongoing_event(username):
    user_type = session.get('user_type')
    if user_type != 'host' and user_type != 'attendee':
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    session_username = session.get('username')
    event_status = event_data.find_one({'status': 'ongoing'})
    if session_username and session_username == username:
        user = host_details.find_one({'username': session_username})
        if user:
            # Fetch the ongoing events for the logged-in user only
            ongoing_events = list(event_data.find({'hostName': session_username}))
            if ongoing_events == [] or event_status is None:
                return render_template('ongoing_event.html', user_type=user_type, username=session_username)
            else:
                return render_template('ongoing_event.html', username=session_username, user_type=user_type, event_data=ongoing_events)
        else:
            flash('Unauthorized access', 'danger')
            return redirect('/')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/')


@app.route('/<username>/gallery/')
def gallery(username):
    user_type = session.get('user_type')
    if user_type != 'host' and user_type != 'attendee':
        flash('Unauthorized access', 'danger')
        return redirect('/')

    session_username = session.get('username')
    event_name = session.get('event_name')
    if session_username and session_username == username:
        user = host_details.find_one({'username': session_username})
        event = event_data.find_one({'eventName':event_name })
        if user and event:
            images = event_gallery.find({'username': session_username, 'eventName': event_name})
            return render_template("gallery.html", gallery=images, user_type=user_type,username=session_username)
        else:
            flash('Unauthorized access', 'danger')
            return redirect('/')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/')


@app.route('/camera_main')
def camera_main():
    username = session.get('username')
    return render_template('camera_main.html', username=username)


@app.route('/upload_webcam', methods=["GET", "POST"])
def upload_webcam_capture():
    user_type = session.get('user_type')
    if user_type != 'host' and user_type != 'attendee':
        flash('Unauthorized access', 'danger')
        return redirect('/')
    # Rest of the code...
    username = session.get('username')
    event_name = session.get('event_name')
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
                    "username": username,
                    "eventName": event_name
                })

                flash("Successfully uploaded image to gallery!", "success")
                return redirect(url_for("gallery", username=username))
            else:
                flash("An error occurred while uploading the image!", "danger")
                return redirect(url_for("upload_webcam_capture"))
    return render_template("camera_main.html")



@app.route('/delete_image/<image_id>', methods=['GET', 'DELETE'])
def delete_image(image_id):
    user_type = session.get('user_type')
    if user_type != 'host':
        return jsonify({'message': 'Only the host can delete images'})
    
    if request.method == 'GET':
        # Fetch the image document from the MongoDB database
        image = event_gallery.find_one({'_id': ObjectId(image_id)})
        if image:
            # Check if the user is the host
            session_username = session.get('username')
            if session_username and session_username == image['username']:
                return jsonify({'message': 'Confirm deletion'})
            else:
                return jsonify({'message': 'Only the host can delete images'})
        else:
            return jsonify({'message': 'Image not found'}), 404

    elif request.method == 'DELETE':
        # Fetch the image document from the MongoDB database
        image = event_gallery.find_one({'_id': ObjectId(image_id)})
        if image:
            # Check if the user is the host
            session_username = session.get('username')
            if session_username and session_username == image['username']:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], image["filename"]))
                # Delete the image document from the MongoDB database
                event_gallery.delete_one({'_id': ObjectId(image_id)})

                # Check if the event is closed
                event_status = event_data.find_one({'status': 'closed'})
                if event_status:
                    # Perform face encoding and clustering
                    input_dir = 'static/uploads'  # Directory containing the images
                    encodings_file = 'encodings.pickle'  # File to store the face encodings
                    output_dir = 'static/clusters'  # Directory to store the clusters

                    load_and_encode_faces(input_dir, encodings_file)
                    cluster_faces(encodings_file, output_dir)

                return jsonify({'success': True, 'message': 'Image deleted successfully'})

            else:
                return jsonify({'message': 'User not found'}), 404
        else:
            return jsonify({'message': 'Only the host can delete images'})
    else:
        return jsonify({'message': 'Image not found'}), 404

    

@app.route('/<username>/close_event/<event_id>', methods=['POST'])
def close_event(username, event_id):
    user_type = session.get('user_type')
    if user_type != 'host':
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    session_username = session.get('username')
    if session_username and session_username == username:
        user = host_details.find_one({'username': session_username})
        if user:
            event_data.update_one({'_id': ObjectId(event_id)}, {'$set': {"status": 'closed'}})
            flash('Event closed successfully', 'success')

            # Perform face encoding and clustering
            input_dir = 'static/uploads'  # Directory containing the images
            encodings_file = 'encodings.pickle'  # File to store the face encodings
            output_dir = 'static/clusters'  # Directory to store the clusters

            load_and_encode_faces(input_dir, encodings_file)
            cluster_faces(encodings_file, output_dir)

            return redirect(f'/{username}/past_event')
        else:
            flash('Unauthorized access', 'danger')
            return redirect('/')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    
@app.route('/<username>/cluster/<cluster_dir>')
def cluster(username, cluster_dir):
    session_username = session.get('username')
    if session_username and session_username == username:
        user = host_details.find_one({'username': session_username})
        if user:
            # Fetch the images in the cluster directory
            cluster_images = [img for img in os.listdir(os.path.join('static', 'clusters', cluster_dir)) if img.startswith('image_')]
            return render_template('cluster.html', username=session_username, cluster_images=cluster_images, cluster_dir=cluster_dir)
        else:
            flash('Unauthorized access', 'danger')
            return redirect('/')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    
@app.route('/<username>/clusters')
def clusters(username):
    session_username = session.get('username')
    if session_username and session_username == username:
        user = host_details.find_one({'username': session_username})
        if user:
            # Fetch the cluster directories
            cluster_dirs = os.listdir('static/clusters')
            return render_template('clusters.html', username=session_username, cluster_dirs=cluster_dirs)
        else:
            flash('Unauthorized access', 'danger')
            return redirect('/')
    else:
        flash('Unauthorized access', 'danger')
        return redirect('/')
    

if __name__ == '__main__':
    # Delete encodings.pickle file
    if os.path.exists('encodings.pickle'):
        os.remove('encodings.pickle')
    
    # Delete static/clusters directory if it exists
    clusters_dir = 'static/clusters'
    if os.path.exists(clusters_dir):
        # Delete all files and subdirectories within clusters_dir
        for root, dirs, files in os.walk(clusters_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        # Delete the clusters_dir itself
        os.rmdir(clusters_dir)
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