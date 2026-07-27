import json 
from telegram import Update
from telegram.ext import ContextTypes


class CommunityHandlers:
    """Community feature handlers."""

    @staticmethod
    async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set welcome message (admin only)."""
        if not update.effective_user:
            return

        if update.effective_chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("This command only works in groups.")
            return

        member = await update.effective_chat.get_member(update.effective_user.id)
        if not member.status in ["creator", "administrator"]:
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        message_text = update.message.text.replace("/setwelcome", "").strip()
        if not message_text:
            await update.message.reply_text("Please provide a welcome message. Example: /setwelcome Welcome {user} to {group}!")
            return

        from utils.database import Database
        db = Database("data/brickbot.db")
        await db.execute(
            "INSERT OR REPLACE INTO group_config (group_id, config) VALUES (?, ?)",
            (update.effective_chat.id, json.dumps({"welcome": message_text}))
        )

        await update.message.reply_text(f"✅ Welcome message set: {message_text}")

    @staticmethod
    async def set_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set goodbye message (admin only)."""
        if not update.effective_user:
            return

        if update.effective_chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("This command only works in groups.")
            return

        member = await update.effective_chat.get_member(update.effective_user.id)
        if not member.status in ["creator", "administrator"]:
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        message_text = update.message.text.replace("/setgoodbye", "").strip()
        if not message_text:
            await update.message.reply_text("Please provide a goodbye message. Example: /setgoodbye {user} has left {group}!")
            return

        from utils.database import Database
        db = Database("data/brickbot.db")
        await db.execute(
            "INSERT OR REPLACE INTO group_config (group_id, config) VALUES (?, ?)",
            (update.effective_chat.id, json.dumps({"goodbye": message_text}))
        )

        await update.message.reply_text(f"✅ Goodbye message set: {message_text}")
