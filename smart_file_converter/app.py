import os
import logging
import json
from google.oauth2 import service_account
from google.cloud import vision
from google.cloud import storage
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import shutil
import uuid
import base64
import re
import binascii

# Set up logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

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

# Unset the GOOGLE_APPLICATION_CREDENTIALS environment variable if it exists
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']

# Google Cloud Vision initialization
api_key = os.environ.get('GOOGLE_API_KEY')
project_id = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')

# Unset GOOGLE_APPLICATION_CREDENTIALS to prevent default credential search
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']

# Initialize Vision client with API key
if api_key and project_id:
    vision_client = vision.ImageAnnotatorClient(
        credentials=None,
        client_options={"api_key": api_key, "quota_project_id": project_id}
    )
    logging.debug(f"Google Cloud Vision initialized with API key and project ID")
else:
    vision_client = None
    logging.error("Google Cloud Vision API not configured")
    logging.debug(f"GOOGLE_API_KEY: {'set' if api_key else 'not set'}")
    logging.debug(f"GOOGLE_CLOUD_PROJECT_ID: {'set' if project_id else 'not set'}")

# Initialize Google Cloud Storage
bucket_name = os.environ.get('GOOGLE_CLOUD_STORAGE_BUCKET_NAME')
if bucket_name:
    storage_client = storage.Client(credentials=None, client_options={"api_key": api_key, "quota_project_id": project_id})
    bucket = storage_client.bucket(bucket_name)
else:
    storage_client = None
    bucket = None
    logging.warning("Google Cloud Storage not configured - missing bucket name")

def save_file_locally(file):
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    return file_path

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()

# Import routes
import routes