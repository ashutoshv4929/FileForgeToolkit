import io
import os
import uuid
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, current_app, send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy import func

from app import app, db, storage_service
from .models import ConversionHistory, ExtractedText, AppSettings
from smart_file_converter.services.ocr_service import OCRService

# Initialize services
ocr_service = OCRService()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}

# Get upload folder from app config
UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'uploads')

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

@app.route('/')
def index():
    """Home page with conversion options"""
    stats = get_stats()
    return render_template('index.html', stats=stats)

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a file"""
    try:
        file_path = storage_service.get_file_path(filename)
        if not file_path or not os.path.exists(file_path):
            flash('File not found', 'error')
            return redirect(url_for('my_files'))
            
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            as_attachment=True,
            download_name=filename.split('_', 1)[-1]  # Remove UUID from download filename
        )
    except Exception as e:
        app.logger.error(f'Error downloading file {filename}: {str(e)}')
        flash('Error downloading file', 'error')
        return redirect(url_for('my_files'))

@app.route('/upload')
def upload_page():
    """File upload page"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        
        # Save file using storage service
        file_path = storage_service.upload_file(file, filename)
        
        # Log the upload
        history = ConversionHistory(
            filename=filename,
            file_type=filename.rsplit('.', 1)[1].lower(),
            status='uploaded',
            operation='upload',
            file_path=file_path
        )
        db.session.add(history)
        db.session.commit()
        
        flash('File successfully uploaded')
        return redirect(url_for('my_files'))
    
    flash('Invalid file type. Please upload PDF, DOC, DOCX, TXT, or image files.', 'error')
    return redirect(request.url)
    
    flash('Invalid file type. Please upload PDF, DOC, DOCX, TXT, or image files.', 'error')
    return redirect(request.url)

@app.route('/extract-text')
def extract_text_page():
    """OCR text extraction page"""
    return render_template('extract_text.html')

@app.route('/extract-text', methods=['POST'])
def extract_text():
    """Handle OCR text extraction"""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    if file and file.filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'gif', 'pdf']:
        try:
            # Generate unique filename and save file using storage service
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            filepath = storage_service.upload_file(file, filename)
            
            # Extract text using OCR
            extracted_text, confidence = ocr_service.extract_text(filepath)
            
            if extracted_text:
                # Save extracted text to database
                text_record = ExtractedText(
                    filename=filename,
                    original_filename=file.filename,
                    extracted_text=extracted_text,
                    confidence_score=confidence
                )
                db.session.add(text_record)
                
                # Save to conversion history
                conversion = ConversionHistory(
                    filename=filename,
                    original_filename=file.filename,
                    file_type=file.filename.rsplit('.', 1)[1].lower(),
                    conversion_type='ocr_extraction',
                    file_size=os.path.getsize(filepath),
                    status='completed',
                    processed_at=datetime.utcnow()
                )
                db.session.add(conversion)
                db.session.commit()
                
                return render_template('extract_text.html', 
                                     extracted_text=extracted_text, 
                                     confidence=confidence,
                                     filename=file.filename)
            else:
                flash('No text could be extracted from the image', 'warning')
                return redirect(request.url)
                
        except Exception as e:
            app.logger.error(f'OCR extraction error: {str(e)}')
            flash(f'Error extracting text: {str(e)}', 'error')
            return redirect(request.url)
    
    flash('Invalid file type. Please upload an image or PDF file.', 'error')
    return redirect(request.url)

@app.route('/save-text', methods=['POST'])
def save_text():
    """Save extracted text to file"""
    text_content = request.form.get('text_content')
    original_filename = request.form.get('original_filename', 'extracted_text')
    
    if not text_content:
        flash('No text to save', 'error')
        return redirect(url_for('extract_text_page'))
    
    try:
        # Generate filename for text file
        text_filename = f"{original_filename.rsplit('.', 1)[0]}_extracted.txt"
        
        # Save text to file using storage service
        from io import StringIO
        file_obj = StringIO(text_content)
        file_path = storage_service.upload_file(file_obj, text_filename, content_type='text/plain')
        
        flash('Text saved successfully!', 'success')
        return redirect(url_for('download_file', filename=os.path.basename(file_path)))
        
    except Exception as e:
        app.logger.error(f'Error saving text: {str(e)}')
        flash(f'Error saving text: {str(e)}', 'error')
        return redirect(url_for('extract_text_page'))

@app.route('/my-files')
def my_files():
    """Display user's uploaded files"""
    files = ConversionHistory.query.order_by(ConversionHistory.created_at.desc()).all()
    
    # Add file existence check and human-readable size
    for file in files:
        file.exists = storage_service.file_exists(file.filename) if file.filename else False
        file.human_size = _human_readable_size(file.file_size) if file.file_size else 'N/A'
    
    return render_template('my_files.html', files=files)

def _human_readable_size(size_bytes):
    """Convert file size in bytes to human readable format"""
    if not size_bytes:
        return "0 B"
    
    size_names = ('B', 'KB', 'MB', 'GB', 'TB')
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.2f} {size_names[i]}"

