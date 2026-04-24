import json
import logging
import os
import sys
from copy import deepcopy
from pathlib import Path

from dotenv import load_dotenv

# --- PATH CONFIGURATION ---
SRC_DIR = Path(__file__).parent
PROJECT_ROOT = SRC_DIR.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for directory in [CONFIG_DIR, DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# --- APP CONFIGURATION ---
DATABASE_PATH = RAW_DATA_DIR / "marketing_intelligence.db"
HTTP_TIMEOUT = 30
LLM_TIMEOUT = 600
MAX_RETRIES = 3
PIPELINE_CONFIG_PATH = CONFIG_DIR / "pipeline.json"

DEFAULT_PIPELINE_SETTINGS = {
    "pipeline": {
        "market_topic": "Xu huong smartphone 2026 va thi truong AI Phone",
        "report_prefix": "Smartphone_Strategic_Report",
        "feedback_signal_limit": 5,
        "feedback_lookback_days": 30,
        "signal_recent_window_minutes": 10,
    },
    "analysis": {
        "allowed_regions": ["North", "South", "Central", "Highlands"],
        "reference_roi_data": (
            "TikTok=1383.21 (budget 235tr), Instagram=995.0 (budget 28tr), "
            "Facebook=980.42 (budget 166tr), KOL=951.66, "
            "YouTube=333.57 (budget 461tr), Google Search=332.98 (budget 468tr)"
        ),
    },
    "llm": {
        "temperature": 0.3,
        "max_tokens": 4096,
        "timeout": LLM_TIMEOUT,
        "primary": {
            "name": "Llama 3.3 70B",
            "provider": "NVIDIA NIM",
            "model_id": "nvidia_nim/meta/llama-3.3-70b-instruct",
            "parameters": "70B",
            "context_window": "128K",
            "env_keys": ["NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY"],
        },
        "backup": {
            "name": "Llama 3.3 70B",
            "provider": "OpenRouter",
            "model_id": "openrouter/meta-llama/llama-3.3-70b-instruct:free",
            "parameters": "70B",
            "context_window": "128K",
            "env_keys": ["OPENROUTER_API_KEY"],
        },
    },
    "dashboard": {
        "social_post_limit": 5,
        "orchestrator": {"name": "CrewAI", "version": "0.1"},
        "agents": [
            {"role": "Intelligence Lead", "tools": ["search_internet", "query_marketing_db"]},
            {"role": "Creative Director", "tools": ["query_marketing_db"]},
            {"role": "Brand Strategist", "tools": ["read_marketing_content"]},
            {"role": "Chief Strategy Officer (CSO)", "tools": ["query_marketing_db", "save_report", "create_sales_chart", "signal_update"]},
        ],
        "tools": [
            {"name": "search_internet", "type": "Web", "desc": "Tim kiem xu huong thi truong"},
            {"name": "query_marketing_db", "type": "SQL", "desc": "Truy xuat du lieu read-only tu SQLite"},
            {"name": "read_marketing_content", "type": "Content", "desc": "Doc tai lieu marketing noi bo"},
            {"name": "save_report", "type": "Output", "desc": "Luu bao cao Markdown"},
            {"name": "create_sales_chart", "type": "Chart", "desc": "Ve bieu do tu du lieu JSON"},
            {"name": "signal_update", "type": "Learning", "desc": "Luu bai hoc chien luoc cho chu ky sau"},
        ],
    },
}

# --- LOGGING CONFIGURATION ---
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
LOG_FILE = LOGS_DIR / "system.log"


def setup_logging(name: str = "ai_marketing"):
    """Centralized logging setup for both console and file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)

    return logger


def _merge_settings(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_settings(base[key], value)
        else:
            base[key] = value
    return base


def load_pipeline_settings(config_path: str | Path | None = None) -> dict:
    """Load runtime configuration with a file-based override and safe defaults."""
    logger = logging.getLogger("config_loader")
    settings = deepcopy(DEFAULT_PIPELINE_SETTINGS)
    path = Path(config_path) if config_path else PIPELINE_CONFIG_PATH

    if path.exists():
        try:
            overrides = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(overrides, dict):
                _merge_settings(settings, overrides)
            else:
                logger.warning("Pipeline config %s is not a JSON object. Using defaults.", path)
        except Exception as exc:
            logger.warning("Cannot read pipeline config %s: %s. Using defaults.", path, exc)

    regions = settings.get("analysis", {}).get("allowed_regions", [])
    if not isinstance(regions, list) or not regions:
        settings["analysis"]["allowed_regions"] = DEFAULT_PIPELINE_SETTINGS["analysis"]["allowed_regions"][:]

    pipeline = settings.get("pipeline", {})
    if not pipeline.get("market_topic"):
        pipeline["market_topic"] = DEFAULT_PIPELINE_SETTINGS["pipeline"]["market_topic"]
    if not pipeline.get("report_prefix"):
        pipeline["report_prefix"] = DEFAULT_PIPELINE_SETTINGS["pipeline"]["report_prefix"]

    return settings


def provider_has_credentials(provider_config: dict) -> bool:
    for env_key in provider_config.get("env_keys", []):
        if os.getenv(env_key):
            return True
    return False


def get_runtime_model_info(settings: dict | None = None) -> dict:
    settings = settings or load_pipeline_settings()
    llm = settings["llm"]
    primary = llm["primary"]
    backup = llm["backup"]
    dashboard = settings["dashboard"]

    return {
        "primary_model": {
            "name": primary["name"],
            "provider": primary["provider"],
            "model_id": primary["model_id"].split("/", 1)[-1],
            "parameters": primary["parameters"],
            "temperature": llm["temperature"],
            "context_window": primary["context_window"],
            "api_connected": provider_has_credentials(primary),
        },
        "orchestrator": {
            "name": dashboard["orchestrator"]["name"],
            "version": dashboard["orchestrator"]["version"],
            "agents": dashboard["agents"],
        },
        "tools": dashboard["tools"],
        "backup_provider": {
            "name": backup["provider"],
            "api_connected": provider_has_credentials(backup),
        },
    }


# --- VALIDATION ---
def validate_config():
    """Validates that critical environment variables and files exist."""
    logger = setup_logging("config_validator")
    settings = load_pipeline_settings()

    primary = settings["llm"]["primary"]
    backup = settings["llm"]["backup"]
    if not (provider_has_credentials(primary) or provider_has_credentials(backup)):
        expected = primary["env_keys"] + backup["env_keys"]
        logger.error("CRITICAL ERROR: Missing environment variables: %s", ", ".join(expected))
        logger.error("Please check your .env file.")
        sys.exit(1)

    if not DATABASE_PATH.exists():
        logger.error("CRITICAL ERROR: Database not found at %s", DATABASE_PATH)
        logger.error("Please run 'python src/init_db.py' to initialize the database.")
        sys.exit(1)

    logger.info("Configuration validated successfully.")


# Initialize a default logger for the module
logger = setup_logging()
