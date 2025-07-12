# smart_file_converter/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from .services.cloud_storage import CloudStorageService
from .services.ocr_service import OCRService

# Initialize all extensions here
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Assuming 'auth' is a blueprint name
login_manager.login_message = 'Please log in to access this page.'
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()

# Initialize services here
storage_service = CloudStorageService()
ocr_service = OCRService()
