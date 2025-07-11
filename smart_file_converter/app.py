import os
import logging
import sys
from flask import Flask, send_from_directory
from smart_file_converter.extensions import db, login
from werkzeug.middleware.proxy_fix import ProxyFix
import shutil
import uuid
from pathlib import Path
from smart_file_converter.services import ocr_service, storage_service

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

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}

# Initialize services
from .services import OCRService, StorageService

# Initialize services
ocr_service = OCRService()
storage_service = StorageService(storage_dir=UPLOAD_FOLDER)

# Add route to serve uploaded files
@app.route(f'/{UPLOAD_FOLDER}/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Initialize extensions
db.init_app(app)
login.init_app(app)
login.login_view = 'auth.login'

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Local development
    from routes import *
    app.run()
else:
    # Production (Gunicorn)
    from .routes import *
    application = app