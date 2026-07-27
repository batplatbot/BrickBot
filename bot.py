import os
import sys
import json
import logging
import logging.config
import logging.handlers
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
    """
    Configure logging based on environment (local vs cloud).
    - Cloud (Render, Heroku): console logging only (stdout).
    - Local: rotating file logging + console.
    """
    # Detect cloud environment
    is_cloud = os.getenv("RENDER") == "true" or os.getenv("DYNO") is not None

    if is_cloud:
        # Cloud mode: only console output (platforms capture stdout)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logger = logging.getLogger("brickbot")
        logger.info("Running in cloud mode – console logging only.")
        return

    # Local development: try to load logging.conf
    try:
        if os.path.exists("logging.conf"):
            logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
            logger = logging.getLogger("brickbot")
            logger.info("Running in local mode – using logging.conf.")
        else:
            raise FileNotFoundError("logging.conf not found")
    except Exception as e:
        # Fallback: programmatic configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.handlers.RotatingFileHandler(
                    "data/logs/brickbot.log",
                    maxBytes=10485760,
                    backupCount=5
                )
            ]
        )
        logger = logging.getLogger("brickbot")
        logger.warning(f"Could not load logging.conf, using fallback config: {e}")

# ============================================================
# 3. Load environment and config
# ============================================================
load_dotenv()

# Verify token is set
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN not set in .env")

with open("config.json") as f:
    CONFIG = json.load(f)

# ============================================================
# 4. Main Bot Class
# ============================================================
class BrickBot:
    """Main bot class."""

    def __init__(self):
        self.token = TOKEN
        self.config = CONFIG
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.admin_ids = [
            int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
        ]

        # Build application
        self.app = Application.builder().token(self.token).build()

        # Register handlers
        self._register_handlers()

        # Set up post-init hook
        self.app.post_init = self._on_startup

        # Error handler
        self.app.add_error_handler(self._error_handler)

    def _register_handlers(self):
        """Register all command and message handlers."""
        from handlers.basic import BasicHandlers
        from handlers.community import CommunityHandlers
        from handlers.moderation import ModerationHandlers
        from handlers.auto_mod import AutoModHandlers
        from handlers.support import SupportHandlers, get_conversation_handler
        from handlers.utility import UtilityHandlers

        # ─── Basic commands ──────────────────────────────
        self.app.add_handler(CommandHandler("start", BasicHandlers.start))
        self.app.add_handler(CommandHandler("help", BasicHandlers.help_command))
        self.app.add_handler(CommandHandler("ping", BasicHandlers.ping))
        self.app.add_handler(CommandHandler("id", BasicHandlers.id_command))
        self.app.add_handler(CommandHandler("userinfo", BasicHandlers.userinfo))
        self.app.add_handler(CommandHandler("about", BasicHandlers.about))

        # ─── Community ────────────────────────────────────
        self.app.add_handler(CommandHandler("setwelcome", CommunityHandlers.set_welcome))
        self.app.add_handler(CommandHandler("setgoodbye", CommunityHandlers.set_goodbye))

        # ─── Premium: Moderation ─────────────────────────
        if self.config.get("premium", {}).get("enabled", False):
            self.app.add_handler(CommandHandler("warn", ModerationHandlers.warn))
            self.app.add_handler(CommandHandler("warnings", ModerationHandlers.warnings))
            self.app.add_handler(CommandHandler("mute", ModerationHandlers.mute))
            self.app.add_handler(CommandHandler("unmute", ModerationHandlers.unmute))
            self.app.add_handler(CommandHandler("ban", ModerationHandlers.ban))
            self.app.add_handler(CommandHandler("unban", ModerationHandlers.unban))
            self.app.add_handler(CommandHandler("clear", ModerationHandlers.clear))

        # ─── Premium: Auto-moderation ────────────────────
        if self.config.get("premium", {}).get("enabled", False):
            self.app.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, AutoModHandlers.check_message)
            )

        # ─── Premium: Support ────────────────────────────
        if self.config.get("premium", {}).get("enabled", False):
            self.app.add_handler(CommandHandler("faq", SupportHandlers.faq))
            self.app.add_handler(
                CallbackQueryHandler(SupportHandlers.faq_callback, pattern="^faq_")
            )
            self.app.add_handler(get_conversation_handler())

        # ─── Premium: Utility ────────────────────────────
        if self.config.get("premium", {}).get("enabled", False):
            self.app.add_handler(CommandHandler("poll", UtilityHandlers.poll))
            self.app.add_handler(CommandHandler("remind", UtilityHandlers.remind))
            self.app.add_handler(CommandHandler("announce", UtilityHandlers.announce))
            self.app.add_handler(CommandHandler("qr", UtilityHandlers.qr))
            self.app.add_handler(CommandHandler("random", UtilityHandlers.random_number))
            self.app.add_handler(CommandHandler("dice", UtilityHandlers.dice))
            self.app.add_handler(CommandHandler("coinflip", UtilityHandlers.coinflip))
            self.app.add_handler(CommandHandler("timestamp", UtilityHandlers.timestamp))

    async def _on_startup(self, application):
        """Send startup notification to Discord webhook."""
        logger = logging.getLogger("brickbot")
        logger.info("BrickBot started successfully.")

        if self.discord_webhook:
            try:
                from utils.discord_webhook import send_discord_webhook
                await send_discord_webhook(
                    self.discord_webhook,
                    "🟢 BrickBot started",
                    f"Version: {self.config['bot']['version']}"
                )
            except Exception as e:
                logger.warning(f"Could not send Discord startup notification: {e}")

    async def _error_handler(self, update, context):
        """Global error handler for the bot."""
        logger = logging.getLogger("brickbot")
        logger.error(f"Error: {context.error}")

        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later."
                )
            except Exception:
                pass

    def run(self):
        """Start the bot with polling."""
        logger = logging.getLogger("brickbot")
        logger.info("Starting BrickBot polling...")

        # drop_pending_updates=True prevents conflict errors and discards old updates
        self.app.run_polling(drop_pending_updates=True)


# ============================================================
# 5. Entry Point
# ============================================================
if __name__ == "__main__":
    # Setup logging first
    setup_logging()
    logger = logging.getLogger("brickbot")

    try:
        bot = BrickBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
