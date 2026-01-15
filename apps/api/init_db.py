"""
Database initialization script.
Run this to create tables and enable pgvector extension.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base
from settings_manager import init_settings_table
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fiat:fiat123@localhost:5432/fiat_clarity")

def init_database():
    """Initialize database with pgvector extension and create all tables."""
    engine = create_engine(DATABASE_URL)

    # Enable pgvector extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("✓ pgvector extension enabled")

    # Drop all existing tables and recreate (fresh start)
    print("⚠ Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ Old tables dropped")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created")

    # Alter chunks table to use vector type for embedding
    with engine.connect() as conn:
        # Check if column exists and needs alteration
        result = conn.execute(text("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'chunks' AND column_name = 'embedding'
        """))
        current_type = result.scalar()

        if current_type and current_type != 'USER-DEFINED':
            conn.execute(text("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector"))
            conn.commit()
            print("✓ Chunks.embedding column set to vector(1536)")
        elif not current_type:
            conn.execute(text("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding vector(1536)"))
            conn.commit()
            print("✓ Chunks.embedding column added as vector(1536)")
        else:
            print("✓ Chunks.embedding column already configured")

    # Initialize settings table
    print("Initializing settings table...")
    try:
        init_settings_table(DATABASE_URL)
        print("✓ Settings table initialized")
    except Exception as e:
        print(f"⚠ Settings initialization warning: {e}")

    print("\n✅ Database initialization complete!")
    print(f"   Connected to: {DATABASE_URL}")

if __name__ == "__main__":
    init_database()
