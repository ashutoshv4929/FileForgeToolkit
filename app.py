"""
This is the main entry point for the FileForgeToolkit application.
It creates and configures the Flask application instance.
"""
import os
import logging
from smart_file_converter import create_app, db

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask application using the application factory
app = create_app()

def run():
    """Run the application"""
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run()
