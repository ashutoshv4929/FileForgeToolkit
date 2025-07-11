from flask import Blueprint

bp = Blueprint('main', __name__)

from smart_file_converter.main import routes, errors
