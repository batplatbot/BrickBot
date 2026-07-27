from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters


class SupportHandlers:
    """Support and FAQ handlers."""

    SUPPORT_QUESTION = 0

    FAQ = {
        "How do I get started?": "Just use /start to begin!",
        "What is BrickBot?": "BrickBot is a community management bot for Telegram.",
        "Is BrickBot free?": "Basic features are free. Premium features are available for a small fee.",
        "How do I report a bug?": "Please contact the bot admin or use the /support command.",
    }

    @classmethod
    async def faq(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show FAQ menu."""
        keyboard = []
        for question in cls.FAQ:
            keyboard.append([InlineKeyboardButton(question, callback_data=f"faq_{question}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📚 **Frequently Asked Questions**\n\nSelect a question below:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    @classmethod
    async def faq_callback(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle FAQ selection."""
        query = update.callback_query
        await query.answer()

        question = query.data.replace("faq_", "")
        answer = cls.FAQ.get(question, "No answer found.")

        await query.edit_message_text(
            f"**Q:** {question}\n\n**A:** {answer}",
            parse_mode="Markdown"
        )

    @classmethod
    async def support(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start support conversation."""
        await update.message.reply_text(
            "🆘 **Support**\n\nPlease describe your issue and I'll help you.\n"
            "Type /cancel to cancel.",
            parse_mode="Markdown"
        )
        return cls.SUPPORT_QUESTION

    @classmethod
    async def support_question(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle support question."""
        issue = update.message.text
        await update.message.reply_text(
            f"✅ Thank you for your message. A support team member will respond soon.\n\n"
            f"**Your issue:**\n{issue}"
        )
        return ConversationHandler.END

    @classmethod
    async def cancel(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel support conversation."""
        await update.message.reply_text("✅ Support conversation cancelled.")
        return ConversationHandler.END


def get_conversation_handler():
    """Return the support conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("support", SupportHandlers.support)],
        states={
            SupportHandlers.SUPPORT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, SupportHandlers.support_question)
            ]
        },
        fallbacks=[CommandHandler("cancel", SupportHandlers.cancel)]
                           )
