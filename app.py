from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from database import create_user, authenticate_user, get_user_by_email, get_user_detections, get_user_alerts, get_all_users, add_upload, get_user_uploads
from werkzeug.utils import secure_filename
from camera import start_detection_background, stop_detection_background
from PIL import Image
import io
import os
from datetime import datetime
import zipfile
import shutil

app = Flask(__name__, template_folder='templates')
# Minimal secret key for session (replace for production)
app.secret_key = 'dev-secret'

# Upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Dataset configuration
DATASET_FOLDER = os.path.join(os.path.dirname(__file__), 'dataset')
ALLOWED_DATASET_EXT = {'zip', 'png', 'jpg', 'jpeg', 'bmp', 'gif'}

def is_allowed_dataset_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_DATASET_EXT


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_to_jpg(image_file):
    """Convert uploaded image to JPG format and return the converted image file."""
    try:
        img = Image.open(image_file)
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as JPG to a BytesIO object
        jpg_buffer = io.BytesIO()
        img.save(jpg_buffer, format='JPEG', quality=85)
        jpg_buffer.seek(0)
        return jpg_buffer
    except Exception as e:
        raise Exception(f"Failed to convert image: {str(e)}")

# Home
@app.route('/')
def home():
    return render_template('home.html')

# User Pages
@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        location = request.form.get('location', '').strip() or None

        if not name or not email or not password:
            flash('Name, email and password are required')
            return render_template('user_register.html')

        if get_user_by_email(email):
            flash('A user with that email already exists')
            return render_template('user_register.html')

        user = create_user(name, email, password, location)
        if user:
            # set session and go to dashboard
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            return redirect(url_for('user_dashboard'))
        else:
            flash('Failed to create user (email may already be in use)')
            return render_template('user_register.html')

    return render_template('user_register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = authenticate_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password')
            return render_template('user_login.html')

    return render_template('user_login.html')


@app.route('/user/dashboard')
def user_dashboard():
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    return render_template('user_dashboard.html')


@app.route('/user/history')
def user_history():
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    user_id = session['user_id']
    detections = get_user_detections(user_id)
    return render_template('user_history.html', detections=detections)


@app.route('/user/alerts')
def user_alerts():
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    user_id = session['user_id']
    alerts = get_user_alerts(user_id)
    return render_template('user_alerts.html', alerts=alerts)


@app.route('/start_detection')
def start_detection():
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    # Start detection in background process
    try:
        user_email = session.get('user_email')
        # pass the logged-in user's email as both sender override and recipient
        start_detection_background(sender_email=user_email, recipient_email=user_email)
        flash('Detection started in background.')
    except Exception as e:
        flash(f'Error starting detection: {str(e)}')
    return render_template('user_camera.html')


@app.route('/user/upload', methods=['GET', 'POST'])
def user_upload():
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    
    if request.method == 'POST':
        # Check if file is in request
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Only image files are allowed (PNG, JPG, JPEG, GIF, BMP)')
            return redirect(request.url)
        
        try:
            user_id = session['user_id']
            # Create unique filename with timestamp and JPG extension
            original_name = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            jpg_filename = timestamp + os.path.splitext(original_name)[0] + '.jpg'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], jpg_filename)
            
            # Convert image to JPG
            jpg_buffer = convert_to_jpg(file)
            
            # Save JPG file
            with open(filepath, 'wb') as f:
                f.write(jpg_buffer.getvalue())
            
            # Record in database with original filename
            add_upload(user_id, jpg_filename, original_name)
            
            flash('Image uploaded and converted to JPG successfully!')
            return redirect(url_for('user_upload_success', filename=jpg_filename))
        except Exception as e:
            flash(f'Error uploading file: {str(e)}')
            return redirect(request.url)
    
    return render_template('user_upload.html')


@app.route('/user/upload/success')
def user_upload_success():
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    user_id = session['user_id']
    uploads = get_user_uploads(user_id)
    return render_template('user_upload_success.html', uploads=uploads)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Verify user owns this file (basic security)
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    return None


@app.route('/start_detection/stream')
def start_detection_stream():
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    return ('', 204)  # Not used in static flow


@app.route('/start_detection/snapshot')
def user_snapshot():
    """Return a single JPEG frame for polling fallback."""
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    return ('', 204)  # Not used in static flow


