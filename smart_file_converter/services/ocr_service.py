import pytesseract
from PIL import Image
import logging
import os
import pdf2image
import shutil
from pathlib import Path

# Set Tesseract command path
pytesseract.pytesseract.tesseract_cmd = shutil.which('tesseract') or '/usr/bin/tesseract'

class OCRService:
    def __init__(self):
        # Check if Tesseract is available
        try:
            # Test Tesseract availability
            pytesseract.get_tesseract_version()
            self.available = True
            logging.info("Tesseract OCR initialized successfully")
        except Exception as e:
            self.available = False
            logging.error(f"Tesseract initialization error: {str(e)}")

    def extract_text(self, file_path):
        """Extract text from an image or PDF file"""
        if not self.available:
            return "OCR service not available"
            
        try:
            # Handle PDF files
            if file_path.lower().endswith('.pdf'):
                images = pdf2image.convert_from_path(file_path)
                text = ''
                for i, image in enumerate(images):
                    # Convert PIL image to text
                    page_text = pytesseract.image_to_string(image)
                    text += f"\n--- Page {i+1} ---\n{page_text}"
                return text.strip()
            
            # Handle image files
            else:
                return pytesseract.image_to_string(Image.open(file_path))
                
        except Exception as e:
            logging.error(f"Error extracting text: {str(e)}")
            raise RuntimeError(f"Failed to extract text: {str(e)}")

    def extract_text_from_image(self, image_path):
        """Extract text from an image file"""
        try:
            return pytesseract.image_to_string(Image.open(image_path))
        except Exception as e:
            logging.error(f"Error during OCR: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        if not self.available:
            return "OCR service not available"
            
        # For PDFs, we use pdf2image to convert to images
        images = pdf2image.convert_from_path(pdf_path)
        text = ''
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image)
            text += f"\n--- Page {i+1} ---\n{page_text}"
        return text.strip()

    def is_configured(self):
        """Check if OCR service is properly configured"""
        return self.available
    
    def detect_document_text(self, file_path):
        """Detect and extract document text with layout information"""
        if not self.available:
            raise Exception("Tesseract OCR not properly configured")
        
        try:
            with Image.open(file_path) as image:
                text = pytesseract.image_to_string(image)
                return text, text
            
        except Exception as e:
            logging.error(f"Error detecting document text: {str(e)}")
            raise e
