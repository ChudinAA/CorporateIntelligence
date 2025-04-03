import os

class Config:
    """App configuration class."""
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # File upload configuration
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
    
    # Chat configuration
    MAX_CHAT_HISTORY = 50  # Maximum number of messages to store per chat
    
    # Vector database configuration
    VECTOR_DB_PATH = "vector_db"
    EMBEDDINGS_DIMENSION = 384  # Default for most models
    
    # LLM configuration
    LLM_MODEL_PATH = os.environ.get("LLM_MODEL_PATH", "models/llama3.1-8b")
    
    # Security configuration
    WTF_CSRF_ENABLED = True
    
    # Allowed file extensions for document upload
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'xlsx', 'csv'}
