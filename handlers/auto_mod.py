import re
from collections import defaultdict
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes


class AutoModHandlers:
    """Auto-moderation message handlers."""

    message_history = defaultdict(list)

    invite_pattern = re.compile(r"(?:discord\.gg|t\.me|telegram\.me)/[a-zA-Z0-9]+")
    link_pattern = re.compile(r"https?://[^\s]+")
    scam_patterns = [
        r"free\s+(?:nitro|robux|vbucks|gift|money)",
        r"giveaway",
        r"bit\.ly",
    ]
    bad_words = ["fuck", "shit", "damn", "hell", "bitch", "cunt", "nigger", "faggot", "retard", "kys"]

    @classmethod
    async def check_message(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check message for auto-moderation violations."""
        if not update.effective_message:
            return
        if not update.effective_chat:
            return
        if update.effective_chat.type not in ["group", "supergroup"]:
            return

        message = update.effective_message
        user = message.from_user
        if not user:
            return

        member = await update.effective_chat.get_member(user.id)
        if member.status in ["creator", "administrator"]:
            return

        text = message.text or ""
        violations = []

        # Anti-spam
        now = datetime.now()
        cls.message_history[(update.effective_chat.id, user.id)].append(now)
        threshold = now - timedelta(seconds=5)
        cls.message_history[(update.effective_chat.id, user.id)] = [
            t for t in cls.message_history[(update.effective_chat.id, user.id)] if t > threshold
        ]
        if len(cls.message_history[(update.effective_chat.id, user.id)]) > 5:
            violations.append("spam")

        # Anti-link
        if "http" in text.lower():
            violations.append("link")

        # Anti-invite
        if cls.invite_pattern.search(text):
            violations.append("invite")

        # Anti-scam
        for pattern in cls.scam_patterns:
            if re.search(pattern, text.lower()):
                violations.append("scam")
                break

        # Word filter
        for word in cls.bad_words:
            if word in text.lower():
                violations.append("bad_word")
                break

        if violations:
            try:
                await message.delete()
                await message.reply_text(
                    f"🚫 {user.mention_html()}: Your message was removed due to: {', '.join(violations)}",
                    parse_mode="HTML"
                )
            except Exception:
                pass
