
from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """User model for authentication."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    documents = db.relationship('Document', backref='owner', lazy='dynamic')
    chat_histories = db.relationship('ChatHistory', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Set user password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Document(db.Model):
    """Document model for storing uploaded files metadata."""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    processing_error = db.Column(db.String(255), nullable=True)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    chunks = db.relationship('DocumentChunk', backref='document', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Document {self.original_filename}>'

class DocumentChunk(db.Model):
    """Model for storing document chunks for vector database indexing."""
    id = db.Column(db.Integer, primary_key=True)
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    vector_id = db.Column(db.String(100), nullable=True)  # ID in vector database

    # Foreign keys
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)

    def __repr__(self):
        return f'<DocumentChunk {self.id} from Document {self.document_id}>'

class ChatHistory(db.Model):
    """Model for storing chat sessions."""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    summary = db.Column(db.Text, nullable=True)

    # Relationships
    messages = db.relationship('ChatMessage', backref='chat_history', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ChatHistory {self.session_id}>'

class ChatMessage(db.Model):
    """Model for storing chat messages."""
    id = db.Column(db.Integer, primary_key=True)
    chat_history_id = db.Column(db.Integer, db.ForeignKey('chat_history.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    related_documents = db.Column(db.Text, nullable=True)  # JSON string of related document IDs

    def __repr__(self):
        return f'<ChatMessage {self.id}>'
