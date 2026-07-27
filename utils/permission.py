from telegram import Update


def is_admin(update: Update) -> bool:
    """Check if user is admin in group."""
    if not update.effective_chat:
        return False
    if update.effective_chat.type not in ["group", "supergroup"]:
        return False
    # This is a placeholder – use async version in handlers
    return False
