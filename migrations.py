
from app import db

def migrate_database():
    """Create or update database schema."""
    try:
        # Create tables if they don't exist
        with db.engine.connect() as conn:
            # Create user table
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create document table
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS document (
                    id INTEGER PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    processing_error VARCHAR(255),
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """))
            
            # Create document_chunk table
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS document_chunk (
                    id INTEGER PRIMARY KEY,
                    chunk_text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    vector_id VARCHAR(100),
                    document_id INTEGER NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES document (id)
                )
            """))
            
            # Create chat_history table
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY,
                    session_id VARCHAR(36) UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    summary TEXT,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """))
            
            # Create chat_message table
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS chat_message (
                    id INTEGER PRIMARY KEY,
                    chat_history_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_user BOOLEAN DEFAULT TRUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    related_documents TEXT,
                    FOREIGN KEY (chat_history_id) REFERENCES chat_history (id)
                )
            """))
            
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Migration error: {str(e)}")
        raise

if __name__ == '__main__':
    migrate_database()
