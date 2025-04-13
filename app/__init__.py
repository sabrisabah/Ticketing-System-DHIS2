from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import os
from dotenv import load_dotenv
import logging

db = SQLAlchemy()
mail = Mail()
csrf = CSRFProtect()
login_manager = LoginManager()

def nl2br(value):
    # Convert newlines to <br> tags
    if not value:
        return value
    return value.replace('\n', '<br>\n')

def create_app():
    app = Flask(__name__)
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secure-secret-key-here')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Static file configuration
    app.static_folder = 'static'
    app.static_url_path = '/static'
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['ADMIN_EMAILS'] = [email.strip() for email in os.getenv('ADMIN_EMAILS', '').split(',') if email.strip()]
    
    # Log email configuration status
    logger = logging.getLogger(__name__)
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        logger.warning('Email credentials not configured')
    if not app.config['ADMIN_EMAILS']:
        logger.warning('No admin emails configured')
    else:
        logger.info(f"Admin emails configured: {len(app.config['ADMIN_EMAILS'])} recipients")
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register custom filters
    app.jinja_env.filters['nl2br'] = nl2br
    
    # Register blueprints
    from .routes import main
    app.register_blueprint(main)
    
    # Create database tables and initialize admin user
    with app.app_context():
        db.create_all()
        from .models import User
        User.init_admin()
    
    return app