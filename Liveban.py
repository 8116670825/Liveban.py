import os
import time
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from telegram.constants import ChatMemberStatus
from telegram.error import NetworkError, TimedOut, Conflict

# Gunicorn और Render के लिए सही सेटअप
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Ultra-Pro Anti-Premium Bot is online!"

@flask_app.route('/healthz')
def health_check():
    return "OK", 200

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
    # जब सीधे रन हो (लोकल या gunicorn के थ्रू)
    main()
    
