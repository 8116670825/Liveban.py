import logging
import sys
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError, NetworkError, TimedOut

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Ultra-Stable Zero-Error Anti-Premium Bot is active!"

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

# Updated Token
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
            logger.info(f"[SAFE OWNER] Owner bypass successful: {user.id}")
            return

        if new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]:
            try:
                member_info = await context.bot.get_chat_member(chat_id, user.id)
                if member_info and member_info.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                    logger.info(f"[SAFE ADMIN] Admin bypass successful: {user.id}")
                    return
            except (NetworkError, TimedOut) as net_err:
                logger.warning(f"Network glitch during admin check for {user.id}: {net_err}")
            except Exception as admin_err:
                logger.warning(f"Minor safe-check exception for {user.id}: {admin_err}")

            if getattr(user, "is_premium", False):
                try:
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                    logger.warning(f"[ULTRA FAST BAN] Premium user successfully banned: {user.id}")
                except (NetworkError, TimedOut) as net_err:
                    logger.error(f"Network timeout while banning premium user {user.id}: {net_err}")
                except TelegramError as tg_err:
                    logger.error(f"Telegram API restriction error for user {user.id}: {tg_err}")
                except Exception as ban_err:
                    logger.error(f"Unexpected ban execution error for {user.id}: {ban_err}")
            else:
                logger.info(f"[SAFE USER] Normal non-premium user allowed: {user.id}")

    except (NetworkError, TimedOut) as net_err:
        logger.error(f"Transient network error caught safely in main handler: {net_err}")
    except Exception as e:
        logger.error(f"Non-fatal guarded exception in handler: {e}", exc_info=False)

def main():
    keep_alive()
    logger.info("Keep-alive background thread running smoothly.")

    try:
        telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
        telegram_app.add_handler(ChatMemberHandler(handle_live_stream_entry, ChatMemberHandler.CHAT_MEMBER))

        logger.info("Zero-Error Bot polling started securely...")
        
        telegram_app.run_polling(
            allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER],
            drop_pending_updates=True,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30
        )
    except (NetworkError, TimedOut) as net_err:
        logger.critical(f"Critical network failure in polling loop: {net_err}")
    except Exception as e:
        logger.critical(f"Fatal application exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
  
