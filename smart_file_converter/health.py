from flask import Blueprint, jsonify, current_app
import subprocess
from datetime import datetime

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

def check_tesseract():
    """Check if Tesseract OCR is installed and accessible"""
    try:
        result = subprocess.run(
            ['tesseract', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return True, "Tesseract OCR is available"
        else:
            return False, f"Tesseract check failed: {result.stderr}"
    except Exception as e:
        return False, f"Tesseract check error: {str(e)}"

@health_bp.route('/health')
def health_check():
    """Health check endpoint"""
    # Check database connection
    db_success, db_message = check_database_connection()
    
    # Check Tesseract OCR
    tesseract_success, tesseract_message = check_tesseract()
    
    # Check upload folder
    upload_folder = current_app.config.get('UPLOAD_FOLDER', '')
    upload_folder_ok = True
    upload_message = ""
    
    if not upload_folder:
        upload_folder_ok = False
        upload_message = "UPLOAD_FOLDER not configured"
    else:
        try:
            import os
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder, exist_ok=True)
            # Try to create a test file
            test_file = os.path.join(upload_folder, '.healthcheck')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            upload_message = f"Upload folder is writable: {upload_folder}"
        except Exception as e:
            upload_folder_ok = False
            upload_message = f"Upload folder error: {str(e)}"
    
    # Prepare response
    all_ok = db_success and tesseract_success and upload_folder_ok
    status = 200 if all_ok else 503
    
    return jsonify({
        'status': 'ok' if all_ok else 'error',
        'services': {
            'database': {
                'status': 'ok' if db_success else 'error',
                'message': db_message
            },
            'tesseract_ocr': {
                'status': 'ok' if tesseract_success else 'error',
                'message': tesseract_message
            },
            'upload_folder': {
                'status': 'ok' if upload_folder_ok else 'error',
                'message': upload_message
            }
        },
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'  # You can use your app version here
    }), status
