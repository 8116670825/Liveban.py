import sys
import time
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from telegram.constants import ChatMemberStatus
from telegram.error import NetworkError, TimedOut, Conflict

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Ultra-Pro Anti-Premium Bot is online!"

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
                except Exception:
                    pass

    except Exception:
        pass

def main():
    keep_alive()
    
    # रेंडर पर रीस्टार्ट के वक्त पुराने सर्वर को हटाने के लिए सुरक्षित इंतज़ार
    time.sleep(6)
    
    while True:
        try:
            telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
            telegram_app.add_handler(ChatMemberHandler(handle_live_stream_entry, ChatMemberHandler.CHAT_MEMBER))
            
            telegram_app.run_polling(
                allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER],
                drop_pending_updates=True,
                close_loop=False
            )
        except Conflict:
            time.sleep(10)
        except (NetworkError, TimedOut):
            time.sleep(4)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    main()
    
