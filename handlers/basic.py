import time

from telegram import Update
from telegram.ext import ContextTypes


class BasicHandlers:
    """Basic command handlers."""

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message on /start."""
        user = update.effective_user
        await update.message.reply_text(
            f"👋 Hello {user.mention_html()}!\n\n"
            "I'm BrickBot, a community management bot.\n"
            "Use /help to see available commands.",
            parse_mode="HTML"
        )

    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help menu."""
        help_text = (
            "🧱 **BrickBot Help**\n\n"
            "**Basic Commands:**\n"
            "/start – Welcome message\n"
            "/help – Show this help\n"
            "/ping – Check bot latency\n"
            "/id – Get your ID\n"
            "/userinfo – Get user information\n"
            "/about – About this bot\n\n"
        )

        # Premium features
        help_text += (
            "**Premium Commands:**\n"
            "/warn – Warn a user\n"
            "/warnings – View warnings\n"
            "/mute – Mute a user\n"
            "/unmute – Unmute a user\n"
            "/ban – Ban a user\n"
            "/unban – Unban a user\n"
            "/clear – Delete messages\n"
            "/poll – Create a poll\n"
            "/remind – Set a reminder\n"
            "/announce – Schedule an announcement\n"
            "/qr – Generate QR code\n"
            "/random – Random number\n"
            "/dice – Roll a dice\n"
            "/coinflip – Flip a coin\n"
            "/timestamp – Generate a timestamp"
        )

        await update.message.reply_text(help_text, parse_mode="Markdown")

    @staticmethod
    async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check bot latency."""
        start = time.time()
        await update.message.reply_text("🏓 Pinging...")
        end = time.time()
        latency = (end - start) * 1000
        await update.message.edit_text(f"🏓 Pong! `{latency:.0f}ms`", parse_mode="Markdown")

    @staticmethod
    async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get user ID."""
        user = update.effective_user
        chat = update.effective_chat
        await update.message.reply_text(
            f"**Your ID:** `{user.id}`\n"
            f"**Chat ID:** `{chat.id}`",
            parse_mode="Markdown"
        )

    @staticmethod
    async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get user information."""
        user = update.effective_user
        chat = update.effective_chat

        member = None
        if chat.type in ["group", "supergroup"]:
            member = await chat.get_member(user.id)

        info = f"**User Information**\n\n"
        info += f"ID: `{user.id}`\n"
        info += f"Username: @{user.username or 'N/A'}\n"
        info += f"First Name: {user.first_name or 'N/A'}\n"
        info += f"Last Name: {user.last_name or 'N/A'}\n"

        if member:
            info += f"Joined: {member.joined_at.strftime('%Y-%m-%d %H:%M:%S') if member.joined_at else 'N/A'}\n"
            info += f"Status: {member.status}\n"

        await update.message.reply_text(info, parse_mode="Markdown")

    @staticmethod
    async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """About the bot."""
        await update.message.reply_text(
            "🧱 **BrickBot v1.0.0**\n\n"
            "A professional community management bot for Telegram.\n"
            "Built with Python 3.12+ and python-telegram-bot.\n\n"
            "🛡️ Secure • 📦 Modular • 🚀 Scalable"
      )
