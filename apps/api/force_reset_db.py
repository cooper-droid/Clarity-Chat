"""
Force reset database - drops all tables and recreates them.
Run this manually if preDeployCommand doesn't work.
"""
import os
import sys
from sqlalchemy import create_engine, text
from models import Base

# Get database URL from environment or command line
DATABASE_URL = os.getenv("DATABASE_URL")
if len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

if not DATABASE_URL:
    print("ERROR: No DATABASE_URL provided")
    print("Usage: python force_reset_db.py <DATABASE_URL>")
    sys.exit(1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

try:
    # Drop ALL tables
    print("🔥 DROPPING ALL TABLES...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")

    # Recreate all tables with new schema
    print("🔨 Creating tables with new schema...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created with extra_data columns")

    # Enable pgvector and configure embedding column
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("✅ pgvector extension enabled")

        # Alter chunks table
        try:
            conn.execute(text("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector"))
            conn.commit()
            print("✅ Chunks.embedding configured as vector(1536)")
        except Exception as e:
            if "does not exist" not in str(e):
                print(f"⚠️  Chunks table alteration: {e}")

    print("\n✅✅✅ DATABASE RESET COMPLETE! ✅✅✅")
    print("The application should now work correctly.")

except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
