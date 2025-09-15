import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Application Mode
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() in ['true', '1', 'yes', 'on']
    
    # Google Calendar API
    CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.json')
    
    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = 'gemini-2.0-flash'
    
    # Scheduling Settings
    DEFAULT_TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    DEFAULT_MEETING_DURATION = timedelta(hours=1)
    BUSINESS_HOURS_START = 9  # 9 AM
    BUSINESS_HOURS_END = 17   # 5 PM
    
    # Calendar Scopes
    SCOPES = ['https://www.googleapis.com/auth/calendar']