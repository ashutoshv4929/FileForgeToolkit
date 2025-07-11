import pytesseract
from PIL import Image
import logging
import os
import pdf2image
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class OCRService:
    """Service for performing OCR on images and PDFs"""
    
    def __init__(self, tesseract_cmd=None):
        """Initialize the OCR service with optional Tesseract command path"""
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            pytesseract.pytesseract.tesseract_cmd = shutil.which('tesseract') or '/usr/bin/tesseract'
        
        # Check if Tesseract is available
        try:
            # Test Tesseract availability
            pytesseract.get_tesseract_version()
            self.available = True
            logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            self.available = False
            logger.error(f"Tesseract initialization error: {str(e)}")

    def extract_text(self, file_path):
        """
        Extract text from an image or PDF file
        
        Args:
            file_path (str): Path to the input file
            
        Returns:
            str: Extracted text or None if extraction fails
        """
        if not self.available:
            return "OCR service not available"
            
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
                
            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Handle PDF files
            if ext == '.pdf':
                return self._extract_from_pdf(file_path)
                
            # Handle image files
            elif ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'):
                return self._extract_from_image(file_path)
                
            else:
                logger.error(f"Unsupported file format: {ext}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return None
    
    def _extract_from_image(self, image_path):
        """Extract text from an image file"""
        try:
            with Image.open(image_path) as img:
                return pytesseract.image_to_string(img)
        except Exception as e:
            logger.error(f"Error extracting from image {image_path}: {str(e)}")
            return None
    
    def _extract_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            # Extract text from each page
            text = ""
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                text += f"\n--- Page {i+1} ---\n{page_text}"
                
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting from PDF {pdf_path}: {str(e)}")
            return None

    def extract_text_from_image(self, image_path):
        """Extract text from an image file"""
        try:
            return pytesseract.image_to_string(Image.open(image_path))
        except Exception as e:
            logger.error(f"Error during OCR: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        if not self.available:
            return "OCR service not available"
            
        # For PDFs, we use pdf2image to convert to images
        images = convert_from_path(pdf_path)
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
