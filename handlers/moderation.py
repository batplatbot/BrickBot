import json
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes


class ModerationHandlers:
    """Moderation command handlers."""

    @staticmethod
    async def _is_admin(update: Update) -> bool:
        """Check if user is admin."""
        if not update.effective_chat:
            return False
        if update.effective_chat.type not in ["group", "supergroup"]:
            return False
        member = await update.effective_chat.get_member(update.effective_user.id)
        return member.status in ["creator", "administrator"]

    @staticmethod
    async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Warn a user (admin only)."""
        if not await ModerationHandlers._is_admin(update):
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /warn <user> <reason>")
            return

        try:
            user_id = int(context.args[0])
        except ValueError:
            if update.message.reply_to_message:
                user_id = update.message.reply_to_message.from_user.id
            else:
                await update.message.reply_text("Please mention a user or reply to their message.")
                return

        reason = " ".join(context.args[1:]) or "No reason provided"

        from utils.database import Database
        db = Database("data/brickbot.db")

        warnings = await db.fetch_one(
            "SELECT warnings FROM users WHERE user_id = ? AND group_id = ?",
            (user_id, update.effective_chat.id)
        )

        warning_list = json.loads(warnings["warnings"]) if warnings else []
        warning_list.append({
            "moderator": update.effective_user.id,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

        await db.execute(
            "INSERT OR REPLACE INTO users (user_id, group_id, warnings) VALUES (?, ?, ?)",
            (user_id, update.effective_chat.id, json.dumps(warning_list))
        )

        await update.message.reply_text(
            f"⚠️ User <a href='tg://user?id={user_id}'>{user_id}</a> has been warned.\n"
            f"Reason: {reason}\n"
            f"Total warnings: {len(warning_list)}",
            parse_mode="HTML"
        )

    @staticmethod
    async def warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View warnings for a user."""
        if not await ModerationHandlers._is_admin(update):
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        user_id = None
        if context.args:
            try:
                user_id = int(context.args[0])
            except ValueError:
                pass

        if not user_id and update.message.reply_to_message:
            user_id = update.message.reply_to_message.from_user.id

        if not user_id:
            user_id = update.effective_user.id

        from utils.database import Database
        db = Database("data/brickbot.db")

        warnings = await db.fetch_one(
            "SELECT warnings FROM users WHERE user_id = ? AND group_id = ?",
            (user_id, update.effective_chat.id)
        )

        if not warnings or not warnings["warnings"]:
            await update.message.reply_text("No warnings found for this user.")
            return

        warning_list = json.loads(warnings["warnings"])
        text = f"⚠️ **Warnings for user {user_id}**\n\n"
        for i, w in enumerate(warning_list[-5:], 1):
            text += f"{i}. {w.get('reason', 'No reason')} (by {w.get('moderator', 'Unknown')})\n"

        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mute a user (admin only)."""
        if not await ModerationHandlers._is_admin(update):
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /mute <user> <duration_minutes>")
            return

        try:
            user_id = int(context.args[0])
            duration = int(context.args[1]) if len(context.args) > 1 else 10
        except ValueError:
            await update.message.reply_text("Invalid user ID or duration.")
            return

        until_date = datetime.now() + timedelta(minutes=duration)

        try:
            await update.effective_chat.restrict_member(
                user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            await update.message.reply_text(
                f"🔇 User <a href='tg://user?id={user_id}'>{user_id}</a> has been muted for {duration} minutes.",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to mute user: {e}")

    @staticmethod
    async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unmute a user (admin only)."""
        if not await ModerationHandlers._is_admin(update):
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /unmute <user>")
            return

        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Invalid user ID.")
            return

        try:
            await update.effective_chat.restrict_member(
                user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            await update.message.reply_text(
                f"🔊 User <a href='tg://user?id={user_id}'>{user_id}</a> has been unmuted.",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to unmute user: {e}")

    @staticmethod
    async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban a user (admin only)."""
        if not await ModerationHandlers._is_admin(update):
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /ban <user> [reason]")
            return

        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Invalid user ID.")
            return

        reason = " ".join(context.args[1:]) or "No reason provided"

        try:
            await update.effective_chat.ban_member(user_id)
            await update.message.reply_text(
                f"🔨 User <a href='tg://user?id={user_id}'>{user_id}</a> has been banned.\nReason: {reason}",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to ban user: {e}")

    @staticmethod
    async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban a user (admin only)."""
        if not await ModerationHandlers._is_admin(update):
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /unban <user>")
            return

        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Invalid user ID.")
            return

        try:
            await update.effective_chat.unban_member(user_id)
            await update.message.reply_text(
                f"✅ User <a href='tg://user?id={user_id}'>{user_id}</a> has been unbanned.",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to unban user: {e}")

    @staticmethod
    async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete messages (admin only)."""
        if not await ModerationHandlers._is_admin(update):
            await update.message.reply_text("❌ You need to be an admin to use this command.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /clear <count>")
            return

        try:
            count = int(context.args[0])
            if count < 1 or count > 100:
                await update.message.reply_text("Please provide a number between 1 and 100.")
                return
        except ValueError:
            await update.message.reply_text("Please provide a valid number.")
            return

        try:
            deleted = await update.message.chat.delete_messages(
                [msg.message_id for msg in await update.message.chat.get_messages(count + 1)]
            )
            await update.message.reply_text(f"✅ Deleted {len(deleted)} messages.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to delete messages: {e}")
