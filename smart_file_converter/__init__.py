import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize storage service
    from .services.local_storage import LocalStorageService
    storage_service = LocalStorageService(app.config['UPLOAD_FOLDER'])
    
    # Register blueprints
    from .main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Register error handlers
    from .errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    # Add storage service to app context
    app.storage_service = storage_service
    
    return app

# Import models to ensure they are registered with SQLAlchemy
from . import models