@app.route('/history')
def history():
    """Display conversion history"""
    history_records = ConversionHistory.query.order_by(ConversionHistory.created_at.desc()).all()
    
    # Add human-readable size and format timestamps
    for record in history_records:
        record.human_size = _human_readable_size(record.file_size) if record.file_size else 'N/A'
        record.formatted_date = record.processed_at.strftime('%Y-%m-%d %H:%M:%S') if record.processed_at else 'N/A'
        record.exists = storage_service.file_exists(record.filename) if record.filename else False
    
    return render_template('history.html', history=history_records)

# PDF Tools Routes

@app.route('/merge-pdf')
def merge_pdf_page():
    """Merge PDF page"""
    return render_template('pdf_tools/merge.html')

@app.route('/split-pdf')
def split_pdf_page():
    """Split PDF page"""
    return render_template('pdf_tools/split.html')

@app.route('/compress-pdf')
def compress_pdf_page():
    """Compress PDF page"""
    return render_template('pdf_tools/compress.html')

@app.route('/pdf-to-images')
def pdf_to_images_page():
    """PDF to Images page"""
    return render_template('pdf_tools/pdf_to_images.html')

@app.route('/images-to-pdf')
def images_to_pdf_page():
    """Images to PDF page"""
    return render_template('pdf_tools/images_to_pdf.html')

@app.route('/merge-pdf', methods=['POST'])
def merge_pdf():
    """Handle PDF merging"""
    from PyPDF2 import PdfMerger
    
    files = request.files.getlist('files')
    if not files or len(files) < 2:
        flash('Please select at least 2 PDF files to merge', 'error')
        return redirect(request.url)
    
    try:
        merger = PdfMerger()
        temp_files = []
        
        # Save uploaded files temporarily
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                # Save file using storage service
                filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                file_path = storage_service.upload_file(file, filename)
                
                # Read the file back for merging
                with storage_service.get_file(file_path) as f:
                    merger.append(f)
                
                temp_files.append(file_path)
        
        # Create merged PDF in memory
        import io
        merged_pdf = io.BytesIO()
        merger.write(merged_pdf)
        merger.close()
        merged_pdf.seek(0)
        
        # Save merged PDF using storage service
        merged_filename = f"merged_{uuid.uuid4().hex[:8]}.pdf"
        merged_path = storage_service.upload_file(merged_pdf, merged_filename, content_type='application/pdf')
        
        # Clean up temp files
        for temp_file in temp_files:
            storage_service.delete_file(temp_file)
        
        # Save to database
        file_size = os.path.getsize(merged_path) if os.path.exists(merged_path) else 0
        conversion = ConversionHistory(
            filename=os.path.basename(merged_path),
            original_filename='merged_pdf',
            file_type='pdf',
            conversion_type='merge_pdf',
            file_size=file_size,
            status='completed',
            processed_at=datetime.utcnow(),
            file_path=merged_path
        )
        db.session.add(conversion)
        db.session.commit()
        
        flash('PDFs merged successfully!', 'success')
        return redirect(url_for('download_file', filename=os.path.basename(merged_path)))
        
    except Exception as e:
        app.logger.error(f'PDF merge error: {str(e)}')
        flash(f'Error merging PDFs: {str(e)}', 'error')
        return redirect(request.url)

@app.route('/split-pdf', methods=['POST'])
def split_pdf():
    """Handle PDF splitting"""
    from PyPDF2 import PdfReader, PdfWriter
    import zipfile
    
    if 'file' not in request.files:
        flash('No PDF file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if not file or not file.filename.lower().endswith('.pdf'):
        flash('Please select a PDF file', 'error')
        return redirect(request.url)
    
    try:
        # Save uploaded file using storage service
        filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        file_path = storage_service.upload_file(file, filename)
        
        # Read the PDF
        with storage_service.get_file(file_path) as f:
            reader = PdfReader(f)
            
            # Split PDF into pages
            page_files = []
            for page_num in range(len(reader.pages)):
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])
                
                # Save page to memory
                page_buffer = io.BytesIO()
                writer.write(page_buffer)
                page_buffer.seek(0)
                
                # Save page using storage service
                page_filename = f"page_{page_num + 1}.pdf"
                page_path = storage_service.upload_file(page_buffer, page_filename, content_type='application/pdf')
                page_files.append(page_path)
        
        # Create zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for page_path in page_files:
                with storage_service.get_file(page_path) as page_file:
                    zip_file.writestr(os.path.basename(page_path), page_file.read())
        
        zip_buffer.seek(0)
        
        # Save zip file using storage service
        zip_filename = f"split_pages_{uuid.uuid4().hex[:8]}.zip"
        zip_path = storage_service.upload_file(zip_buffer, zip_filename, content_type='application/zip')
        
        # Clean up
        storage_service.delete_file(file_path)
        for page_file in page_files:
            storage_service.delete_file(page_file)
        
        # Save to database
        file_size = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
        conversion = ConversionHistory(
            filename=os.path.basename(zip_path),
            original_filename=file.filename,
            file_type='pdf',
            conversion_type='split_pdf',
            file_size=file_size,
            status='completed',
            processed_at=datetime.utcnow(),
            file_path=zip_path
        )
        db.session.add(conversion)
        db.session.commit()
        
        flash('PDF split successfully!', 'success')
        return send_file(zip_path, as_attachment=True, download_name='split_pages.zip')
        
    except Exception as e:
        app.logger.error(f'PDF split error: {str(e)}')
        flash(f'Error splitting PDF: {str(e)}', 'error')
        return redirect(request.url)

