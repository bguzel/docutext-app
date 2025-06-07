# --- Imports ---
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import os
import uuid
from engine import ocr_pdf

# ### CORRECT IMPORT based on your new screenshot ###
from paddle_billing import Client, Environment, Options

# --- App Initialization and Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
# Find this old configuration:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Replace it with this new, more robust configuration:
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # We are on Render, use the PostgreSQL database
    # The 'postgresql' scheme is what SQLAlchemy expects.
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://")
else:
    # We are running locally, use the SQLite file
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File Paths
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# --- Paddle Configuration ---
PADDLE_API_KEY = 'pdl_sdbx_apikey_01jx5mzya3awnj3j6ctjpvna4p_nNaZS23jBqa04G0Ap4sZGM_Av6'
PADDLE_PRICE_ID = 'pri_01jx5mx7gg1n4716jhtf0myfvn'

# ### CORRECT INITIALIZATION based on your new screenshot ###
paddle_client = Client(
    PADDLE_API_KEY,
    options=Options(Environment.SANDBOX)
)

# --- Database and Login Manager Setup ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- Database Model Definition (Unchanged) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    pages_processed = db.Column(db.Integer, default=0)
    plan = db.Column(db.String(50), default='free', nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Main Application Route (OCR Processor) (Unchanged) ---
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        limit = 5 if current_user.plan == 'free' else 200
        if current_user.pages_processed >= limit:
            flash(f"You have reached your processing limit of {limit} pages for the '{current_user.plan}' plan. Please upgrade.", 'warning')
            return redirect(url_for('index'))
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '' or not file.filename.endswith('.pdf'):
            flash('Please select a valid PDF file.', 'danger')
            return redirect(request.url)
        language = request.form['language']
        unique_id = str(uuid.uuid4())
        input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}.pdf")
        output_filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], f"{unique_id}_searchable.pdf")
        file.save(input_filepath)
        try:
            page_count_placeholder = 1
            ocr_pdf(input_path=input_filepath, output_path=output_filepath, language_code=language)
            current_user.pages_processed += page_count_placeholder
            db.session.commit()
            success_message = f"Success! <a href='/downloads/{unique_id}_searchable.pdf'>Click here to download.</a> Usage: {current_user.pages_processed}/{limit} pages."
            flash(success_message, 'success')
        except Exception as e:
            flash(f"An error occurred during OCR: {e}", 'danger')
        return redirect(url_for('index'))
    return render_template('index.html')


# --- Paddle Payment Routes ---
# --- Paddle Payment Routes ---
# --- Paddle Payment Routes ---
@app.route('/create-paddle-checkout')
@login_required
def create_paddle_checkout():
    try:
        transaction_data = {
            "items": [
                {
                    "price_id": PADDLE_PRICE_ID,
                    "quantity": 1
                }
            ],
            "customer": {
                "email": current_user.email
            },
            "checkout": {
                "settings": {
                    "success_url": url_for('success', _external=True),
                    "cancel_url": url_for('cancel', _external=True),
                }
            }
        }

        transaction = paddle_client.transactions.create(transaction_data)

        # This line is correct, the error is happening before it.
        checkout_url = transaction.checkout.url
        return redirect(checkout_url)

    except Exception as e:
        # ### THIS IS THE CRITICAL CHANGE ###
        # We are now flashing the ACTUAL error message to the browser.
        error_message = str(e)
        print(f"PADDLE API ERROR: {error_message}")  # Still print to logs
        flash(f"Error communicating with provider: {error_message}", 'danger')

        return redirect(url_for('index'))

@app.route('/success')
@login_required
def success():
    current_user.plan = 'pro'
    current_user.pages_processed = 0
    db.session.commit()
    flash('Congratulations! You have successfully upgraded to the Pro plan.', 'success')
    return redirect(url_for('index'))

@app.route('/cancel')
@login_required
def cancel():
    flash('Payment was cancelled. You are still on the free plan.', 'info')
    return redirect(url_for('index'))


# --- Authentication and Other Routes (All Unchanged) ---
# ... (The rest of the file is identical to before) ...
@app.route('/register', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email address already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # ### THIS IS THE CORRECTED LINE ###
        # We now explicitly set the plan for every new user.
        new_user = User(email=email, password_hash=hashed_password, plan='free')

        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            return redirect(request.args.get('next') or url_for('index'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    return render_template('login.html', title='Login')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/downloads/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)