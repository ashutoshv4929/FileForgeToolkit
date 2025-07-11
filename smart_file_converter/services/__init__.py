from .local_storage import LocalStorageService
from .ocr_service import OCRService

# Initialize services
ocr_service = OCRService()
storage_service = LocalStorageService('uploads')