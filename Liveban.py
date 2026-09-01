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

# 1. प्रोफेशनल लॉगिंग सेटअप (ताकि रेंडर कंसोल में हर एक एक्टिविटी साफ़ दिखे)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. फ्लास्क हेल्थ-चेक सर्वर (रेंडर के लिए अनिवार्य)
flask_app = Flask(__name__)

@flask_app.route('/')
def home() -> str:
    return "Bot is active and running smoothly!", 200

@flask_app.route('/healthz')
def health_check() -> str:
    return "OK", 200

def run_flask() -> None:
    """रेंडर के दिए गए डायनामिक पोर्ट पर फ्लास्क सर्वर को बैकग्राउंड में चलाना"""
    try:
        port = int(os.environ.get("PORT", 10000))
        flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")

def keep_alive() -> None:
    """फ्लास्क थ्रेड इनिशियलाइज़र"""
    try:
        thread = Thread(target=run_flask, daemon=True)
        thread.start()
        logger.info("Keep-alive background server started successfully.")
    except Exception as e:
        logger.error(f"Failed to start keep-alive thread: {e}")

# 3. कॉन्फिगरेशन कॉन्सटेंट (क्रेडेंशियल्स)
BOT_TOKEN = "8716958222:AAGwJB4bjQhcexbEo_rEdKAeZ-CwBwQzMok"
OWNER_USER_ID = 8064395854  

# डुप्लीकेट प्रोसेसिंग रोकने और सुपर-फास्ट स्पीड के लिए इन-मेमोरी सेट कैश
checked_users_cache = set()

async def ultra_fast_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    अल्ट्रा-फास्ट, नैनो-सेकंड लाइव चेकिंग लॉजिक:
    - ओनर और एडमिन को पूर्ण सुरक्षा प्रदान करता है।
    - प्रीमियम यूजर मिलते ही उसे बिना किसी देरी के तुरंत बैन करता है।
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

        # सुरक्षा और स्पीड ऑप्टिमाइज़ेशन: ओनर या पहले से चेक किए गए यूजर को बाईपास करें
        if user_id == OWNER_USER_ID or user_id in checked_users_cache:
            return

        # कैश में जोड़ें ताकि अगली बार लोड न पड़े
        checked_users_cache.add(user_id)

        # एडमिन या ओनर स्टेटस चेक
        status = new_member.status
        if status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return

        # डायरेक्ट प्रीमियम चेक (बिना अतिरिक्त API डिले के)
        if getattr(user, "is_premium", False):
            try:
                await context.bot.ban_chat_member(chat_id=chat.id, user_id=user_id)
                logger.info(f"Successfully banned premium user ID: {user_id} from chat ID: {chat.id}")
            except Exception as ban_error:
                logger.error(f"Could not ban user {user_id}: {ban_error}")

    except Exception as e:
        logger.error(f"Error inside ultra_fast_checker: {e}")

def main() -> None:
    """मुख्य बोट रनर लूप - ऑटो-रिकवरी और फॉल्ट टॉलरेन्स के साथ"""
    keep_alive()
    time.sleep(1)

    logger.info("Initializing Telegram Bot Application...")
    
    while True:
        try:
            telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
            
            # सिर्फ आवश्यक चैट मेंबर अपडेट्स को रजिस्टर करना
            telegram_app.add_handler(ChatMemberHandler(ultra_fast_checker, ChatMemberHandler.CHAT_MEMBER))
            
            logger.info("Bot is starting polling now...")
            telegram_app.run_polling(
                allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER],
                drop_pending_updates=True,
                close_loop=False
            )
        except Conflict:
            logger.warning("Conflict error detected (another instance might be running). Retrying in 10 seconds...")
            time.sleep(10)
        except (NetworkError, TimedOut):
            logger.warning("Network connection lost or timed out. Reconnecting in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            logger.critical(f"Critical unexpected error in main loop: {e}. Restarting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
    
