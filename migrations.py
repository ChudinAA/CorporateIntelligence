
from app import db

def migrate_database():
    """Remove unused tables and columns."""
    # Drop unused tables
    db.engine.execute('DROP TABLE IF EXISTS user_roles CASCADE')
    db.engine.execute('DROP TABLE IF EXISTS role CASCADE')
    db.engine.execute('DROP TABLE IF EXISTS chat_history CASCADE')
    db.engine.execute('DROP TABLE IF EXISTS chat_message CASCADE')
    
    # Remove unused columns from Document table
    db.engine.execute('ALTER TABLE document DROP COLUMN IF EXISTS processing_error')

if __name__ == '__main__':
    migrate_database()
