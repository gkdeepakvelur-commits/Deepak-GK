import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    # Create the app
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configure database - Use PostgreSQL from environment or fallback to SQLite
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        # Fix for newer SQLAlchemy versions
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///students.db"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Upload configuration
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
    
    # Initialize extensions
    db.init_app(app)
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.app_context():
        # Import models to ensure tables are created
        import models
        
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        from models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('password123')
            db.session.add(admin)
            
            # Create additional admin user
            kkcadmin = User(username='kkcadmin', email='kkcadmin@example.com', role='admin')
            kkcadmin.set_password('kkcedu12345')
            db.session.add(kkcadmin)
            
            db.session.commit()
            logging.info("Default admin users created")
    
    # Add template context processor for global variables
    @app.context_processor
    def inject_global_vars():
        now = datetime.now()
        return {
            'current_year': now.year,
            'error_timestamp': now.strftime('%Y%m%d%H%M%S'),
            'error_datetime': now.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # Register routes
    from routes import register_routes
    register_routes(app)
    
    return app

app = create_app()
