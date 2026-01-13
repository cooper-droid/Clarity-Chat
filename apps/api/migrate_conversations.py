"""
Migration script to add user_id and title columns to conversations table
"""
import sqlite3
import os

DATABASE_PATH = os.getenv("DATABASE_URL", "sqlite:///./fiat_clarity.db").replace("sqlite:///", "")

def migrate():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add user_id column if it doesn't exist
        if 'user_id' not in columns:
            print("Adding user_id column...")
            cursor.execute("ALTER TABLE conversations ADD COLUMN user_id VARCHAR(100)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations(user_id)")
            print("✓ Added user_id column")
        else:
            print("✓ user_id column already exists")

        # Add title column if it doesn't exist
        if 'title' not in columns:
            print("Adding title column...")
            cursor.execute("ALTER TABLE conversations ADD COLUMN title VARCHAR(500)")
            print("✓ Added title column")
        else:
            print("✓ title column already exists")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
