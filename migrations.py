
from app import db

def migrate_database():
    """Remove unused tables and columns."""
    try:
        # Drop unused tables
        db.engine.execute('DROP TABLE IF EXISTS roles_users CASCADE')
        db.engine.execute('DROP TABLE IF EXISTS role CASCADE')
        db.engine.execute('DROP TABLE IF EXISTS chat_history CASCADE')
        db.engine.execute('DROP TABLE IF EXISTS chat_message CASCADE')
        
        # Create new tables if they don't exist
        with db.engine.connect() as conn:
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS document (
                    id INTEGER PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """))
            
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
        
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Migration error: {str(e)}")
        raise

if __name__ == '__main__':
    migrate_database()
