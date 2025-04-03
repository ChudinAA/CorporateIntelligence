from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for user-role relationship
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """User model for authentication and storing user information."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))
    documents = db.relationship('Document', backref='owner', lazy='dynamic')
    chat_histories = db.relationship('ChatHistory', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Set user password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches."""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """Check if user has specified role."""
        return any(role.name == role_name for role in self.roles)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Role(db.Model):
    """Role model for RBAC."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Document(db.Model):
    """Document model for storing uploaded files metadata."""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    processing_error = db.Column(db.Text, nullable=True)
    
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
    """Model for storing chat history."""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    summary = db.Column(db.Text, nullable=True)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='chat_history', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatHistory {self.id} for User {self.user_id}>'

class ChatMessage(db.Model):
    """Model for storing individual chat messages."""
    id = db.Column(db.Integer, primary_key=True)
    chat_history_id = db.Column(db.Integer, db.ForeignKey('chat_history.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True if sent by user, False if by AI
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Additional metadata
    related_documents = db.Column(db.Text, nullable=True)  # JSON string of document IDs used for response
    
    def __repr__(self):
        sender = "User" if self.is_user else "AI"
        return f'<ChatMessage {self.id} from {sender}>'
