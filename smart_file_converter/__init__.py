import os
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, send_from_directory, current_app, jsonify
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()

# Import models to ensure they are registered with SQLAlchemy
from .models import User, ConversionHistory, ExtractedText, AppSettings

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)

    # Configure upload folder
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}

    # Set secret key if not already set
    if not app.secret_key:
        app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Add proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize services
    from .services.local_storage import LocalStorageService
    from .services.ocr_service import OCRService
    
    storage_service = LocalStorageService(app.config['UPLOAD_FOLDER'])
    ocr_service = OCRService(tesseract_cmd=app.config.get('TESSERACT_CMD'))
    
    # Add services to app context
    app.storage_service = storage_service
    app.ocr_service = ocr_service
    
    # Register blueprints
    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register health check blueprint
    from .health import health_bp
    app.register_blueprint(health_bp)
    
    # Import and register user loader
    from .models import load_user
    login_manager.user_loader(load_user)
    
    # Add route to serve uploaded files
    @app.route(f'/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'FileForgeToolkit'
        })
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    return app