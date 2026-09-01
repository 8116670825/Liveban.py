import logging
import sys
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from telegram.constants import ChatMemberStatus

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Ultra-Pro Live Stream Anti-Premium Bot is running successfully!"

@flask_app.route('/healthz')
def health_check():
    return "OK", 200

def run_flask():
    try:
        flask_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask background server error: {e}", file=sys.stderr)

def keep_alive():
    try:
        t = Thread(target=run_flask, daemon=True)
        t.start()
    except Exception as e:
        print(f"Thread initialization error: {e}", file=sys.stderr)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8716958222:AAGwJB4bjQhcexbEo_rEdKAeZ-CwBwQzMok"
OWNER_USER_ID = 8064395854  

async def handle_live_stream_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update or not update.chat_member:
            return

        chat_member_update = update.chat_member
        chat_id = chat_member_update.chat.id
        new_member = chat_member_update.new_chat_member
        
        if not new_member or not new_member.user:
            return

        user = new_member.user

        if user.id == OWNER_USER_ID:
            logger.info(f"[ULTRA-PRO SAFE] Owner bypass active for ID: {user.id} ({user.full_name})")
            return

        if new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]:
            try:
                member_info = await context.bot.get_chat_member(chat_id, user.id)
                if member_info and member_info.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                    logger.info(f"[ULTRA-PRO SAFE] Admin bypass active for ID: {user.id} ({user.full_name})")
                    return
            except Exception as admin_err:
                logger.warning(f"Admin check bypass warning: {admin_err}")

            if getattr(user, "is_premium", False):
                try:
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                    logger.warning(f"[ULTRA-FAST BAN EXECUTED] Premium user removed instantly: {user.full_name} (ID: {user.id})")
                except Exception as ban_err:
                    logger.error(f"Failed to ban premium user {user.id}: {ban_err}")
            else:
                logger.info(f"[ALLOWED] Non-premium user permitted: {user.full_name} (ID: {user.id})")

    except Exception as e:
        logger.error(f"Error inside ultra-pro live handler: {e}", exc_info=True)

def main():
    keep_alive()
    logger.info("Keep-alive active. Initializing Ultra-Pro Telegram Bot...")

    try:
        telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
        telegram_app.add_handler(ChatMemberHandler(handle_live_stream_entry, ChatMemberHandler.CHAT_MEMBER))

        logger.info("Ultra-Pro Anti-Premium Bot polling started with zero-error framework...")
        
        telegram_app.run_polling(
            allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER],
            drop_pending_updates=True
        )
    except Exception as e:
        logger.critical(f"Fatal application crash: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
    
