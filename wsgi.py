"""
WSGI config for FileForgeToolkit.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import logging
from smart_file_converter import create_app
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create application instance
application = create_app()

# Add proxy fix for reverse proxy
application.wsgi_app = ProxyFix(application.wsgi_app, x_proto=1, x_host=1)

# Set up logging
if not application.debug:
    log_dir = os.path.join(application.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Error log
    file_handler = logging.FileHandler(os.path.join(log_dir, 'error.log'))
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # Access log
    access_log = logging.FileHandler(os.path.join(log_dir, 'access.log'))
    access_log.setLevel(logging.INFO)
    access_log.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # Add handlers
    application.logger.addHandler(file_handler)
    application.logger.addHandler(access_log)
    
    application.logger.setLevel(logging.INFO)
    logger.info('FileForgeToolkit startup in production mode')

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)
