#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Install system dependencies
echo "Installing system dependencies..."
apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    python3-pip \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation
if ! command -v tesseract &> /dev/null; then
    echo "Error: Tesseract OCR is not installed properly"
    exit 1
fi

echo "Tesseract version: $(tesseract --version | head -n 1)"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r smart_file_converter/requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p /app/logs
mkdir -p /app/uploads

# Set permissions
echo "Setting permissions..."
chmod -R a+rwx /app/logs
chmod -R a+rwx /app/uploads

echo "Build completed successfully!"
