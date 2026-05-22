from telegram import Update, ChatPermissions
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

from datetime import time as dtime, timedelta
import logging
import time
import re
import os

# =====================================================
# CONFIG
# =====================================================

TOKEN = os.getenv("TOKEN")

BAD_WORDS = [
    "mc",
    "bc",
    "madarchod",
    "bhenchod",
    "fuck",
    "shit",
    "bkl"
]

MAX_WARNS = 3
MUTE_HOURS = 2

FLOOD_LIMIT = 5
FLOOD_TIME = 10

ANTI_RAID_JOIN_LIMIT = 5
ANTI_RAID_TIME = 20

LOG_CHANNEL_ID = -1003709832725

LOCK_HOUR = 0
LOCK_MINUTE = 30

UNLOCK_HOUR = 6
UNLOCK_MINUTE = 0

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =====================================================
# DATABASE
# =====================================================

warns = {}
user_messages = {}
recent_joins = {}

# =====================================================
# ADMIN CHECK
# =====================================================

def is_admin(chat_id, user_id, context):

    admins = context.bot.get_chat_administrators(chat_id)

    for admin in admins:

        if admin.user.id == user_id:
            return True

    return False

# =====================================================
# START
# =====================================================

def start(update: Update, context: CallbackContext):

    update.message.reply_text(
        "🔥 SPYYT SECURITY BOT ACTIVE"
    )

# =====================================================
# WARNS
# =====================================================

def warnings(update: Update, context: CallbackContext):

    user_id = update.effective_user.id

    count = warns.get(user_id, 0)

    update.message.reply_text(
        f"⚠️ Your warnings: {count}"
    )

# =====================================================
# RESET WARN
# =====================================================

def resetwarn(update: Update, context: CallbackContext):

    if not update.message.reply_to_message:
        return

    admin = update.effective_user

    chat_id = update.effective_chat.id

    if not is_admin(chat_id, admin.id, context):
        return

    target = update.message.reply_to_message.from_user

    warns[target.id] = 0

    update.message.reply_text(
        f"✅ Warnings reset for {target.first_name}"
    )

# =====================================================
# LOCK GROUP
# =====================================================

def lock_group(context: CallbackContext):

    job = context.job

    chat_id = job.context

    context.bot.set_chat_permissions(
        chat_id,
        ChatPermissions(
            can_send_messages=False
        )
    )

    context.bot.send_message(
        chat_id,
        "🔒 Group locked automatically."
    )

# =====================================================
# UNLOCK GROUP
# =====================================================

def unlock_group(context: CallbackContext):

    job = context.job

    chat_id = job.context

    context.bot.set_chat_permissions(
        chat_id,
        ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )

    context.bot.send_message(
        chat_id,
        "🔓 Group unlocked automatically."
    )

# =====================================================
# SETUP AUTO LOCK
# =====================================================

def setup_jobs(updater):

    jq = updater.job_queue

    # ADD YOUR GROUP ID HERE

    GROUP_ID = -1002551061136

    jq.run_daily(
        lock_group,
        time=dtime(hour=LOCK_HOUR, minute=LOCK_MINUTE),
        context=GROUP_ID
    )

    jq.run_daily(
        unlock_group,
        time=dtime(hour=UNLOCK_HOUR, minute=UNLOCK_MINUTE),
        context=GROUP_ID
    )

# =====================================================
# ANTI RAID
# =====================================================

def anti_raid(update: Update, context: CallbackContext):

    chat_id = update.effective_chat.id

    now = time.time()

    if chat_id not in recent_joins:
        recent_joins[chat_id] = []

    recent_joins[chat_id].append(now)

    recent_joins[chat_id] = [
        t for t in recent_joins[chat_id]
        if now - t < ANTI_RAID_TIME
    ]

    if len(recent_joins[chat_id]) >= ANTI_RAID_JOIN_LIMIT:

        context.bot.set_chat_permissions(
            chat_id,
            ChatPermissions(
                can_send_messages=False
            )
        )

        context.bot.send_message(
            chat_id,
            "🚨 RAID DETECTED\n🔒 Group locked automatically."
        )

        context.bot.send_message(
            LOG_CHANNEL_ID,
            f"🚨 RAID ALERT IN {chat_id}"
        )

