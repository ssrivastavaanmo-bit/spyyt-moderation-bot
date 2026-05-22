from telegram import Update, ChatPermissions
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

from datetime import timedelta
import time
import re
import logging
import os

# ==========================================
# CONFIG
# ==========================================

TOKEN = os.getenv("TOKEN")

BAD_WORDS = [
    "mc",
    "bc",
    "madarchod",
    "bhenchod",
    "fuck",
    "shit"
]

MAX_WARNS = 3
MUTE_HOURS = 2
FLOOD_LIMIT = 5
FLOOD_TIME = 10

# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ==========================================
# MEMORY DATABASE
# ==========================================

warns = {}
user_messages = {}

# ==========================================
# ADMIN CHECK
# ==========================================

def is_admin(chat_id, user_id, context):

    admins = context.bot.get_chat_administrators(chat_id)

    for admin in admins:

        if admin.user.id == user_id:
            return True

    return False

# ==========================================
# START COMMAND
# ==========================================

def start(update: Update, context: CallbackContext):

    update.message.reply_text(
        "🔥 SPYYT MODERATION BOT ACTIVE"
    )

# ==========================================
# WARNINGS COMMAND
# ==========================================

def warnings(update: Update, context: CallbackContext):

    user_id = update.effective_user.id

    count = warns.get(user_id, 0)

    update.message.reply_text(
        f"⚠️ Your warnings: {count}"
    )

# ==========================================
# MAIN MODERATION
# ==========================================

def moderate(update: Update, context: CallbackContext):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.lower()

    user = update.effective_user

    chat_id = update.effective_chat.id

    # ======================================
    # ADMIN BYPASS
    # ======================================

    if is_admin(chat_id, user.id, context):
        return

    # ======================================
    # FLOOD DETECTION
    # ======================================

    now = time.time()

    if user.id not in user_messages:
        user_messages[user.id] = []

    user_messages[user.id].append(now)

    user_messages[user.id] = [
        t for t in user_messages[user.id]
        if now - t < FLOOD_TIME
    ]

    if len(user_messages[user.id]) >= FLOOD_LIMIT:

        try:

            update.message.delete()

            context.bot.restrict_chat_member(
                chat_id,
                user.id,
                ChatPermissions(
                    can_send_messages=False
                ),
                until_date=update.message.date + timedelta(minutes=10)
            )

            context.bot.send_message(
                chat_id,
                f"🚫 {user.first_name} muted for flooding."
            )

        except Exception as e:
            logger.error(e)

        return

    # ======================================
    # LINK BLOCKER
    # ======================================

    if re.search(r"(https?://|t\.me/)", text):

        try:

            update.message.delete()

            context.bot.send_message(
                chat_id,
                "🚫 Links are not allowed."
            )

        except Exception as e:
            logger.error(e)

        return

    # ======================================
    # BAD WORD FILTER
    # ======================================

    for word in BAD_WORDS:

        if word in text:

            try:

                update.message.delete()

                warns[user.id] = warns.get(user.id, 0) + 1

                count = warns[user.id]

                # ==========================
                # AUTO BAN
                # ==========================

                if count >= MAX_WARNS:

                    context.bot.ban_chat_member(
                        chat_id,
                        user.id
                    )

                    context.bot.send_message(
                        chat_id,
                        f"⛔ {user.first_name} banned."
                    )

                    warns[user.id] = 0

                    return

                # ==========================
                # AUTO MUTE
                # ==========================

                context.bot.restrict_chat_member(
                    chat_id,
                    user.id,
                    ChatPermissions(
                        can_send_messages=False
                    ),
                    until_date=update.message.date + timedelta(hours=MUTE_HOURS)
                )

                context.bot.send_message(
                    chat_id,
                    f"""
🚫 Bad language detected

👤 User: {user.first_name}
⚠️ Warnings: {count}/{MAX_WARNS}
🔇 Muted for {MUTE_HOURS} hours
"""
                )

            except Exception as e:
                logger.error(e)

            return

# ==========================================
# ERROR HANDLER
# ==========================================

def error_handler(update, context):

    logger.warning(f"Update {update} caused error {context.error}")

# ==========================================
# MAIN
# ==========================================

def main():

    updater = Updater(
        TOKEN,
        use_context=True
    )

    dp = updater.dispatcher

    # Commands

    dp.add_handler(
        CommandHandler("start", start)
    )

    dp.add_handler(
        CommandHandler("warnings", warnings)
    )

    # Moderation

    dp.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            moderate
        )
    )

    # Error Handler

    dp.add_error_handler(error_handler)

    # Start Bot

    print("🔥 SPYYT BOT RUNNING")

    updater.start_polling(
        drop_pending_updates=True
    )

    updater.idle()

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    main()
