import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Qwen AI Configuration
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")

# Venue Configuration
VENUE_BASE_URL = os.getenv("VENUE_BASE_URL", "https://vbs.sports.taipei/venues/?K=352")
VENUE_ID = os.getenv("VENUE_ID", "352")

# Request Configuration
REQUEST_DELAY_MIN = float(os.getenv("REQUEST_DELAY_MIN", 2))
REQUEST_DELAY_MAX = float(os.getenv("REQUEST_DELAY_MAX", 5))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 15))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Validation
def validate_config():
    """Validate required configuration"""
    required = ["TELEGRAM_BOT_TOKEN", "DASHSCOPE_API_KEY"]
    missing = [key for key in required if not os.getenv(key)]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True
