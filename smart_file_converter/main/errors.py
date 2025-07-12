from flask import render_template, jsonify
from werkzeug.exceptions import HTTPException

def init_app(app):
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html'), 400

    # Handle all other HTTP exceptions
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return render_template(
            'errors/error.html',
            error=error,
            status_code=error.code,
            description=error.description
        ), error.code
