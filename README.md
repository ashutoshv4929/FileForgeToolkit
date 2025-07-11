# FileForgeToolkit

A web application for file conversion and OCR (Optical Character Recognition) built with Flask and Tesseract OCR.

## Features

- Upload and convert various file formats
- Extract text from images and PDFs using Tesseract OCR
- User authentication and file management
- RESTful API for integration with other services

## Prerequisites

- Python 3.9+
- Tesseract OCR
- Poppler-utils (for PDF processing)
- PostgreSQL (for production)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/FileForgeToolkit.git
   cd FileForgeToolkit
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

## Running the Application

### Development

```bash
flask run
```

### Production with Gunicorn

```bash
gunicorn --bind 0.0.0.0:5000 wsgi:application
```

### Using Docker

```bash
# Build and start containers
docker-compose up --build

# Run database migrations
docker-compose exec web flask db upgrade
```

## API Endpoints

- `POST /api/upload` - Upload a file for processing
- `GET /api/files` - List all uploaded files
- `GET /api/files/<file_id>` - Get file details
- `POST /api/ocr` - Extract text from an image or PDF

## Deployment

### Render.com

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following environment variables:
   - `FLASK_APP=wsgi.py`
   - `FLASK_ENV=production`
   - `SECRET_KEY` (generate a secure secret key)
   - `DATABASE_URL` (your PostgreSQL connection string)
   - `TESSERACT_CMD=/usr/bin/tesseract`

### Heroku

```bash
# Login to Heroku CLI
heroku login

# Create a new Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set FLASK_APP=wsgi.py
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key

# Deploy to Heroku
git push heroku main

# Run database migrations
heroku run flask db upgrade
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

MIT
