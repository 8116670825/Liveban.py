import os
import sys
import logging
import time
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from telegram.constants import ChatMemberStatus
from telegram.error import NetworkError, TimedOut, Conflict

# लॉगिंग सेटअप
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# फ्लास्क हेल्थ-चेक सर्वर (रेंडर के लिए)
flask_app = Flask(__name__)

@flask_app.route('/')
def home() -> str:
    return "Bot is active and running smoothly!", 200

@flask_app.route('/healthz')
def health_check() -> str:
    return "OK", 200

def run_flask() -> None:
    try:
        port = int(os.environ.get("PORT", 10000))
        flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")

def keep_alive() -> None:
    try:
        thread = Thread(target=run_flask, daemon=True)
        thread.start()
    except Exception as e:
        logger.error(f"Keep-alive thread error: {e}")

# क्रेडेंशियल्स
BOT_TOKEN = "8716958222:AAGwJB4bjQhcexbEo_rEdKAeZ-CwBwQzMok"
OWNER_USER_ID = 8064395854  

# सुपर-फास्ट स्पीड और डुप्लीकेट रोकने के लिए कैश
checked_users_cache = set()

async def live_stream_instant_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    यह हैंडलर जॉइन रिक्वेस्ट को बिल्कुल हाथ नहीं लगाएगा (यानी रिक्वेस्ट आपके कंट्रोल में रहेगी)।
    लेकिन जैसे ही कोई यूजर चैनल या लाइव गतिविधि में आएगा, बॉट प्रीमियम चेक करके 0.1 सेकंड में बैन कर देगा।
    """
    try:
        if not update or not update.chat_member:
            return

        chat_member_update = update.chat_member
        chat = chat_member_update.chat
        new_member = chat_member_update.new_chat_member
        
        if not chat or not new_member or not new_member.user:
            return

        user = new_member.user
        user_id = user.id

        # ओनर और पहले से चेक किए गए यूजर्स को बाईपास करें
        if user_id == OWNER_USER_ID or user_id in checked_users_cache:
            return

        checked_users_cache.add(user_id)

        # एडमिन या ओनर को पूर्ण सुरक्षा
        status = new_member.status
        if status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return

        # डायरेक्ट प्रीमियम चेक और इंस्टेंट बैन (0.1 सेकंड के अंदर)
        if getattr(user, "is_premium", False):
            try:
                await context.bot.ban_chat_member(chat_id=chat.id, user_id=user_id)
                logger.info(f"Instant-banned premium user ID: {user_id} from chat ID: {chat.id}")
            except Exception as ban_error:
                logger.error(f"Could not ban user {user_id}: {ban_error}")

    except Exception as e:
        logger.error(f"Error inside live_stream_instant_ban: {e}")

def main() -> None:
    keep_alive()
    time.sleep(1)

    logger.info("Starting Telegram Bot Application...")
    
    while True:
        try:
            telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
            
            # ध्यान दें: हमने यहाँ ChatJoinRequestHandler को पूरी तरह हटा दिया है, 
            # ताकि बॉट आपकी मर्जी के खिलाफ कोई रिक्वेस्ट ऑटो-अप्रूव या टच न करे।
            telegram_app.add_handler(ChatMemberHandler(live_stream_instant_ban, ChatMemberHandler.CHAT_MEMBER))
            
            telegram_app.run_polling(
                allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER],
                drop_pending_updates=True,
                close_loop=False
            )
        except Conflict:
            logger.warning("Conflict error detected. Retrying in 10 seconds...")
            time.sleep(10)
        except (NetworkError, TimedOut):
            logger.warning("Network connection lost. Reconnecting...")
            time.sleep(3)
        except Exception as e:
            logger.critical(f"Critical error: {e}. Restarting...")
            time.sleep(5)

if __name__ == "__main__":
    main()
    
