import os
import logging
import json
from google.oauth2 import service_account
from google.cloud import vision
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

# Initialize Google Cloud Vision client
api_key = os.environ.get('GOOGLE_API_KEY')
if not api_key:
    logging.error("ERROR: GOOGLE_API_KEY environment variable not set")
    exit(1)

vision_client = vision.ImageAnnotatorClient(credentials=None, client_options={"api_key": api_key})

# --- END OF CHANGED SECTION ---

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