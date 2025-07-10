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
logging.basicConfig(level=logging.DEBUG)

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
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PROCESSED_FOLDER'] = 'static/processed'

# Google Cloud configuration
app.config['GOOGLE_CLOUD_PROJECT'] = os.environ.get("GOOGLE_CLOUD_PROJECT")

# Google Cloud credentials setup
google_creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
if google_creds_json:
    try:
        google_creds_dict = json.loads(google_creds_json)
        
        # Fix private key padding if needed
        private_key = google_creds_dict.get('private_key', '')
        if private_key:
            # Remove extra spaces/newlines
            private_key = re.sub(r'\s+', '', private_key)
            
            # Ensure proper padding
            try:
                base64.b64decode(private_key)
            except binascii.Error:
                # Add padding if missing
                padding_needed = 4 - (len(private_key) % 4)
                private_key += '=' * padding_needed
                
            google_creds_dict['private_key'] = private_key
            
        credentials = service_account.Credentials.from_service_account_info(google_creds_dict)
        print("Google credentials loaded successfully")
    except Exception as e:
        print(f"Error loading Google credentials: {e}")
        credentials = None
else:
    print("GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
    credentials = None

vision_client = vision.ImageAnnotatorClient(credentials=credentials)
storage_client = storage.Client(credentials=credentials, project=os.environ.get('GCLOUD_PROJECT'))

# Use Google Cloud Storage
if storage_client:
    bucket_name = os.environ.get('GCLOUD_STORAGE_BUCKET')
    bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
        bucket.create()

def save_file_to_gcs(file):
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    blob = bucket.blob(filename)
    blob.upload_from_file(file)
    return blob.public_url

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()

# Import routes
import routes
