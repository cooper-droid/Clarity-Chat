"""
Database initialization script for SQLite (no Docker needed).
"""
import os
from sqlalchemy import create_engine
from models_sqlite import Base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fiat_clarity.db")

def init_database():
    """Initialize SQLite database and create all tables."""
    print("Initializing SQLite database...")
    engine = create_engine(DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created")

    print("\n✅ Database initialization complete!")
    print(f"   Database: {DATABASE_URL}")
    print("   Note: Using SQLite (keyword search only, no vector embeddings)")

if __name__ == "__main__":
    init_database()
