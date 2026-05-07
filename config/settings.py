import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Claude models
CLAUDE_CRITIQUE_MODEL = os.getenv("CLAUDE_CRITIQUE_MODEL", "claude-sonnet-4-6")
CLAUDE_QUICK_MODEL = os.getenv("CLAUDE_QUICK_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Memory
MEMORY_STORE_PATH = Path(os.getenv("MEMORY_STORE_PATH", str(BASE_DIR / "memory" / "store.json")))
DESIGN_MEMORY_PATH = Path(os.getenv("DESIGN_MEMORY_PATH", str(BASE_DIR / "design-memory")))

# Features
OCR_ENABLED = os.getenv("OCR_ENABLED", "false").lower() == "true"
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "20"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Webhook (optional — leave empty for polling mode)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8443"))

# Admin
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0")) if os.getenv("ADMIN_USER_ID") else None

# Journey categories — order matters for detection priority
JOURNEY_CATEGORIES = [
    "onboarding",
    "kyc",
    "trust-signals",
    "cta-patterns",
    "navigation",
    "anti-patterns",
]

JOURNEY_CATEGORY_LABELS = {
    "onboarding": "Onboarding",
    "kyc": "KYC / Identity Verification",
    "trust-signals": "Trust Signals",
    "cta-patterns": "CTA & Conversion",
    "navigation": "Navigation & Wayfinding",
    "anti-patterns": "Anti-patterns",
}


def validate_config() -> list[str]:
    """Return list of missing required config values."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    return missing
