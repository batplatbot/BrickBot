import os
import sys
import json
import logging
import logging.config
from pathlib import Path

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# ============================================================
# 1. Ensure required directories exist
# ============================================================
def ensure_directories():
    """Create necessary directories for logs and database."""
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(parents=True, exist_ok=True)

ensure_directories()

# ============================================================
# 2. Environment‑aware logging setup
# ============================================================
def setup_logging():
    """Configure logging based on environment (local vs cloud)."""
    # Check if running on Render (or any cloud platform)
    is_cloud = os.getenv("RENDER") == "true" or os.getenv("DYNO")  # Heroku

    # Basic config for cloud: only console output
    if is_cloud:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        # Also create a logger for the bot
        logger = logging.getLogger("brickbot")
        logger.info("Running in cloud mode – console logging only.")
        return

    # Local development: use rotating file + console
    try:
        # Try to load the config file
        logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
        logger = logging.getLogger("brickbot")
        logger.info("Running in local mode – file logging enabled.")
    except Exception as e:
        # Fallback if logging.conf is missing or invalid
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.handlers.RotatingFileHandler(
                    "data/logs/brickbot.log", maxBytes=10485760, backupCount=5
                )
            ]
        )
        logger = logging.getLogger("brickbot")
        logger.warning(f"Could not load logging.conf, using fallback config: {e}")

# ============================================================
# 3. Load environment and config
# ============================================================
load_dotenv()

with open("config.json") as f:
    CONFIG = json.load(f)

# ============================================================
# 4. Main Bot Class
# ============================================================
class BrickBot:
    """Main bot class."""

    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN not set in .env")

        self.config = CONFIG
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.admin_ids = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

        # Build application
        self.app = Application.builder().token(self.token).build()

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register all command and message handlers."""
        from handlers.basic import BasicHandlers
        from handlers.community import CommunityHandlers
        from handlers.moderation import ModerationHandlers
        from handlers.auto_mod import AutoModHandlers
        from handlers.support import SupportHandlers, get_conversation_handler
        from handlers.utility import UtilityHandlers

        # Basic commands
        self.app.add_handler(CommandHandler("start", BasicHandlers.start))
        self.app.add_handler(CommandHandler("help", BasicHandlers.help_command))
        self.app.add_handler(CommandHandler("ping", BasicHandlers.ping))
        self.app.add_handler(CommandHandler("id", BasicHandlers.id_command))
        self.app.add_handler(CommandHandler("userinfo", BasicHandlers.userinfo))
        self.app.add_handler(CommandHandler("about", BasicHandlers.about))

        # Community
        self.app.add_handler(CommandHandler("setwelcome", CommunityHandlers.set_welcome))
        self.app.add_handler(CommandHandler("setgoodbye", CommunityHandlers.set_goodbye))

        # Moderation (premium)
        if self.config.get("premium", {}).get("enabled", False):
            self.app.add_handler(CommandHandler("warn", ModerationHandlers.warn))
            self.app.add_handler(CommandHandler("warnings", ModerationHandlers.warnings))
            self.app.add_handler(CommandHandler("mute", ModerationHandlers.mute))
            self.app.add_handler(CommandHandler("unmute", ModerationHandlers.unmute))
            self.app.add_handler(CommandHandler("ban", ModerationHandlers.ban))
            self.app.add_handler(CommandHandler("unban", ModerationHandlers.unban))
            self.app.add_handler(CommandHandler("clear", ModerationHandlers.clear))

        # Auto-moderation (premium)
        if self.config.get("premium", {}).get("enabled", False):
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, AutoModHandlers.check_message))

        # Support (premium)
        if self.config.get("premium", {}).get("enabled", False):
            self.app.add_handler(CommandHandler("faq", SupportHandlers.faq))
            self.app.add_handler(CallbackQueryHandler(SupportHandlers.faq_callback, pattern="^faq_"))
            self.app.add_handler(get_conversation_handler())

        # Utility (premium)
        if self.config.get("premium", {}).get("enabled", False):
            self.app.add_handler(CommandHandler("poll", UtilityHandlers.poll))
            self.app.add_handler(CommandHandler("remind", UtilityHandlers.remind))
            self.app.add_handler(CommandHandler("announce", UtilityHandlers.announce))
            self.app.add_handler(CommandHandler("qr", UtilityHandlers.qr))
            self.app.add_handler(CommandHandler("random", UtilityHandlers.random_number))
            self.app.add_handler(CommandHandler("dice", UtilityHandlers.dice))
            self.app.add_handler(CommandHandler("coinflip", UtilityHandlers.coinflip))
            self.app.add_handler(CommandHandler("timestamp", UtilityHandlers.timestamp))

        # Error handler
        self.app.add_error_handler(self._error_handler)

        # Start-up notification
        self.app.post_init = self._on_startup

    async def _on_startup(self, application):
        """Send startup notification to Discord webhook."""
        if self.discord_webhook:
            from utils.discord_webhook import send_discord_webhook
            await send_discord_webhook(
                self.discord_webhook,
                "🟢 BrickBot started",
                f"Version: {self.config['bot']['version']}"
            )
        logger = logging.getLogger("brickbot")
        logger.info("BrickBot started")

    async def _error_handler(self, update, context):
        """Global error handler."""
        logger = logging.getLogger("brickbot")
        logger.error(f"Error: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ An error occurred. Please try again later.")

    def run(self):
        """Start the bot."""
        logger = logging.getLogger("brickbot")
        logger.info("Starting BrickBot...")
        self.app.run_polling()


if __name__ == "__main__":
    setup_logging()
    try:
        bot = BrickBot()
        bot.run()
    except KeyboardInterrupt:
        logger = logging.getLogger("brickbot")
        logger.info("Bot stopped by user")
    except Exception as e:
        logger = logging.getLogger("brickbot")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
