import logging
import sys
import time
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from telegram.constants import ChatMemberStatus
from telegram.error import NetworkError, TimedOut

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Ultra-Stable Anti-Premium Bot is running!"

@flask_app.route('/healthz')
def health_check():
    return "OK", 200

def run_flask():
    try:
        flask_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except Exception:
        pass

def keep_alive():
    try:
        t = Thread(target=run_flask, daemon=True)
        t.start()
    except Exception:
        pass

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
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
            return

        if new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]:
            try:
                member_info = await context.bot.get_chat_member(chat_id, user.id)
                if member_info and member_info.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                    return
            except Exception:
                pass

            if getattr(user, "is_premium", False):
                try:
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                    logger.warning(f"Banned Premium User: {user.id}")
                except Exception:
                    pass

    except Exception:
        pass

def main():
    keep_alive()
    logger.info("Starting Autonomous Anti-Premium Bot...")

    while True:
        try:
            telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
            telegram_app.add_handler(ChatMemberHandler(handle_live_stream_entry, ChatMemberHandler.CHAT_MEMBER))
            
            logger.info("Bot polling connected successfully.")
            telegram_app.run_polling(
                allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER],
                drop_pending_updates=True,
                close_loop=False
            )
        except (NetworkError, TimedOut) as net_err:
            logger.warning(f"Network timeout/glitch encountered: {net_err}. Reconnecting in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            logger.error(f"Polling exception caught: {e}. Restarting loop in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
    
