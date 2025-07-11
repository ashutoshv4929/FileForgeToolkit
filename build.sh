#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r smart_file_converter/requirements.txt

# Install Tesseract OCR
apt-get update
apt-get install -y tesseract-ocr