@app.route('/start_detection/stop')
def stop_detection():
    if not session.get('user_id'):
        return redirect(url_for('user_login'))
    try:
        stop_detection_background()
        flash('Detection stopped.')
    except Exception as e:
        flash(f'Error stopping detection: {str(e)}')
    return redirect(url_for('user_dashboard'))

# Admin Pages
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == 'admin' and password == 'admin':
            session['admin_authenticated'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password')
            return render_template('admin_login.html')

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')


@app.route('/admin/users')
def admin_users():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))
    users = get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/admin/dataset')
def admin_dataset():
    return render_template('admin_dataset.html')


@app.route('/admin/train')
def admin_train():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))
    return render_template('admin_train.html')


@app.route('/admin/start_training', methods=['POST'])
def admin_start_training():
    if not session.get('admin_authenticated'):
        return {'started': False}, 403
    # This is a dummy endpoint: in real life you'd kick off a training job here.
    return {'started': True}


@app.route('/admin/logs')
def admin_logs():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))
    return render_template('admin_logs.html')


@app.route('/admin/logs/data')
def admin_logs_data():
    # Return some dummy logs as JSON
    dummy_logs = [
        {'time': '2025-11-28 09:00:00', 'msg': 'Training job queued.'},
        {'time': '2025-11-28 09:00:05', 'msg': 'Initializing model...'},
        {'time': '2025-11-28 09:00:20', 'msg': 'Loaded dataset with 1248 images.'},
        {'time': '2025-11-28 09:01:00', 'msg': 'Epoch 1/5 - loss: 1.423 - acc: 0.45'},
        {'time': '2025-11-28 09:02:00', 'msg': 'Epoch 2/5 - loss: 1.125 - acc: 0.56'},
        {'time': '2025-11-28 09:03:00', 'msg': 'Epoch 3/5 - loss: 0.987 - acc: 0.62'},
        {'time': '2025-11-28 09:04:00', 'msg': 'Epoch 4/5 - loss: 0.842 - acc: 0.70'},
        {'time': '2025-11-28 09:05:00', 'msg': 'Epoch 5/5 - loss: 0.765 - acc: 0.74'},
        {'time': '2025-11-28 09:05:30', 'msg': 'Training complete. Best val_acc: 0.742'},
    ]
    return {'logs': dummy_logs}


@app.route('/admin/upload_dataset', methods=['GET', 'POST'])
def admin_upload_dataset():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        ext = filename.rsplit('.',1)[1].lower() if '.' in filename else ''
        try:
            if ext == 'zip':
                # save zip to a temp location and extract safely into DATASET_FOLDER
                os.makedirs(DATASET_FOLDER, exist_ok=True)
                tmp_path = os.path.join(DATASET_FOLDER, f"__tmp_upload_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip")
                file.save(tmp_path)
                with zipfile.ZipFile(tmp_path, 'r') as z:
                    for member in z.namelist():
                        member_path = os.path.normpath(member)
                        # prevent path traversal
                        if member_path.startswith('..') or os.path.isabs(member_path):
                            continue
                        target_path = os.path.join(DATASET_FOLDER, member_path)
                        target_dir = os.path.dirname(target_path)
                        os.makedirs(target_dir, exist_ok=True)
                        # extract file
                        with z.open(member) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                os.remove(tmp_path)
                flash('ZIP uploaded and extracted to dataset successfully')
            elif ext in ALLOWED_DATASET_EXT:
                # single image upload; optional category
                category = request.form.get('category', '').strip() or 'misc'
                target_dir = os.path.join(DATASET_FOLDER, secure_filename(category))
                os.makedirs(target_dir, exist_ok=True)
                save_path = os.path.join(target_dir, filename)
                file.save(save_path)
                flash(f'File saved to dataset/{category}/')
            else:
                flash('Unsupported file type for dataset upload')
        except Exception as e:
            flash(f'Error processing upload: {e}')
        return redirect(request.url)

    # GET: list dataset folders and counts
    folders = []
    try:
        if os.path.exists(DATASET_FOLDER):
            for name in sorted(os.listdir(DATASET_FOLDER)):
                path = os.path.join(DATASET_FOLDER, name)
                if os.path.isdir(path):
                    # count image files
                    count = 0
                    for root, _, files in os.walk(path):
                        for f in files:
                            if is_allowed_dataset_file(f):
                                count += 1
                    folders.append({'name': name, 'count': count})
    except Exception:
        folders = []

    return render_template('admin_upload_dataset.html', folders=folders)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin_login'))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
