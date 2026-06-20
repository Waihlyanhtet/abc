import telebot
import asyncio
import aiohttp
import base64
import re
import time
import json
import random
import cv2
import numpy as np
import ddddocr
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone

BOT_TOKEN = "8983136063:AAESNF_iu11s3PddSrIvHXCOzC-i6K-1wMk"
bot = telebot.TeleBot(BOT_TOKEN)

# User data storage
user_data = {}

# ---------- bbb.py မှ အတိအကျ functions (အထက်ပါအတိုင်း) ----------
# [NOTE: Minute_to_Hour, Code_Expires_Date, _ocr, _ocr_sync, Captcha_Text, Captcha_Image, Varify_Captcha, get_mac, replace_mac, get_session_id, perform_check တို့ကို ယခင်အဖြေမှ အတိအကျ ကူးယူထည့်ပါ။ နေရာလွတ်ကန့်သတ်ချက်ကြောင့် ဤနေရာတွင် ထပ်မရေးတော့ပါ။]

# ---------- Menu keyboards ----------
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📥 Set Session URL", callback_data="set_session"),
        InlineKeyboardButton("🔍 Check Single Code", callback_data="check_code"),
        InlineKeyboardButton("📊 Session Info", callback_data="session_info"),
        InlineKeyboardButton("❌ Clear Session", callback_data="clear_session")
    )
    return markup

def back_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu"))
    return markup

# ---------- Callback handlers ----------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    if call.data == "set_session":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "📥 *Session URL ကို ထည့်ပါ:*\n\nဥပမာ:\n`https://portal-as.ruijienetworks.com/...?sessionId=XXXXX&mac=...`", parse_mode="Markdown", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_session_url)
    
    elif call.data == "check_code":
        bot.answer_callback_query(call.id)
        if chat_id not in user_data or 'session_url' not in user_data[chat_id]:
            bot.send_message(chat_id, "❌ *အရင်ဆုံး Session URL ကို သတ်မှတ်ပါ။*", reply_markup=main_menu(), parse_mode="Markdown")
            return
        msg = bot.send_message(chat_id, "🔍 *Voucher Code ကို ထည့်ပါ:*\n\nဥပမာ:\n`686382`", parse_mode="Markdown", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_check_code)
    
    elif call.data == "session_info":
        bot.answer_callback_query(call.id)
        if chat_id in user_data and 'session_url' in user_data[chat_id]:
            # Extract session_id from URL
            match = re.search(r'[?&]sessionId=([a-zA-Z0-9]+)', user_data[chat_id]['session_url'])
            session_id = match.group(1) if match else "Unknown"
            bot.send_message(chat_id, f"📊 *Session Info*\n\nSession ID: `{session_id}`\nURL: `{user_data[chat_id]['session_url'][:80]}...`", reply_markup=main_menu(), parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ Session မရှိသေးပါ။", reply_markup=main_menu())
    
    elif call.data == "clear_session":
        bot.answer_callback_query(call.id)
        if chat_id in user_data:
            user_data.pop(chat_id)
        bot.send_message(chat_id, "✅ Session ကို ဖျက်ပြီးပါပြီ။", reply_markup=main_menu())
    
    elif call.data == "back_menu":
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🤖 *Voucher Checker Bot*\n\nအောက်ပါ menu မှ ရွေးချယ်ပါ။", chat_id, call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")

# ---------- Step handlers ----------
def process_session_url(message):
    chat_id = message.chat.id
    url = message.text.strip()
    
    # Validate URL has sessionId
    if not re.search(r'[?&]sessionId=[a-zA-Z0-9]+', url):
        bot.send_message(chat_id, "❌ *Session URL မှ sessionId ကို ရှာမတွေ့ပါ။*\n\nပုံစံ: `?sessionId=XXXXX`", reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    # Verify session is valid
    status_msg = bot.send_message(chat_id, "⏳ Session အား စစ်ဆေးနေပါသည်...")
    if not asyncio.run(verify_session_async(url)):
        bot.edit_message_text("❌ *Session ID မမှန်ကန်ပါ။* ထပ်မံစမ်းပါ။", chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    user_data[chat_id] = {'session_url': url}
    bot.edit_message_text(
        f"✅ *Session သိမ်းဆည်းပြီးပါပြီ။*\n\nSession ID: `{re.search(r'[?&]sessionId=([a-zA-Z0-9]+)', url).group(1)}`\n\n/start မှ menu ဖွင့်ပါ။",
        chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown"
    )

def process_check_code(message):
    chat_id = message.chat.id
    code = message.text.strip()
    
    if not code.isdigit() or len(code) < 6:
        bot.send_message(chat_id, "❌ *Code သည် အနည်းဆုံး ၆ လုံးရှိသော ဂဏန်းဖြစ်ရမည်။*", reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    session_url = user_data[chat_id]['session_url']
    
    # Send processing status
    status_msg = bot.send_message(chat_id, "⏳ စစ်ဆေးနေပါသည်... (captcha ဖြေရှင်းခြင်း အပါအဝင်)")
    
    # Run async check
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(perform_check(session_url, code))
        loop.close()
    except Exception as e:
        bot.edit_message_text(f"❌ အမှားဖြစ်သည်: {str(e)}", chat_id, status_msg.message_id, reply_markup=main_menu())
        return
    
    # Format result
    if result.get("status") == "success":
        reply_text = f"✅ *Success*\n\n🎫 `{code}`\n   {result.get('expire', '')}"
        bot.edit_message_text(reply_text, chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")
    elif result.get("status") == "limited":
        reply_text = f"⚠️ *Limited*\n\n🎫 `{code}`\n   {result.get('expire', '')}"
        bot.edit_message_text(reply_text, chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")
    elif result.get("status") == "failed":
        reply_text = f"❌ *မအောင်မြင်ပါ*\n\nResponse: `{json.dumps(result.get('response', {}), indent=2)[:300]}`"
        bot.edit_message_text(reply_text, chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        bot.edit_message_text(f"❌ *Unknown result*\n\n```json\n{json.dumps(result, indent=2)[:300]}\n```", chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")

# ---------- Async session verification ----------
async def verify_session_async(session_url):
    try:
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(connector=connector, connector_owner=False, timeout=timeout) as session:
            session_id = await get_session_id(session, session_url, None)
            if not session_id:
                return False
            # Try to get captcha image to verify
            image = await Captcha_Image(session, session_id)
            return len(image) > 1000  # Captcha image should be > 1KB
    except:
        return False

# ---------- Start command ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "🤖 *Voucher Checker Bot*\n\nအောက်ပါ menu မှ ရွေးချယ်ပါ။",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ---------- Main ----------
if __name__ == '__main__':
    print("🤖 Bot starting...")
    bot.infinity_polling()