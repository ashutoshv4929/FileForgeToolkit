from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Create blueprints
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__, url_prefix='/auth')
api = Blueprint('api', __name__, url_prefix='/api')

# Import models and services
from .models import db, User, Conversion, ExtractedText
from .services import FileService, OCRService

# Initialize services
file_service = None
ocr_service = None

def init_services(app):
    """Initialize services with app context"""
    global file_service, ocr_service
    file_service = FileService(
        upload_folder=app.config['UPLOAD_FOLDER'],
        allowed_extensions=app.config['ALLOWED_EXTENSIONS']
    )
    ocr_service = OCRService(tesseract_cmd=app.config.get('TESSERACT_CMD'))

# Main routes
@main.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    # Save the uploaded file
    filepath = file_service.save_file(file)
    if not filepath:
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Create conversion record
        conversion = Conversion(
            user_id=current_user.id,
            original_filename=secure_filename(file.filename),
            conversion_type='ocr',
            status='processing'
        )
        db.session.add(conversion)
        db.session.commit()
        
        # Process the file (OCR)
        text = ocr_service.extract_text(filepath)
        
        if text:
            # Save extracted text
            extracted = ExtractedText(
                conversion_id=conversion.id,
                text_content=text
            )
            db.session.add(extracted)
            
            # Update conversion status
            conversion.status = 'completed'
            conversion.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'text': text,
                'conversion_id': conversion.id
            })
        else:
            conversion.status = 'failed'
            conversion.error_message = 'Failed to extract text'
            db.session.commit()
            return jsonify({'error': 'Failed to extract text'}), 500
            
    except Exception as e:
        if 'conversion' in locals():
            conversion.status = 'failed'
            conversion.error_message = str(e)
            db.session.commit()
        return jsonify({'error': str(e)}), 500

# Auth routes
@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        # Handle login logic
        pass
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        # Handle registration logic
        pass
    return render_template('auth/register.html')

# API routes
@api.route('/conversions')
@login_required
def get_conversions():
    """Get user's conversion history"""
    conversions = Conversion.query.filter_by(user_id=current_user.id)\
        .order_by(Conversion.created_at.desc())\
        .all()
    return jsonify([{
        'id': c.id,
        'original_filename': c.original_filename,
        'status': c.status,
        'created_at': c.created_at.isoformat(),
        'completed_at': c.completed_at.isoformat() if c.completed_at else None
    } for c in conversions])

@api.route('/conversions/<int:conversion_id>')
@login_required
def get_conversion(conversion_id):
    """Get details of a specific conversion"""
    conversion = Conversion.query.get_or_404(conversion_id)
    if conversion.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    extracted = ExtractedText.query.filter_by(conversion_id=conversion_id).first()
    
    return jsonify({
        'id': conversion.id,
        'original_filename': conversion.original_filename,
        'status': conversion.status,
        'created_at': conversion.created_at.isoformat(),
        'completed_at': conversion.completed_at.isoformat() if conversion.completed_at else None,
        'error_message': conversion.error_message,
        'extracted_text': extracted.text_content if extracted else None
    })
