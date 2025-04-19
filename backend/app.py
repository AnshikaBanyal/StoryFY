from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS  # Import Flask-CORS
import os
from AI_bot import extract_text_from_pdf, convert_to_script  # Replace with your script's logic

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/convert', methods=['POST'])
def convert_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    try:
        text = extract_text_from_pdf(file_path)
        script = convert_to_script(text)
        os.remove(file_path)  # Clean up
        return jsonify({'script': script})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
