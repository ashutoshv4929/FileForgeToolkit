import os
from backend import create_app, db
from backend.models import User, Conversion, ExtractedText
from backend.routes import init_services

# Create the Flask application
app = create_app()

# Initialize services
init_services(app)

# Create database tables and admin user
with app.app_context():
    # Create database tables
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
