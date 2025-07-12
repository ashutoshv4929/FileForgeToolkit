from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from . import bp
from ..models import ConversionHistory, ExtractedText, db
from ..services.ocr_service import OCRService

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('main/index.html')

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the file with OCR
        ocr_service = current_app.ocr_service
        try:
            text = ocr_service.extract_text(filepath)
            
            # Save to database
            conversion = ConversionHistory(
                user_id=current_user.id,
                original_filename=filename,
                file_path=filepath,
                status='completed'
            )
            db.session.add(conversion)
            
            extracted_text = ExtractedText(
                conversion_id=conversion.id,
                text=text,
                language='eng'  # Default language
            )
            db.session.add(extracted_text)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'text': text,
                'filename': filename,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            current_app.logger.error(f"Error processing file: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return jsonify({
        'success': False,
        'error': 'File type not allowed'
    }), 400
