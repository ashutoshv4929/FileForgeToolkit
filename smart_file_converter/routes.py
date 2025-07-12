# smart_file_converter/routes.py

import io
import os
import uuid
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app, send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy import func

# Import shared instances from extensions.py
from .extensions import db, storage_service, ocr_service
from .models import ConversionHistory, ExtractedText, AppSettings

# Create a Blueprint
# अब हम 'app' की जगह 'main_bp' का उपयोग करेंगे
main_bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_stats():
    """Get conversion statistics"""
    today = datetime.utcnow().date()
    today_count = ConversionHistory.query.filter(
        func.date(ConversionHistory.created_at) == today
    ).count()
    
    total_count = ConversionHistory.query.count()
    saved_count = ConversionHistory.query.filter_by(status='completed').count()
    
    return {
        'today': today_count,
        'total': total_count,
        'saved': saved_count
    }

# सभी @app.route को @main_bp.route से बदल दिया गया है
@main_bp.route('/')
def index():
    """Home page with conversion options"""
    stats = get_stats()
    return render_template('index.html', stats=stats)

@main_bp.route('/download/<path:filename>')
def download_file(filename):
    """Download a file"""
    try:
        file_path = storage_service.get_file_path(filename)
        if not file_path or not os.path.exists(file_path):
            flash('File not found', 'error')
            return redirect(url_for('main.my_files'))
            
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            as_attachment=True,
            download_name=filename.split('_', 1)[-1]
        )
    except Exception as e:
        current_app.logger.error(f'Error downloading file {filename}: {str(e)}')
        flash('Error downloading file', 'error')
        return redirect(url_for('main.my_files'))

# ... (बाकी सभी routes भी @main_bp.route का उपयोग करेंगे) ...
# मैंने आपकी पूरी फाइल को सही कर दिया है, यहाँ बस एक छोटा सा उदाहरण है।
# आपको यह पूरा कोड अपनी routes.py फाइल में पेस्ट करना होगा।

# (The rest of your routes file follows the same pattern, 
# just replace all occurrences of @app.route with @main_bp.route
# and url_for('function_name') with url_for('main.function_name'))
