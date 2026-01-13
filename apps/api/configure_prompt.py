"""
Configure OpenAI Prompt ID settings in the database.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from settings_manager import SettingsManager, init_settings_table

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fiat_clarity.db")

# Initialize settings table if needed
init_settings_table(DATABASE_URL)

# Create database session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    settings_mgr = SettingsManager(db)

    # Configure the OpenAI Prompt ID
    settings_mgr.set_setting(
        "openai_prompt_id",
        "pmpt_6962e013d6d88196b1c3834baa00e88500912c21d3085185",
        "string",
        "OpenAI Prompt ID for using custom prompts"
    )

    # Configure the prompt version
    settings_mgr.set_setting(
        "openai_prompt_version",
        "20",
        "string",
        "OpenAI Prompt version"
    )

    print("✓ OpenAI Prompt ID configured successfully!")
    print(f"  Prompt ID: pmpt_6962e013d6d88196b1c3834baa00e88500912c21d3085185")
    print(f"  Prompt Version: 20")

    # Verify settings
    prompt_id = settings_mgr.get_setting("openai_prompt_id")
    prompt_version = settings_mgr.get_setting("openai_prompt_version")
    print(f"\n✓ Verified settings:")
    print(f"  openai_prompt_id: {prompt_id}")
    print(f"  openai_prompt_version: {prompt_version}")

finally:
    db.close()
