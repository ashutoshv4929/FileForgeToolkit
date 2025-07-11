from flask import Blueprint, jsonify
from flask_sqlalchemy import SQLAlchemy

health_bp = Blueprint('health', __name__)

def check_database_connection():
    """Check if the database is accessible"""
    try:
        from . import db
        # Try to execute a simple query
        db.session.execute('SELECT 1')
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

@health_bp.route('/health')
def health_check():
    """Health check endpoint"""
    # Check database connection
    db_success, db_message = check_database_connection()
    
    # Prepare response
    status = 200 if db_success else 503
    
    return jsonify({
        'status': 'healthy' if db_success else 'unhealthy',
        'database': db_message,
        'timestamp': datetime.utcnow().isoformat()
    }), status
