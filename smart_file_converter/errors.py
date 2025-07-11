from flask import render_template, request, jsonify
from smart_file_converter import db
from smart_file_converter.api.errors import error_response as api_error_response

def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']

def error_response(status_code, message=None):
    if wants_json_response():
        return api_error_response(status_code, message)
    return message, status_code

def bad_request(message):
    return error_response(400, f'Bad request: {message}')

def unauthorized(message='Please authenticate to access this resource'):
    return error_response(401, f'Unauthorized: {message}')

def forbidden(message='You do not have permission to access this resource'):
    return error_response(403, f'Forbidden: {message}')

def not_found(message='The requested resource was not found'):
    return error_response(404, message)

def method_not_allowed(message='The method is not allowed for the requested URL'):
    return error_response(405, f'Method not allowed: {message}')

def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500, 'An unexpected error has occurred')
    return render_template('errors/500.html', error=error), 500

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request_error(error):
        return bad_request(error.description or 'Invalid request')

    @app.errorhandler(401)
    def unauthorized_error(error):
        return unauthorized(error.description or 'Please authenticate')

    @app.errorhandler(403)
    def forbidden_error(error):
        return forbidden(error.description or 'Insufficient permissions')

    @app.errorhandler(404)
    def not_found_error(error):
        return not_found(error.description or 'Resource not found')

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return method_not_allowed(error.description or 'Method not allowed')

    @app.errorhandler(500)
    def internal_error_handler(error):
        return internal_error(error)

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f'Unhandled exception: {str(error)}', exc_info=True)
        return internal_error(error)
