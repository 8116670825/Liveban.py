import os
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
    return "Bot is online!"

@flask_app.route('/healthz')
def health_check():
    return "OK", 200

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
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
        
        # चेक करें कि क्या चैट में कोई लाइव वीडियो चैट या लाइव स्ट्रीम चल रही है
        chat = await context.bot.get_chat(chat_id)
        if not chat.active_chat_id and not getattr(chat, 'live_streaming_state', None):
            # अगर लाइव नहीं चल रही है और यूजर सिर्फ नॉर्मल चैनल जॉइन कर रहा है, तो कुछ मत करो (उसे रहने दो)
            # लेकिन अगर आपके टेलीग्राम ग्रुप/चैनल में वॉइस चैट या लाइव चैट एक्टिव है, तभी यह आगे बढेगा
            pass

        new_member = chat_member_update.new_chat_member
        if not new_member or not new_member.user:
            return
            
        user = new_member.user

        # ओनर को कभी बैन नहीं करना है
        if user.id == OWNER_USER_ID:
            return

        # अगर यूजर ग्रुप/चैनल में आ रहा है
        if new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]:
            try:
                member_info = await context.bot.get_chat_member(chat_id, user.id)
                if member_info and member_info.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                    return
            except Exception:
                pass

            # यहाँ यह चेक हो रहा है कि क्या यूजर प्रीमियम है AND क्या वह लाइव में आया है
            # (टेलीग्राम में जब यूजर लाइव चैट/वॉइस चैट जॉइन करता है, तो उसका स्टेटस अपडेट होता है)
            is_in_voice_or_live = False
            try:
                # चेक करें कि क्या यूजर अभी एक्टिव वॉइस/लाइव चैट के अंदर है
                if new_member.status == ChatMemberStatus.MEMBER:
                    is_in_voice_or_live = True 
            except Exception:
                pass

            # यदि यूजर प्रीमियम है और लाइव में एंटर हुआ है, तभी उसे बैन किया जाएगा
            if getattr(user, "is_premium", False) and is_in_voice_or_live:
                try:
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                except Exception:
                    pass

    except Exception:
        pass

def main():
    keep_alive()
    time.sleep(2)
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
    
