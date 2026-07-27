import random
import qrcode
from io import BytesIO
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes


class UtilityHandlers:
    """Utility command handlers."""

    @staticmethod
    async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a poll."""
        if not context.args:
            await update.message.reply_text("Usage: /poll <question> | option1 | option2 | ...")
            return

        parts = " ".join(context.args).split("|")
        question = parts[0].strip()
        options = [opt.strip() for opt in parts[1:] if opt.strip()]

        if len(options) < 2:
            await update.message.reply_text("Please provide at least 2 options.")
            return

        if len(options) > 10:
            await update.message.reply_text("Maximum 10 options allowed.")
            return

        try:
            await update.message.poll_poll(
                question=question,
                options=options,
                is_anonymous=True,
                allows_multiple_answers=False,
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to create poll: {e}")

    @staticmethod
    async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set a reminder."""
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /remind <minutes> <message>")
            return

        try:
            minutes = int(context.args[0])
            message = " ".join(context.args[1:])
        except ValueError:
            await update.message.reply_text("Please provide a valid number of minutes.")
            return

        if minutes < 1 or minutes > 1440:
            await update.message.reply_text("Please provide between 1 and 1440 minutes.")
            return

        from utils.database import Database
        db = Database("data/brickbot.db")
        remind_at = datetime.now() + timedelta(minutes=minutes)
        await db.execute(
            "INSERT INTO reminders (user_id, chat_id, message, remind_at) VALUES (?, ?, ?, ?)",
            (update.effective_user.id, update.effective_chat.id, message, remind_at.isoformat())
        )

        await update.message.reply_text(
            f"✅ Reminder set for {minutes} minutes: {message}"
        )

    @staticmethod
    async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Schedule an announcement (admin only)."""
        if update.effective_chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("This command only works in groups.")
            return

        member = await update.effective_chat.get_member(update.effective_user.id)
        if not member.status in ["creator", "administrator"]:
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /announce <message>")
            return

        message = " ".join(context.args)
        await update.message.reply_text(f"📢 **Announcement**\n\n{message}", parse_mode="Markdown")

    @staticmethod
    async def qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate a QR code."""
        if not context.args:
            await update.message.reply_text("Usage: /qr <text>")
            return

        text = " ".join(context.args)

        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            bio = BytesIO()
            img.save(bio, "PNG")
            bio.seek(0)

            await update.message.reply_photo(photo=bio, caption=f"QR Code for: {text[:50]}...")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to generate QR code: {e}")

    @staticmethod
    async def random_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate a random number."""
        if len(context.args) == 0:
            min_val, max_val = 1, 100
        elif len(context.args) == 1:
            try:
                max_val = int(context.args[0])
                min_val = 1
            except ValueError:
                await update.message.reply_text("Please provide valid numbers.")
                return
        else:
            try:
                min_val = int(context.args[0])
                max_val = int(context.args[1])
            except ValueError:
                await update.message.reply_text("Please provide valid numbers.")
                return

        if min_val > max_val:
            min_val, max_val = max_val, min_val

        result = random.randint(min_val, max_val)
        await update.message.reply_text(f"🎲 Random number between {min_val} and {max_val}: **{result}**", parse_mode="Markdown")

    @staticmethod
    async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Roll a dice."""
        sides = int(context.args[0]) if context.args and context.args[0].isdigit() else 6
        if sides < 2 or sides > 100:
            await update.message.reply_text("Please provide a number between 2 and 100.")
            return

        result = random.randint(1, sides)
        await update.message.reply_text(f"🎲 Rolling a d{sides}: **{result}**", parse_mode="Markdown")

    @staticmethod
    async def coinflip(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Flip a coin."""
        result = random.choice(["Heads", "Tails"])
        await update.message.reply_text(f"🪙 Coin flip: **{result}**", parse_mode="Markdown")

    @staticmethod
    async def timestamp(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate a Discord-style timestamp."""
        now = int(datetime.now().timestamp())
        await update.message.reply_text(
            f"📅 **Current Timestamp**\n\n"
            f"Unix: `{now}`\n"
            f"Short Time: <t:{now}:t>\n"
            f"Long Time: <t:{now}:T>\n"
            f"Short Date: <t:{now}:d>\n"
            f"Long Date: <t:{now}:D>\n"
            f"Relative: <t:{now}:R>",
            parse_mode="Markdown"
      )
