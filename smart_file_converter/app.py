from smart_file_converter import create_app, db
import os

# Create application instance
app = create_app()

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])

if __name__ == '__main__':
    # Local development
    from routes import *
    app.run()
else:
    # Production (Gunicorn)
    from .routes import *
    application = app