@app.route('/pdf-to-images', methods=['POST'])
def pdf_to_images():
    """Convert PDF pages to images"""
    import pdf2image
    import zipfile
    
    if 'file' not in request.files:
        flash('No PDF file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if not file or not file.filename.lower().endswith('.pdf'):
        flash('Please select a PDF file', 'error')
        return redirect(request.url)
    
    try:
        # Save uploaded file using storage service
        filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        file_path = storage_service.upload_file(file, filename)
        
        # Convert PDF to images in memory
        with storage_service.get_file(file_path) as f:
            # Save to a temporary file for pdf2image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(f.read())
                temp_pdf_path = temp_pdf.name
            
            try:
                images = pdf2image.convert_from_path(temp_pdf_path)
            finally:
                os.unlink(temp_pdf_path)
        
        # Save images to storage service
        image_files = []
        for i, image in enumerate(images):
            # Save image to memory
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Save image using storage service
            image_filename = f"page_{i + 1}.png"
            image_path = storage_service.upload_file(img_buffer, image_filename, content_type='image/png')
            image_files.append(image_path)
        
        # Create zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for img_path in image_files:
                with storage_service.get_file(img_path) as img_file:
                    zip_file.writestr(os.path.basename(img_path), img_file.read())
        
        zip_buffer.seek(0)
        
        # Save zip file using storage service
        zip_filename = f"pdf_images_{uuid.uuid4().hex[:8]}.zip"
        zip_path = storage_service.upload_file(zip_buffer, zip_filename, content_type='application/zip')
        
        # Clean up
        storage_service.delete_file(file_path)
        for img_file in image_files:
            storage_service.delete_file(img_file)
        
        # Save to database
        file_size = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
        conversion = ConversionHistory(
            filename=os.path.basename(zip_path),
            original_filename=file.filename,
            file_type='pdf',
            conversion_type='pdf_to_images',
            file_size=file_size,
            status='completed',
            processed_at=datetime.utcnow(),
            file_path=zip_path
        )
        db.session.add(conversion)
        db.session.commit()
        
        flash('PDF converted to images successfully!', 'success')
        return send_file(zip_path, as_attachment=True, download_name='pdf_images.zip')
        
    except Exception as e:
        app.logger.error(f'PDF to images error: {str(e)}')
        flash(f'Error converting PDF to images: {str(e)}', 'error')
        return redirect(request.url)

@app.route('/images-to-pdf', methods=['POST'])
def images_to_pdf():
    """Convert images to PDF"""
    from PIL import Image
    
    files = request.files.getlist('files')
    if not files:
        flash('Please select image files', 'error')
        return redirect(request.url)
    
    try:
        images = []
        temp_file_paths = []
        
        for file in files:
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Save file using storage service
                filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                file_path = storage_service.upload_file(file, filename)
                
                # Open image from storage
                with storage_service.get_file(file_path) as f:
                    # Open and convert image
                    image = Image.open(f)
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Save to memory
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='JPEG')
                    img_buffer.seek(0)
                    
                    # Create a new image from buffer
                    img_buffer.seek(0)
                    images.append(Image.open(img_buffer))
                    
                    # Store the path for cleanup
                    temp_file_paths.append(file_path)
        
        if not images:
            flash('No valid image files found', 'error')
            return redirect(request.url)
        
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        images[0].save(pdf_buffer, format='PDF', save_all=True, append_images=images[1:])
        pdf_buffer.seek(0)
        
        # Save PDF using storage service
        pdf_filename = f"images_to_pdf_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = storage_service.upload_file(pdf_buffer, pdf_filename, content_type='application/pdf')
        
        # Clean up temp files
        for temp_file in temp_file_paths:
            storage_service.delete_file(temp_file)
        
        # Save to database
        file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
        conversion = ConversionHistory(
            filename=os.path.basename(pdf_path),
            original_filename='images_to_pdf',
            file_type='pdf',
            conversion_type='images_to_pdf',
            file_size=file_size,
            status='completed',
            processed_at=datetime.utcnow(),
            file_path=pdf_path
        )
        db.session.add(conversion)
        db.session.commit()
        
        flash('Images converted to PDF successfully!', 'success')
        return send_file(pdf_path, as_attachment=True, download_name='images.pdf')
        
    except Exception as e:
        app.logger.error(f'Images to PDF error: {str(e)}')
        flash(f'Error converting images to PDF: {str(e)}', 'error')
        return redirect(request.url)

@app.route('/settings')
def settings():
    """Display settings page"""
    return render_template('settings.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint for getting statistics"""
    stats = get_stats()
    return jsonify(stats)

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum file size is 16MB.', 'error')
    return redirect(url_for('upload_page'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f'Internal server error: {str(e)}')
    return render_template('500.html'), 500
