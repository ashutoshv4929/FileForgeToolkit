from PIL import Image
import logging
import os
import tesserocr
import io
import pdf2image
from pathlib import Path

class OCRService:
    def __init__(self):
        # Check if Tesseract is available
        try:
            # Test Tesseract availability by creating a simple API instance
            with tesserocr.PyTessBaseAPI() as api:
                self.available = True
                logging.info("Tesseract OCR initialized successfully")
        except Exception as e:
            self.available = False
            logging.error(f"Tesseract initialization error: {str(e)}")

    def extract_text(self, file_path):
        """Extract text from an image or PDF file"""
        if not self.available:
            raise RuntimeError("Tesseract OCR is not available")
        if not self.available:
            return "OCR service not available"
            
        try:
            # Handle PDF files
            if file_path.lower().endswith('.pdf'):
                images = pdf2image.convert_from_path(file_path)
                text = ''
                with tesserocr.PyTessBaseAPI() as api:
                    for i, image in enumerate(images):
                        # Convert PIL image to bytes
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        # Set image and get text
                        api.SetImageBytes(img_byte_arr, image.width, image.height, 4, 4 * image.width)
                        page_text = api.GetUTF8Text()
                        text += f"\n--- Page {i+1} ---\n{page_text}"
                return text.strip()
            
            # Handle image files
            else:
                with tesserocr.PyTessBaseAPI() as api:
                    image = Image.open(file_path)
                    api.SetImage(image)
                    return api.GetUTF8Text()
                
        except Exception as e:
            logging.error(f"Error extracting text: {str(e)}")
            raise RuntimeError(f"Failed to extract text: {str(e)}")

    def extract_text_from_image(self, image_path):
        """Extract text from an image file"""
        try:
            with tesserocr.PyTessBaseAPI() as api:
                image = Image.open(image_path)
                api.SetImage(image)
                return api.GetUTF8Text()
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
        with tesserocr.PyTessBaseAPI() as api:
            for i, image in enumerate(images):
                # Convert PIL image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Set image and get text
                api.SetImageBytes(img_byte_arr, image.width, image.height, 4, 4 * image.width)
                page_text = api.GetUTF8Text()
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
