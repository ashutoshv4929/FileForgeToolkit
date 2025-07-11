"""
WSGI config for FileForgeToolkit.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from smart_file_converter import create_app

# Create application instance
application = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)
