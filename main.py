from telegram import Update, ChatPermissions
from telegram.ext import *

from datetime import timedelta
import time
import re

TOKEN = "8917728575:AAFwlrYx8pN0H4ci5r9yZKXvnoa2O9LOyTc"

BAD_WORDS = ["mc", "bc", "madarchod", "bhenchod"]

warns = {}
user_messages = {}

async def is_admin(chat_id, user_id, context):

    admins = await context.bot.get_chat_administrators(chat_id)

    for admin in admins:
        if admin.user.id == user_id:
            return True

    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🔥 SPYYT MODERATION BOT ACTIVE"
    )

async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.lower()

    user = update.effective_user

    chat_id = update.effective_chat.id

    if await is_admin(chat_id, user.id, context):
        return

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

        return

    if re.search(r"(https?://|t\.me/)", text):

        await update.message.delete()

        return

    for word in BAD_WORDS:

        if word in text:

            await update.message.delete()

            warns[user.id] = warns.get(user.id, 0) + 1

            if warns[user.id] >= 3:

                await context.bot.ban_chat_member(
                    chat_id,
                    user.id
                )

                warns[user.id] = 0

                return

            await context.bot.restrict_chat_member(
                chat_id,
                user.id,
                ChatPermissions(
                    can_send_messages=False
                ),
                until_date=update.message.date + timedelta(hours=2)
            )

            await context.bot.send_message(
                chat_id,
                f"🚫 {user.first_name} muted."
            )

            return

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        moderate
    )
)

print("BOT RUNNING")

app.run_polling()