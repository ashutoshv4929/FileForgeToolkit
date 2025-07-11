from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

def error_response(status_code, message=None):
    """Generate a JSON error response with the given status code and message."""
    payload = {
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error'),
        'status': status_code
    }
    if message:
        payload['message'] = message
    
    response = jsonify(payload)
    response.status_code = status_code
    return response

def bad_request(message):
    """400 Bad Request"""
    return error_response(400, message)

def unauthorized(message='Please authenticate to access this resource'):
    """401 Unauthorized"""
    return error_response(401, message)

def forbidden(message='You do not have permission to access this resource'):
    """403 Forbidden"""
    return error_response(403, message)

def not_found(message='The requested resource was not found'):
    """404 Not Found"""
    return error_response(404, message)

def method_not_allowed(message='The method is not allowed for the requested URL'):
    """405 Method Not Allowed"""
    return error_response(405, message)

def conflict(message='A resource with this ID already exists'):
    """409 Conflict"""
    return error_response(409, message)

def too_many_requests(message='Too many requests, please try again later'):
    """429 Too Many Requests"""
    return error_response(429, message)

def internal_error(message='An unexpected error has occurred'):
    """500 Internal Server Error"""
    return error_response(500, message)

def service_unavailable(message='The service is temporarily unavailable'):
    """503 Service Unavailable"""
    return error_response(503, message)
