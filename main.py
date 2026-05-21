from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from datetime import timedelta
import time
import re
import logging

# ====================================
# BOT TOKEN
# ====================================

TOKEN = "8917728575:AAFwlrYx8pN0H4ci5r9yZKXvnoa2O9LOyTc"

# ====================================
# SETTINGS
# ====================================

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

# ====================================
# LOGGING
# ====================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ====================================
# WARN DATABASE
# ====================================

warns = {}

# ====================================
# FLOOD SYSTEM
# ====================================

user_messages = {}

# ====================================
# ADMIN CHECK
# ====================================

async def is_admin(chat_id, user_id, context):

    admins = await context.bot.get_chat_administrators(chat_id)

    for admin in admins:
        if admin.user.id == user_id:
            return True

    return False

# ====================================
# START
# ====================================

async def start(update: Update, context):

    await update.message.reply_text(
        "🔥 SPYYT MODERATION BOT ACTIVE"
    )

# ====================================
# WARN COMMAND
# ====================================

async def warnings(update: Update, context):

    user_id = update.effective_user.id

    count = warns.get(user_id, 0)

    await update.message.reply_text(
        f"⚠️ Your warnings: {count}"
    )

# ====================================
# MAIN MODERATION
# ====================================

async def moderate(update: Update, context):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.lower()

    user = update.effective_user

    chat_id = update.effective_chat.id

    # ====================================
    # ADMIN BYPASS
    # ====================================

    if await is_admin(chat_id, user.id, context):
        return

    # ====================================
    # FLOOD DETECTION
    # ====================================

    now = time.time()

    if user.id not in user_messages:
        user_messages[user.id] = []

    user_messages[user.id].append(now)

    user_messages[user.id] = [
        t for t in user_messages[user.id]
        if now - t < 10
    ]

    if len(user_messages[user.id]) >= 5:

        await update.message.delete()

        await context.bot.restrict_chat_member(
            chat_id,
            user.id,
            ChatPermissions(
                can_send_messages=False
            ),
            until_date=update.message.date + timedelta(minutes=10)
        )

        await context.bot.send_message(
            chat_id,
            f"🚫 {user.first_name} muted for flooding."
        )

        return

    # ====================================
    # LINK BLOCKER
    # ====================================

    if re.search(r"(https?://|t\.me/)", text):

        await update.message.delete()

        await context.bot.send_message(
            chat_id,
            "🚫 Links are not allowed."
        )

        return

    # ====================================
    # BAD WORD FILTER
    # ====================================

    for word in BAD_WORDS:

        if word in text:

            await update.message.delete()

            warns[user.id] = warns.get(user.id, 0) + 1

            count = warns[user.id]

            # AUTO BAN

            if count >= MAX_WARNS:

                await context.bot.ban_chat_member(
                    chat_id,
                    user.id
                )

                await context.bot.send_message(
                    chat_id,
                    f"⛔ {user.first_name} banned."
                )

                warns[user.id] = 0

                return

            # AUTO MUTE

            await context.bot.restrict_chat_member(
                chat_id,
                user.id,
                ChatPermissions(
                    can_send_messages=False
                ),
                until_date=update.message.date + timedelta(hours=MUTE_HOURS)
            )

            await context.bot.send_message(
                chat_id,
                f"""
🚫 Bad language detected

👤 User: {user.first_name}
⚠️ Warnings: {count}/{MAX_WARNS}
🔇 Muted for {MUTE_HOURS} hours
"""
            )

            return

# ====================================
# RUN BOT
# ====================================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("warnings", warnings))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            moderate
        )
    )

    print("🔥 BOT RUNNING")

    app.run_polling()

if __name__ == "__main__":
    main()
