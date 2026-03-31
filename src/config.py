import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- PATH CONFIGURATION ---
SRC_DIR = Path(__file__).parent
PROJECT_ROOT = SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for d in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# --- APP CONFIGURATION ---
DATABASE_PATH = RAW_DATA_DIR / "marketing_intelligence.db"
HTTP_TIMEOUT = 30
LLM_TIMEOUT = 600
MAX_RETRIES = 3

# --- LOGGING CONFIGURATION ---
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
LOG_FILE = LOGS_DIR / "system.log"

def setup_logging(name: str = "ai_marketing"):
    """Centralized logging setup for both console and file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(fh)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(ch)
        
    return logger

# --- VALIDATION ---
def validate_config():
    """Validates that critical environment variables and files exist."""
    logger = setup_logging("config_validator")
    
    missing_keys = []
    # Check for primary LLM keys
    if not (os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY") or os.getenv("OPENROUTER_API_KEY")):
        missing_keys.append("NVIDIA_NIM_API_KEY or OPENROUTER_API_KEY")
    
    if missing_keys:
        logger.error(f"CRITICAL ERROR: Missing environment variables: {', '.join(missing_keys)}")
        logger.error("Please check your .env file.")
        sys.exit(1)
        
    if not DATABASE_PATH.exists():
        logger.error(f"CRITICAL ERROR: Database not found at {DATABASE_PATH}")
        logger.error("Please run 'python src/init_db.py' to initialize the database.")
        sys.exit(1)
        
    logger.info("Configuration validated successfully.")

# Initialize a default logger for the module
logger = setup_logging()
