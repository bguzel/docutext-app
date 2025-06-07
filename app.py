from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

# We'll import the function from our original engine script
from engine import ocr_pdf

# --- App Initialization ---
app = Flask(__name__)

# --- Configuration ---
# A secret key is needed for session management and flashing messages
app.config['SECRET_KEY'] = os.urandom(24)  # Generates a secure random key
# Database configuration: Use SQLite, a simple file-based database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# File upload/download paths
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# --- Database and Extension Setup ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
# If a user tries to access a page that requires login, redirect them here
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


# --- User Model Definition ---
# This class defines the 'user' table in our database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    pages_processed = db.Column(db.Integer, default=0)

    # We will add plan info later, e.g., 'free' or 'pro'

    def __repr__(self):
        return f"User('{self.email}')"


# This function is required by Flask-Login to load a user from the DB
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Main Application Routes ---

@app.route('/', methods=['GET', 'POST'])
@login_required  # This line protects the page!
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.', 'danger')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)

        if file and file.filename.endswith('.pdf'):
            # --- Check User's Quota ---
            # For now, let's set a simple hard limit, e.g., 50 pages total
            # We will make this a monthly limit later
            if current_user.pages_processed >= 5:  # FREE TIER LIMIT
                flash('You have reached your free processing limit of 5 pages. Please upgrade for more.', 'warning')
                return redirect(url_for('index'))

            language = request.form['language']
            unique_id = str(uuid.uuid4())
            input_filename = unique_id + ".pdf"
            output_filename = unique_id + "_searchable.pdf"
            input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
            output_filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], output_filename)

            file.save(input_filepath)

            try:
                # We need to get page count before processing for the quota
                # This is a placeholder - a real implementation would use a library like PyPDF2 to count pages first.
                # For now, we'll just increment by 1 document.
                page_count_placeholder = 1  # In a real app, count pages here!

                ocr_pdf(input_path=input_filepath, output_path=output_filepath, language_code=language)

                # Update user's processed page count
                current_user.pages_processed += page_count_placeholder
                db.session.commit()

                success_message = f"Success! <a href='/downloads/{output_filename}'>Click here to download.</a> You have processed {current_user.pages_processed} page(s) out of your 5-page free limit."
                flash(success_message, 'success')

            except Exception as e:
                flash(f"An error occurred during OCR: {e}", 'danger')

            return redirect(url_for('index'))
        else:
            flash('Invalid file type. Please upload a PDF.', 'danger')
            return redirect(request.url)

    return render_template('index.html')


# --- Authentication Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already in use. Please log in.', 'warning')
            return redirect(url_for('login'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            # If user was trying to access a protected page, redirect them there
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')

    return render_template('login.html', title='Login')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# --- File Serving Route ---
@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)