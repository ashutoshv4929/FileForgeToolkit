from flask import Blueprint

bp = Blueprint('main', __name__)

# Import routes after creating the blueprint to avoid circular imports
from smart_file_converter.main import routes

# Initialize error handlers
def init_app(app):
    from . import errors  # noqa
    errors.init_app(app)
