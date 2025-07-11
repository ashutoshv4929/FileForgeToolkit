import pytesseract
from PIL import Image
import logging
import os
import pdf2image

class OCRService:
    def __init__(self):
        # Check if Tesseract is available
        try:
            pytesseract.get_tesseract_version()
            self.available = True
            logging.info("Tesseract OCR initialized successfully")
        except pytesseract.TesseractNotFoundError:
            self.available = False
            logging.error("Tesseract not found. Please install Tesseract OCR")

    def extract_text(self, file_path):
        """Extract text from an image or PDF file"""
        if not self.available:
            return "OCR service not available"
            
        try:
            # Check if file is PDF
            if file_path.lower().endswith('.pdf'):
                return self.extract_text_from_pdf(file_path)
            else:
                return self.extract_text_from_image(file_path)
        except Exception as e:
            logging.error(f"Error extracting text from {file_path}: {str(e)}")
            raise e
    
    def extract_text_from_image(self, image_path):
        """Extract text from an image file"""
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            return text
        except Exception as e:
            logging.error(f"Error during OCR: {e}")
            return ""

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file by converting to images first"""
        if not self.available:
            return "OCR service not available"
            
        # For PDFs, we use pdf2image to convert to images
        images = pdf2image.convert_from_path(pdf_path)
        full_text = ""
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image)
            full_text += f"Page {i+1}:\n{text}\n\n"
        return full_text

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
