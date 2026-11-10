import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "smart-people-analytics-secret-key-default")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.getenv("PORT", 5000))
    
    # Instance and Database
    INSTANCE_DIR = BASE_DIR / "instance"
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(INSTANCE_DIR / "people_analytics.db"))
    
    # AI Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "builtin") # builtin, gemini, openai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
