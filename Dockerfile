# Use the official Python 3.9 image as a base image
FROM python:3.9.18-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    FLASK_APP=smart_file_converter.app \
    FLASK_ENV=production \
    TESSERACT_CMD=/usr/bin/tesseract \
    UPLOAD_FOLDER=/app/uploads \
    MAX_CONTENT_LENGTH=16777216

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    python3-dev \
    build-essential \
    gcc \
    g++ \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs \
    && mkdir -p /app/uploads \
    && chmod -R a+rwx /app/logs \
    && chmod -R a+rwx /app/uploads \
    && if [ -f "/app/build.sh" ]; then chmod +x /app/build.sh && ./build.sh; fi

# Expose the port the app runs on
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "4", "--timeout", "120", "smart_file_converter.app:app"]
