# Apply eventlet monkey patching before any other imports
import eventlet
eventlet.monkey_patch()

import os
import json
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("Initializing application with eventlet support")

# Import extensions
from extensions import db, login_manager, socketio

def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # Set configurations
    app.config.from_object('config.Config')
    
    # Set secret key from environment variable
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    
    # Register custom Jinja2 filters
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        """Parse a JSON string into Python object."""
        try:
            return json.loads(value) if value else []
        except (ValueError, TypeError):
            return []
    
    # Initialize extensions with app
    db.init_app(app)
    # Use eventlet for WebSocket support
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet', manage_session=False)
    logger.info("Socket.IO initialized with eventlet mode")
    
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
