import logging

import anthropic
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config.settings import (
    TELEGRAM_BOT_TOKEN,
    ANTHROPIC_API_KEY,
    WEBHOOK_URL,
    WEBHOOK_PORT,
    LOG_LEVEL,
    validate_config,
)
from core.conversation_manager import ConversationManager
from memory.memory_store import MemoryStore
from bot.handlers import (
    init_handlers,
    start_command,
    help_command,
    journey_command,
    patterns_command,
    approve_command,
    clear_command,
    handle_photo,
    handle_text,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger(__name__)


def build_app() -> Application:
    """Build and configure the Telegram bot application."""
    missing = validate_config()
    if missing:
        raise RuntimeError(f"Missing required config: {', '.join(missing)}")

    # Shared services
    claude_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    conversation_manager = ConversationManager()
    memory_store = MemoryStore()

    init_handlers(claude_client, conversation_manager, memory_store)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("journey", journey_command))
    app.add_handler(CommandHandler("patterns", patterns_command))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("clear", clear_command))

    # Media
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Text (follow-ups and approvals)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info(f"KayaFlow bot initialized. Memory store: {memory_store.count()} patterns loaded.")
    return app


def run_polling() -> None:
    """Run bot in polling mode (development)."""
    app = build_app()
    logger.info("Starting KayaFlow in polling mode...")
    app.run_polling(drop_pending_updates=True)


def run_webhook() -> None:
    """Run bot in webhook mode (production)."""
    if not WEBHOOK_URL:
        raise RuntimeError("WEBHOOK_URL must be set for webhook mode")
    app = build_app()
    logger.info(f"Starting KayaFlow in webhook mode: {WEBHOOK_URL}")
    app.run_webhook(
        listen="0.0.0.0",
        port=WEBHOOK_PORT,
        webhook_url=WEBHOOK_URL,
    )


if __name__ == "__main__":
    run_polling()
