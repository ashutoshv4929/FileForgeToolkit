import os
import shutil
import logging
from pathlib import Path

class LocalStorageService:
    def __init__(self, storage_dir='uploads'):
        """
        Initialize local storage service.
        
        Args:
            storage_dir (str): Directory to store uploaded files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Local storage initialized at: {self.storage_dir.absolute()}")
    
    def upload_file(self, file_stream, destination_path):
        """
        Upload a file to local storage.
        
        Args:
            file_stream: File-like object to upload
            destination_path (str): Path where the file should be stored
            
        Returns:
            str: Path to the stored file
        """
        destination = self.storage_dir / destination_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        with open(destination, 'wb') as f:
            if hasattr(file_stream, 'read'):
                file_stream.seek(0)
                shutil.copyfileobj(file_stream, f)
            else:
                f.write(file_stream)
        
        return str(destination)
    
    def download_file(self, source_path):
        """
        Download a file from local storage.
        
        Args:
            source_path (str): Path to the file to download
            
        Returns:
            str: Path to the downloaded file
        """
        source = self.storage_dir / source_path
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")
        return str(source)
    
    def delete_file(self, file_path):
        """
        Delete a file from local storage.
        
        Args:
            file_path (str): Path to the file to delete
        """
        target = self.storage_dir / file_path
        if target.exists():
            target.unlink()
    
    def get_file_url(self, file_path):
        """
        Get a URL to access the file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: URL to access the file
        """
        return f"/uploads/{file_path}"  # This will be handled by Flask's static file serving
    
    def file_exists(self, file_path):
        """
        Check if a file exists in storage.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            bool: True if the file exists, False otherwise
        """
        return (self.storage_dir / file_path).exists()


class CloudStorageService:
    def __init__(self, storage_dir='cloud_uploads'):
        """
        Initialize cloud storage service.
        For now, this is a placeholder that uses local storage.
        
        Args:
            storage_dir (str): Directory to store uploaded files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Cloud storage initialized at: {self.storage_dir.absolute()}")
    
    def upload_file(self, file_stream, destination_path):
        """
        Upload a file to cloud storage.
        
        Args:
            file_stream: File-like object to upload
            destination_path (str): Path where the file should be stored
            
        Returns:
            str: Path to the stored file
        """
        destination = self.storage_dir / destination_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        with open(destination, 'wb') as f:
            if hasattr(file_stream, 'read'):
                file_stream.seek(0)
                shutil.copyfileobj(file_stream, f)
            else:
                f.write(file_stream)
        
        return str(destination)
    
    def download_file(self, source_path):
        """
        Download a file from cloud storage.
        
        Args:
            source_path (str): Path to the file to download
            
        Returns:
            str: Path to the downloaded file
        """
        source = self.storage_dir / source_path
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")
        return str(source)
    
    def delete_file(self, file_path):
        """
        Delete a file from cloud storage.
        
        Args:
            file_path (str): Path to the file to delete
        """
        target = self.storage_dir / file_path
        if target.exists():
            target.unlink()
    
    def get_file_url(self, file_path):
        """
        Get a URL to access the file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: URL to access the file
        """
        return f"/cloud_uploads/{file_path}"
    
    def file_exists(self, file_path):
        """
        Check if a file exists in cloud storage.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            bool: True if the file exists, False otherwise
        """
        return (self.storage_dir / file_path).exists()
    
    def list_files(self, prefix=""):
        """
        List files in cloud storage.
        
        Args:
            prefix (str): Optional prefix to filter files
            
        Returns:
            list: List of file paths
        """
        files = []
        search_dir = self.storage_dir / prefix if prefix else self.storage_dir
        
        if search_dir.exists():
            for file_path in search_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.storage_dir)
                    files.append(str(relative_path))
        
        return files
