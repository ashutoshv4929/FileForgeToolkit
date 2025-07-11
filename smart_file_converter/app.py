from smart_file_converter import create_app

app = create_app()

if __name__ == "__main__":
    app.run()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Local development
    from routes import *
    app.run()
else:
    # Production (Gunicorn)
    from .routes import *
    application = app