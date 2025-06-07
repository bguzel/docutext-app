from flask import Flask, request, render_template, send_from_directory
import os
import uuid  # To generate unique filenames

# We'll import the function from our original engine script
from engine import ocr_pdf

# --- Basic Flask App Setup ---
app = Flask(__name__)

# --- Configuration ---
# Define the paths for our upload and download folders
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
# Ensure these folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
# Set a limit on the size of uploaded files, e.g., 16 Megabytes
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # --- File Handling Logic ---
        # 1. Check if a file was even uploaded
        if 'file' not in request.files:
            return render_template('index.html', message="Error: No file part in the request.")

        file = request.files['file']

        # 2. Check if the user selected a file
        if file.filename == '':
            return render_template('index.html', message="Error: No file selected.")

        # 3. Check if the file is a PDF
        if file and file.filename.endswith('.pdf'):
            # --- Processing Logic ---
            # 4. Get the selected language from the form
            language = request.form['language']

            # 5. Create a secure, unique filename to avoid conflicts
            # e.g., 'abc-123-def-456.pdf'
            unique_id = str(uuid.uuid4())
            input_filename = unique_id + ".pdf"
            output_filename = unique_id + "_searchable.pdf"

            input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
            output_filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], output_filename)

            # 6. Save the uploaded file to our 'uploads' folder
            file.save(input_filepath)

            # 7. Call our OCR engine function from Phase 1!
            try:
                ocr_pdf(input_path=input_filepath, output_path=output_filepath, language_code=language)

                # 8. Create a success message with a download link
                # The '/downloads/<filename>' part matches the route below
                success_message = f"Success! <a href='/downloads/{output_filename}'>Click here to download your searchable PDF.</a>"
                return render_template('index.html', message=success_message)

            except Exception as e:
                # If ocr_pdf fails, show an error
                return render_template('index.html', message=f"An error occurred during OCR: {e}")

        else:
            return render_template('index.html', message="Error: Invalid file type. Please upload a PDF.")

    # This is for a GET request (when you first visit the page)
    return render_template('index.html')


# --- Route for serving the processed files ---
# This allows users to actually download the files from the 'downloads' folder
@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    # Runs the Flask app. debug=True means it will auto-reload when you save changes.
    # We will run this locally on our computer.
    app.run(debug=True)