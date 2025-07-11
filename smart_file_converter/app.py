import os
import logging
import json
import sys
from flask import Flask
from smart_file_converter.extensions import db
from werkzeug.middleware.proxy_fix import ProxyFix
import shutil
import uuid
import base64
import re
import binascii

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///smart_converter.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = 'static/processed'

# --- GOOGLE CLOUD CONFIGURATION ---

# Get project ID from environment variable
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
if not project_id:
    logging.error("ERROR: GOOGLE_CLOUD_PROJECT_ID environment variable not set.")
    exit(1)
app.config['GOOGLE_CLOUD_PROJECT'] = project_id

# If GOOGLE_SERVICE_ACCOUNT_JSON is set, write it to a file and set GOOGLE_APPLICATION_CREDENTIALS
if 'GOOGLE_SERVICE_ACCOUNT_JSON' in os.environ:
    service_account_info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
    with open('service-account-key.json', 'w') as f:
        json.dump(service_account_info, f)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'service-account-key.json'

# Initialize services
from .services import OCRService
ocr_service = OCRService()

def save_file_locally(file):
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    return file_path

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    db.create_all()

if __name__ == '__main__':
    # Local development
    from routes import *
    app.run()
else:
    # Production (Gunicorn)
    from .routes import *
    application = app