"""
Settings manager for chatbot configuration.
Stores settings in SQLite for easy runtime updates.
"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()


class ChatSettings(Base):
    __tablename__ = "chat_settings"

    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(Text, nullable=False)
    setting_type = Column(String(50), nullable=False)  # string, number, boolean, json
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SettingsManager:
    """Manages chatbot settings with database persistence."""

    DEFAULT_SETTINGS = {
        # OpenAI Configuration
        "openai_api_key": {
            "value": "",
            "type": "string",
            "description": "OpenAI API key for ChatGPT integration"
        },
        "openai_model": {
            "value": "gpt-4-turbo-preview",
            "type": "string",
            "description": "OpenAI model to use (gpt-4-turbo-preview, gpt-3.5-turbo, etc.)"
        },
        "temperature": {
            "value": 0.7,
            "type": "number",
            "description": "Response creativity (0.0-2.0). Lower = more focused, Higher = more creative"
        },
        "max_tokens": {
            "value": 1000,
            "type": "number",
            "description": "Maximum response length in tokens"
        },
        "openai_prompt_id": {
            "value": "",
            "type": "string",
            "description": "OpenAI Prompt ID for using custom prompts"
        },
        "openai_prompt_version": {
            "value": "2",
            "type": "string",
            "description": "OpenAI Prompt version"
        },

        # Chat Behavior
        "enable_rag": {
            "value": True,
            "type": "boolean",
            "description": "Enable RAG (Retrieval-Augmented Generation) for document search"
        },
        "rag_chunk_limit": {
            "value": 3,
            "type": "number",
            "description": "Number of document chunks to retrieve for context"
        },
        "enable_citations": {
            "value": True,
            "type": "boolean",
            "description": "Show citations in responses"
        },

        # System Prompt
        "system_prompt": {
            "value": """You are a retirement planning assistant for Fiat Wealth Management. Your goal is to provide clear, concise, educational information.

RESPONSE STYLE:
- Keep answers SHORT and direct (2-3 sentences for simple concepts)
- Answer the specific question asked without extra fluff
- End with a simple follow-up question offering to go deeper (e.g., "Want me to explain X in more detail?" or "Would you like to discuss Y?")
- NO lengthy frameworks, NO structured sections, NO checklists unless specifically requested
- Write conversationally, like you're chatting with someone

GUARDRAILS:
- Provide educational information only, not personalized advice
- Never recommend specific buy/sell/hold actions or exact dollar amounts
- If they ask "what should I do," explain general factors to consider and suggest they discuss specifics with an advisor
- Keep it brief - users can always ask for more detail

TONE:
- Friendly and conversational, like a knowledgeable friend
- Plain language, no jargon
- Helpful without being overwhelming""",
            "type": "string",
            "description": "System prompt that guides the AI's behavior"
        },

        # Lead Capture
        "enable_lead_gate": {
            "value": False,
            "type": "boolean",
            "description": "Require contact info after first message"
        },
        "lead_gate_message": {
            "value": "Before we keep going, where should we send your summary and how can we reach you?",
            "type": "string",
            "description": "Message shown when requesting contact info"
        },

        # UI Customization
        "chat_title": {
            "value": "Fiat Clarity Chat",
            "type": "string",
            "description": "Title shown in chat header"
        },
        "chat_subtitle": {
            "value": "Retirement planning guidance",
            "type": "string",
            "description": "Subtitle shown in chat header"
        },
        "welcome_message": {
            "value": "Hello! I'm here to help you navigate retirement planning with clarity and confidence. Whether you're curious about Roth conversions, Social Security timing, tax strategies, or building sustainable retirement income, I'm here to guide you.\n\nWhat questions do you have about your retirement journey?",
            "type": "string",
            "description": "Initial greeting message"
        },
        "schedule_button_text": {
            "value": "Schedule a Clarity Call",
            "type": "string",
            "description": "Text for the scheduling button"
        },
    }

    def __init__(self, db: Session):
        self.db = db

    def get_setting(self, key: str, default=None):
        """Get a setting value by key."""
        try:
            setting = self.db.query(ChatSettings).filter(
                ChatSettings.setting_key == key
            ).first()

            if not setting:
                # Return default from DEFAULT_SETTINGS
                if key in self.DEFAULT_SETTINGS:
                    return self.DEFAULT_SETTINGS[key]["value"]
                return default

            # Parse value based on type
            if setting.setting_type == "boolean":
                return setting.setting_value.lower() == "true"
            elif setting.setting_type == "number":
                return float(setting.setting_value)
            elif setting.setting_type == "json":
                return json.loads(setting.setting_value)
            else:
                return setting.setting_value
        except Exception as e:
            print(f"⚠ Settings query error for '{key}': {e}")
            self.db.rollback()  # Rollback failed transaction
            # Return default
            if key in self.DEFAULT_SETTINGS:
                return self.DEFAULT_SETTINGS[key]["value"]
            return default

    def set_setting(self, key: str, value, setting_type: str = None, description: str = None):
        """Set a setting value."""
        setting = self.db.query(ChatSettings).filter(
            ChatSettings.setting_key == key
        ).first()

        # Convert value to string for storage
        if isinstance(value, bool):
            str_value = "true" if value else "false"
            setting_type = setting_type or "boolean"
        elif isinstance(value, (int, float)):
            str_value = str(value)
            setting_type = setting_type or "number"
        elif isinstance(value, (dict, list)):
            str_value = json.dumps(value)
            setting_type = setting_type or "json"
        else:
            str_value = str(value)
            setting_type = setting_type or "string"

        if setting:
            setting.setting_value = str_value
            setting.setting_type = setting_type
            if description:
                setting.description = description
            setting.updated_at = datetime.utcnow()
        else:
            setting = ChatSettings(
                setting_key=key,
                setting_value=str_value,
                setting_type=setting_type,
                description=description or self.DEFAULT_SETTINGS.get(key, {}).get("description", "")
            )
            self.db.add(setting)

        self.db.commit()
        return setting

    def get_all_settings(self):
        """Get all settings as a dictionary."""
        settings = {}
        db_settings = self.db.query(ChatSettings).all()

        # Start with defaults
        for key, config in self.DEFAULT_SETTINGS.items():
            settings[key] = {
                "value": config["value"],
                "type": config["type"],
                "description": config["description"]
            }

        # Override with database values
        for setting in db_settings:
            value = setting.setting_value
            if setting.setting_type == "boolean":
                value = value.lower() == "true"
            elif setting.setting_type == "number":
                value = float(value)
            elif setting.setting_type == "json":
                value = json.loads(value)

            settings[setting.setting_key] = {
                "value": value,
                "type": setting.setting_type,
                "description": setting.description
            }

        return settings

    def initialize_defaults(self):
        """Initialize default settings if they don't exist."""
        for key, config in self.DEFAULT_SETTINGS.items():
            existing = self.db.query(ChatSettings).filter(
                ChatSettings.setting_key == key
            ).first()

            if not existing:
                self.set_setting(
                    key,
                    config["value"],
                    config["type"],
                    config["description"]
                )

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        for key, config in self.DEFAULT_SETTINGS.items():
            self.set_setting(
                key,
                config["value"],
                config["type"],
                config["description"]
            )


# Initialize settings table
def init_settings_table(database_url: str):
    """Initialize the settings table."""
    engine = create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        settings_mgr = SettingsManager(db)
        settings_mgr.initialize_defaults()
        print("✓ Settings initialized")
    finally:
        db.close()
