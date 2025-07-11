"""
WSGI config for FileForgeToolkit.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from smart_file_converter import create_app, db
from smart_file_converter.models import User, ConversionHistory, ExtractedText, AppSettings

# Create application instance
app = create_app()

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# This is used by the production server
application = app

if __name__ == "__main__":
    # Run the development server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
