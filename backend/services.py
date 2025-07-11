import os
import shutil
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

class FileService:
    """Handles file operations"""
    
    def __init__(self, upload_folder, allowed_extensions=None):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions or {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
        
    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def get_secure_filename(self, filename):
        """Generate a secure filename with a random prefix"""
        prefix = uuid.uuid4().hex[:8]
        filename = secure_filename(filename)
        return f"{prefix}_{filename}"
    
    def save_file(self, file):
        """Save uploaded file and return its path"""
        if not file or not self.allowed_file(file.filename):
            return None
            
        filename = self.get_secure_filename(file.filename)
        filepath = os.path.join(self.upload_folder, filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save the file
        file.save(filepath)
        return filepath
    
    def delete_file(self, filepath):
        """Delete a file if it exists"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")
            return False

class OCRService:
    """Handles OCR operations using Tesseract"""
    
    def __init__(self, tesseract_cmd=None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def extract_text_from_image(self, image_path):
        """Extract text from an image file"""
        try:
            return pytesseract.image_to_string(Image.open(image_path))
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            # Extract text from each page
            text = ''
            for i, image in enumerate(images):
                text += f"\n--- Page {i+1} ---\n"
                text += pytesseract.image_to_string(image)
                
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None
    
    def extract_text(self, file_path):
        """Extract text from a file (supports images and PDFs)"""
        if not os.path.exists(file_path):
            return None
            
        ext = file_path.rsplit('.', 1)[1].lower()
        
        if ext == 'pdf':
            return self.extract_text_from_pdf(file_path)
        else:
            return self.extract_text_from_image(file_path)
