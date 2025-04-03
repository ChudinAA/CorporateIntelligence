import os
import eventlet
import logging
from flask import Flask, render_template, request, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Monkey patch for eventlet (required for SocketIO with eventlet)
eventlet.monkey_patch()

# Import extensions
from extensions import db, login_manager, socketio

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure app
    app.config.from_object('config.Config')
    app.secret_key = os.environ.get("SESSION_SECRET", "development-key")
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Initialize Socket.IO with CORS support
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    
    # Initialize services
    from rag_engine import RAGEngine
    from document_processor import DocumentProcessor
    from vector_store import VectorStore
    from llm_integration import LLMService
    from openai_integration import OpenAIService
    
    # Initialize services with application context
    vector_store = VectorStore(app)
    llm_service = LLMService(app)
    openai_service = OpenAIService(app)
    rag_engine = RAGEngine(app)
    document_processor = DocumentProcessor(app)
    
    # Make services available to the application context
    app.rag_engine = rag_engine
    app.document_processor = document_processor
    
    # Register blueprints
    from auth import auth_bp
    from chat import chat_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    
    # Custom Jinja2 filters
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        """Parse a JSON string into Python object."""
        import json
        return json.loads(value)
    
    # Create tables
    with app.app_context():
        # Import models here to ensure they're registered with SQLAlchemy
        import models
        db.create_all()
        
        # Create default roles if they don't exist
        from models import Role
        roles = ['user', 'admin']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                new_role = Role(name=role_name, description=f"{role_name.capitalize()} role")
                db.session.add(new_role)
        db.session.commit()
    
    # Routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    logger.info("Application with Socket.IO support via eventlet")
    return app

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

app = create_app()

if __name__ == "__main__":
    logger.info("Starting application with Socket.IO support via eventlet")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)