import os
import logging
from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from pathlib import Path
from config import Config

# Initialize extensions
from .extensions import db, migrate, login_manager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Configure upload folder
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
    
    # Set secret key
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Add proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize services
    from .services.local_storage import LocalStorageService
    from .services.ocr_service import OCRService
    
    storage_service = LocalStorageService(app.config['UPLOAD_FOLDER'])
    ocr_service = OCRService()
    
    # Add services to app context
    app.storage_service = storage_service
    app.ocr_service = ocr_service
    
    # Register blueprints
    from .main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Register error handlers
    from .errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    # Import and register user loader
    from .models import load_user
    login_manager.user_loader(load_user)
    
    # Add route to serve uploaded files
    @app.route(f'/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app