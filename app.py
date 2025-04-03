import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
socketio = SocketIO()
login_manager = LoginManager()

def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # Set configurations
    app.config.from_object('config.Config')
    
    # Set secret key from environment variable
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    
    # Initialize extensions with app
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Configure login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from models import User, Role, Document, ChatHistory, DocumentChunk
        
        # Create database tables if they don't exist
        db.create_all()
        
        # Check if roles exist, if not create default roles
        from models import Role
        if not Role.query.first():
            admin_role = Role(name='admin', description='Administrator')
            user_role = Role(name='user', description='Regular User')
            db.session.add(admin_role)
            db.session.add(user_role)
            db.session.commit()
            logging.info("Default roles created")
        
        # Register blueprints
        from auth import auth_bp
        from chat import chat_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(chat_bp)
        
        # Register routes
        @app.route('/')
        def index():
            from flask import redirect, url_for
            return redirect(url_for('auth.login'))
            
        return app

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create app instance
app = create_app()