# =====================================================
# MAIN MODERATION
# =====================================================

def moderate(update: Update, context: CallbackContext):

    if not update.message:
        return

    user = update.effective_user

    chat_id = update.effective_chat.id

    # ==============================================
    # NEW MEMBERS
    # ==============================================

    if update.message.new_chat_members:

        anti_raid(update, context)

        return

    # ==============================================
    # ONLY TEXT
    # ==============================================

    if not update.message.text:
        return

    text = update.message.text.lower()

    # ==============================================
    # ADMIN BYPASS
    # ==============================================

    if is_admin(chat_id, user.id, context):
        return

    # ==============================================
    # ANTI FORWARD
    # ==============================================

    if update.message.forward_date:

        try:

            update.message.delete()

            context.bot.send_message(
                chat_id,
                "🚫 Forwarded messages are not allowed."
            )

        except:
            pass

        return

    # ==============================================
    # MEDIA BLOCKER
    # ==============================================

    if (
        update.message.photo
        or update.message.video
        or update.message.document
        or update.message.audio
        or update.message.voice
        or update.message.sticker
    ):

        try:

            update.message.delete()

            context.bot.send_message(
                chat_id,
                "🚫 Media messages are blocked."
            )

        except:
            pass

        return

    # ==============================================
    # FLOOD DETECTION
    # ==============================================

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

            context.bot.send_message(
                LOG_CHANNEL_ID,
                f"🚨 Flood detected from {user.first_name}"
            )

        except:
            pass

        return

    # ==============================================
    # LINK BLOCKER
    # ==============================================

    if re.search(r"(https?://|t\.me/)", text):

        try:

            update.message.delete()

            context.bot.send_message(
                chat_id,
                "🚫 Links are not allowed."
            )

        except:
            pass

        return

    # ==============================================
    # BAD WORD FILTER
    # ==============================================

    for word in BAD_WORDS:

        if word in text:

            try:

                update.message.delete()

                warns[user.id] = warns.get(user.id, 0) + 1

                count = warns[user.id]

                # ==================================
                # BAN
                # ==================================

                if count >= MAX_WARNS:

                    context.bot.ban_chat_member(
                        chat_id,
                        user.id
                    )

                    context.bot.send_message(
                        chat_id,
                        f"⛔ {user.first_name} banned."
                    )

                    context.bot.send_message(
                        LOG_CHANNEL_ID,
                        f"⛔ User banned: {user.first_name}"
                    )

                    warns[user.id] = 0

                    return

                # ==================================
                # MUTE
                # ==================================

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

                context.bot.send_message(
                    LOG_CHANNEL_ID,
                    f"⚠️ Bad word detected from {user.first_name}"
                )

            except:
                pass

            return

# =====================================================
# ERROR
# =====================================================

def error_handler(update, context):

    logger.warning(context.error)

# =====================================================
# MAIN
# =====================================================

def main():

    updater = Updater(
        TOKEN,
        use_context=True
    )

    dp = updater.dispatcher

    setup_jobs(updater)

    # COMMANDS

    dp.add_handler(
        CommandHandler("start", start)
    )

    dp.add_handler(
        CommandHandler("warnings", warnings)
    )

    dp.add_handler(
        CommandHandler("resetwarn", resetwarn)
    )

    # MAIN HANDLER

    dp.add_handler(
        MessageHandler(
            Filters.all,
            moderate
        )
    )

    # ERROR

    dp.add_error_handler(error_handler)

    print("🔥 SPYYT SECURITY BOT RUNNING")

    updater.start_polling(
        drop_pending_updates=True
    )

    updater.idle()

# =====================================================
# START
# =====================================================

if __name__ == "__main__":
    main()
