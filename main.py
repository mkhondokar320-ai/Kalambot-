import telebot
from telebot import types
import json
import os
import time
import logging
from datetime import datetime
import requests
import hashlib
import re
from collections import deque
import threading

# --- ⚙️ ADVANCED CONFIGURATION & LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - 𝐈𝐍𝐒 𝐇𝐔𝐁𝐄 - %(levelname)s - %(message)s')

# Telegram Bot Token & Admin
API_TOKEN = '8364756844:AAFGuS6NTl7MzSJt3TjuD4OoMSTXO4KFjYY'
MAIN_ADMIN_ID = 7087989353

# ================= 🚀 DUAL API CONFIGURATION =================
# API 1
API_1_URL = "http://203.161.58.20/api/functions/agent-api"
API_1_KEY = "sk_b331fc25989e09a87e32cd047f13d4ff346696b821c556cb642075d293f8ee35"

# API 2
API_2_URL = "http://147.135.212.197/crapi/had/viewstats"
API_2_TOKEN = "RVFRQTRSQnxgk2NDSJiAZERTmIdSa49rXIB3fYJ_YVJXmICIdIyB"

POLL_INTERVAL = 5
FETCH_RECORDS = 50

# --- 📢 FORCE JOIN CHANNELS ---
FORCE_JOIN_CHANNELS = [
    {"name": "🌟 𝑴𝒂𝒊𝒏 𝑪𝒉𝒂𝒏𝒏𝒆𝒍", "url": "https://t.me/Minhaz_Official", "chat_id": "@Minhaz_Official"},
    {"name": "💬 𝑶𝑻𝑷 𝑮𝒓𝒐𝒖𝒑", "url": "https://t.me/kalamifxvvv223", "chat_id": "@kalamifxvvv223"},
    {"name": "🛡️ 𝑩𝒂𝒄𝒌𝒖𝒑 𝑪𝒉𝒂𝒏𝒏𝒆𝒍", "url": "https://t.me/becup3290", "chat_id":"@becup3290"} 
]

bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')
DB_FILE = 'ins_hube_database.json'
db_lock = threading.RLock()

admin_sessions = {}
user_sessions = {}

# ================= 🔥 FANCY MENU BUTTONS =================
BTN_GET_NUM = "📞 𝑮𝒆𝒕 𝑵𝒖𝒎𝒃𝒆𝒓"
BTN_PROFILE = "📋 𝑷𝒓𝒐𝒇𝒊𝒍𝒆"
BTN_WALLET = "💳 𝑾𝒂𝒍𝒍𝒆𝒕 (𝑾𝒊𝒕𝒉𝒅𝒓𝒂𝒘)"
BTN_SUPPORT = "🎧 𝑺𝒖𝒑𝒑𝒐𝒓𝒕"
BTN_ADMIN = "👑 𝑨𝒅𝒎𝒊𝒏 𝑷𝒂𝒏𝒆𝒍"

def bold_text(text):
    text = str(text).upper()
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    bold = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"
    return text.translate(str.maketrans(normal, bold))

# ================= 💾 DATABASE MANAGER =================
class InsDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.data = self.load()

    def load(self):
        if not os.path.exists(self.db_path):
            default_data = {
                "admins": [MAIN_ADMIN_ID, 7833093821, 6820798198],
                "banned_users": [],
                "users": {},
                "services": {},
                "withdraw_requests": {},
                "settings": {
                    "bot_status": True,
                    "maintenance_msg": "🛠️ <b>বট রক্ষণাবেক্ষণ চলছে!</b>\nকিছুক্ষণ পরে আবার চেষ্টা করুন।",
                    "welcome_msg": "🌟 স্বাগতম 𝑰𝑵𝑺 𝑯𝑼𝑩𝑬 তে!",
                    "currency": "৳",
                    "cooldown_time": 10,
                    "min_withdraw": 50.0
                }
            }
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4)
            return default_data

        with open(self.db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            settings = data.get("settings", {})
            if "cooldown_time" not in settings: settings["cooldown_time"] = 10
            if "min_withdraw" not in settings: settings["min_withdraw"] = 50.0
            data["settings"] = settings
            if "withdraw_requests" not in data: data["withdraw_requests"] = {}
            if isinstance(data.get("withdraw_requests"), list): data["withdraw_requests"] = {}
            
            if "admins" not in data: data["admins"] = []
            if MAIN_ADMIN_ID not in data["admins"]: data["admins"].append(MAIN_ADMIN_ID)
                
            return data

    def save(self):
        with db_lock:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)

    def get_user(self, user_id):
        uid = str(user_id)
        default_user = {
            "balance": 0.0,
            "total_earned": 0.0,
            "total_spent": 0.0,
            "numbers_taken": 0,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_number_time": 0.0,
            "active_numbers": None
        }
        with db_lock:
            if uid not in self.data["users"]:
                self.data["users"][uid] = default_user
                self.save()
            else:
                user = self.data["users"][uid]
                for key, val in default_user.items():
                    if key not in user:
                        user[key] = val
                self.save()
            return self.data["users"][uid]

db = InsDatabase(DB_FILE)

# ================= 🎛 KEYBOARDS =================
def ins_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton(BTN_GET_NUM))
    markup.add(types.KeyboardButton(BTN_PROFILE), types.KeyboardButton(BTN_WALLET))
    markup.add(types.KeyboardButton(BTN_SUPPORT))
    if user_id in db.data["admins"]:
        markup.add(types.KeyboardButton(BTN_ADMIN))
    return markup

def inline_back_btn(callback_data="home"):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"🔙 𝑩𝒂𝒄𝒌", callback_data=callback_data))
    return markup

def get_admin_panel_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(f"➕ ADD NUMBERS", callback_data="adm_add_country"),
        types.InlineKeyboardButton(f"📋 MANAGE NUMS", callback_data="adm_manage_num")
    )
    markup.add(
        types.InlineKeyboardButton(f"📁 ADD CATEGORY", callback_data="adm_add_service"),
        types.InlineKeyboardButton(f"🗑 DEL CATEGORY", callback_data="adm_del_cat_list")
    )
    markup.add(
        types.InlineKeyboardButton(f"⏳ SET COOLDOWN", callback_data="adm_cooldown"),
        types.InlineKeyboardButton(f"💳 MIN WITHDRAW", callback_data="adm_min_wd")
    )
    markup.add(
        types.InlineKeyboardButton(f"💸 WITHDRAW REQS", callback_data="adm_withdraw_reqs"),
        types.InlineKeyboardButton(f"📢 BROADCAST", callback_data="adm_broadcast")
    )
    markup.add(
        types.InlineKeyboardButton(f"⚙️ SETTINGS", callback_data="adm_settings"),
        types.InlineKeyboardButton(f"❌ CLOSE PANEL", callback_data="close_ui")
    )
    return markup

# ================= 🚀 DUAL API OTP ENGINE & INBOX SENDER =================
def extract_otp(message):
    match = re.search(r'\b(\d{3,4}[\s-]?\d{3,4})\b', message)
    if match: return re.sub(r'[-\s]', '', match.group(1))
    match2 = re.search(r'\b\d{4,8}\b', message)
    return match2.group(0) if match2 else "Copy"

def send_user_otp(chat_id, number, svc_name, c_name, message, otp_code_api):
    otp_code = otp_code_api if otp_code_api else extract_otp(message)
    
    text = f"🌟 <b>𝑰𝑵𝑺 𝑯𝑼𝑩𝑬 𝑶𝑻𝑷 𝑹𝑬𝑪𝑬𝑰𝑽𝑬𝑫</b> 🌟\n\n"
    text += f"💎 <b>𝑺𝒆𝒓𝒗𝒊𝒄𝒆:</b> {svc_name.upper()}\n"
    text += f"🌍 <b>𝑪𝒐𝒖𝒏𝒕𝒓𝒚:</b> {c_name.upper()}\n\n"
    
    text += f"┌───────── • 🔔 • ─────────┐\n"
    text += f"    <b>আপনার নতুন ওটিপি এসেছে!</b>\n"
    text += f"└──────────────────────────┘\n\n"
    text += f"✨ 𝑷𝒐𝒘𝒆𝒓𝒆𝒅 𝒃𝒚 <a href='https://t.me/Minhaz_Official'>𝐒𝐊𝐘</a> ✨"
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(f"☎️ Num: +{number}", copy_text=types.CopyTextButton(text=str(number))),
        types.InlineKeyboardButton(f"🔑 OTP: {otp_code}", copy_text=types.CopyTextButton(text=otp_code)),
        types.InlineKeyboardButton("📝 𝑭𝒖𝒍𝒍 𝑴𝒆𝒔𝒔𝒂𝒈𝒆", copy_text=types.CopyTextButton(text=message[:256]))
    )
    
    try:
        bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"Failed to send OTP to {chat_id}: {e}")

def background_otp_poller():
    seen_otps = deque(maxlen=4000)
    logging.info("Starting DUAL-API Background Poller & 20-Min Expiry Checker...")
    
    while True:
        try:
            current_time = time.time()
            users_to_expire = []
            
            # --- ⏳ ২০ মিনিট টাইমার চেক ---
            with db_lock:
                for uid, udata in db.data["users"].items():
                    active = udata.get("active_numbers")
                    if active and "buy_time" in active:
                        if current_time - active["buy_time"] > 1200: # 1200 sec = 20 mins
                            users_to_expire.append(uid)
                
                for uid in users_to_expire:
                    active = db.data["users"][uid]["active_numbers"]
                    if active:
                        prev_nums = active.get("nums", [])
                        prev_rate = active.get("otp_rate", 0.0)
                        
                        db.data["users"][uid]["balance"] += (prev_rate * len(prev_nums))
                        db.data["users"][uid]["total_spent"] = max(0, db.data["users"][uid]["total_spent"] - (prev_rate * len(prev_nums)))
                        db.data["users"][uid]["numbers_taken"] = max(0, db.data["users"][uid]["numbers_taken"] - len(prev_nums))
                        
                        svc_name = active.get("svc")
                        c_name = active.get("c")
                        if svc_name in db.data["services"] and c_name in db.data["services"][svc_name]:
                            db.data["services"][svc_name][c_name]["number_list"].extend(prev_nums)
                            db.data["services"][svc_name][c_name]["stock"] += len(prev_nums)

                    db.data["users"][uid]["active_numbers"] = None
                    db.save()
                    try:
                        bot.send_message(uid, "⚠️ <b>আপনার কেনা নাম্বারের মেয়াদ (২০ মিনিট) শেষ হয়ে গেছে!</b>\nটাকা আপনার ব্যালেন্সে রিফান্ড দেওয়া হয়েছে।", parse_mode='HTML')
                    except: pass

            # --- 🌐 DUAL API DATA FETCHING ---
            combined_otps = []

            # 1. API 1 Fetch
            try:
                res1 = requests.get(f"{API_1_URL}/otp", headers={"x-api-key": API_1_KEY}, params={"page": 1, "limit": FETCH_RECORDS}, timeout=10)
                if res1.status_code == 200 and res1.json().get("ok"):
                    for item in res1.json().get("data", []):
                        combined_otps.append({
                            "num": str(item.get("number", "")),
                            "msg": str(item.get("message_text") or item.get("message") or item.get("sms") or "").strip(),
                            "svc": str(item.get("platform", "Service")),
                            "dt": str(item.get("received_at", "time")),
                            "otp_code": str(item.get("otp_code", ""))
                        })
            except Exception as e: logging.error(f"API 1 Fetch Error: {e}")

            # 2. API 2 Fetch
            try:
                res2 = requests.get(API_2_URL, params={"token": API_2_TOKEN, "records": FETCH_RECORDS}, timeout=10)
                if res2.status_code == 200 and res2.json().get("status") == "success":
                    for item in res2.json().get("data", []):
                        combined_otps.append({
                            "num": str(item.get("num", "")),
                            "msg": str(item.get("message", "")).strip(),
                            "svc": str(item.get("cli", "Service")),
                            "dt": str(item.get("dt", "time")),
                            "otp_code": "" 
                        })
            except Exception as e: logging.error(f"API 2 Fetch Error: {e}")

            # --- 🔄 PROCESS COMBINED DATA ---
            combined_otps.reverse() # পুরোনো থেকে নতুন চেক করতে
            
            for otp in combined_otps:
                message = otp["msg"]
                if not message or message.lower() in ['none', 'null', '']:
                    continue
                
                api_num = otp["num"]
                dt = otp["dt"]
                otp_code_api = otp["otp_code"]
                
                raw_string = f"{dt}_{api_num}_{message}"
                otp_id = hashlib.md5(raw_string.encode()).hexdigest()
                
                if otp_id not in seen_otps:
                    seen_otps.append(otp_id)
                    clean_api_num = re.sub(r'\D', '', api_num)
                    
                    matched_uid = None
                    matched_num = None
                    
                    # ডাটাবেজ থেকে নাম্বার মিলিয়ে দেখা হচ্ছে কার ইনবক্সে যাবে
                    with db_lock:
                        for uid, udata in db.data["users"].items():
                            active = udata.get("active_numbers")
                            if active and active.get("nums"):
                                for s_num in active["nums"]:
                                    clean_s = re.sub(r'\D', '', str(s_num))
                                    if clean_s and clean_api_num and (clean_api_num.endswith(clean_s) or clean_s.endswith(clean_api_num)):
                                        matched_uid = uid
                                        matched_num = s_num
                                        break
                            if matched_uid: break
                    
                    if matched_uid:
                        with db_lock:
                            active_info = db.data["users"][matched_uid]["active_numbers"]
                            svc = active_info.get("svc", otp["svc"])
                            c = active_info.get("c", "Country")
                        
                        send_user_otp(matched_uid, matched_num, svc, c, message, otp_code_api)
                        logging.info(f"✅ Dual-API Auto OTP Sent to Inbox: {matched_uid} for number {matched_num}")
                        
                        with db_lock:
                            try:
                                db.data["users"][matched_uid]["active_numbers"]["nums"].remove(matched_num)
                                if len(db.data["users"][matched_uid]["active_numbers"]["nums"]) == 0:
                                    db.data["users"][matched_uid]["active_numbers"] = None
                                db.save()
                            except: pass

        except Exception as e:
            logging.error(f"Poller Error: {e}")
            
        time.sleep(POLL_INTERVAL)

# ================= 🚦 MIDDLEWARE (FORCE JOIN) =================
def check_ban_and_maintenance(obj):
    uid = obj.from_user.id
    chat_id = obj.message.chat.id if isinstance(obj, types.CallbackQuery) else obj.chat.id
    
    if uid in db.data.get("banned_users", []):
        bot.send_message(chat_id, "🚫 <b>You are banned from using 𝑰𝑵𝑺 𝑯𝑼𝑩𝑬.</b>")
        return False
        
    if not db.data["settings"]["bot_status"] and uid not in db.data["admins"]:
        bot.send_message(chat_id, db.data["settings"]["maintenance_msg"])
        return False
        
    if uid not in db.data["admins"]:
        not_joined = False
        for chan in FORCE_JOIN_CHANNELS:
            if chan["chat_id"]:
                try:
                    status = bot.get_chat_member(chan["chat_id"], uid).status
                    if status in ['left', 'kicked']:
                        not_joined = True
                        break
                except:
                    not_joined = True
                    break
                    
        if not_joined:
            if isinstance(obj, types.CallbackQuery) and obj.data == "verify_join":
                bot.answer_callback_query(obj.id, "❌ আপনি এখনো চ্যানেলগুলোতে জয়েন করেননি! সবগুলোতে জয়েন করে আবার ভেরিফাই করুন।", show_alert=True)
                return False
                
            markup = types.InlineKeyboardMarkup(row_width=1)
            for chan in FORCE_JOIN_CHANNELS:
                markup.add(types.InlineKeyboardButton(text=chan["name"], url=chan["url"]))
                
            markup.add(types.InlineKeyboardButton(f"✅ 𝑽𝒆𝒓𝒊𝒇𝒚 𝑱𝒐𝒊𝒏", callback_data="verify_join"))
            
            text = (
                "⚠️ <b>অ্যাক্সেস ডিনাইড!</b>\n\n"
                "বটটি ব্যবহার করতে এবং দ্রুত সার্ভিস পেতে অনুগ্রহ করে আমাদের <b>নিচের চ্যানেল এবং গ্রুপগুলোতে জয়েন করুন</b>।\n\n"
                "<i>সবগুলোতে জয়েন করার পর 'Verify Join' বাটনে ক্লিক করুন।</i>"
            )
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML', disable_web_page_preview=True)
            return False
            
    return True

# ================= 🚀 START & MENUS =================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if not check_ban_and_maintenance(message): return
    user = message.from_user
    udata = db.get_user(user.id)
    welcome = (
        f"🌟 <b>{db.data['settings']['welcome_msg']}</b>\n"
        f"⚡ <i>সবচেয়ে দ্রুত এবং সিকিউর OTP সার্ভিস</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>𝑵𝒂𝒎𝒆:</b> {user.first_name}\n"
        f"🆔 <b>𝑼𝒔𝒆𝒓 𝑰𝒅:</b> <code>{user.id}</code>\n"
        f"💵 <b>𝑩𝒂𝒍𝒂𝒏𝒄𝒆:</b> {db.data['settings']['currency']}{udata['balance']:.2f}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👇 <i>নিচের মেনু থেকে 📞 𝑮𝒆𝒕 𝑵𝒖𝒎𝒃𝒆𝒓 এ ক্লিক করে নাম্বার নিন</i>"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=ins_main_menu(user.id))

@bot.message_handler(commands=['addbal'])
def add_balance(message):
    if message.from_user.id not in db.data["admins"]: return
    try:
        parts = message.text.split()
        target_uid = parts[1]
        amount = float(parts[2])
        with db_lock:
            if target_uid not in db.data["users"]:
                db.get_user(target_uid) 
            db.data["users"][target_uid]["balance"] += amount
            db.save()
        bot.send_message(message.chat.id, f"✅ Successfully added {amount} to user {target_uid}")
        try:
            bot.send_message(target_uid, f"💰 <b>আপনার অ্যাকাউন্টে {amount} {db.data['settings']['currency']} যোগ করা হয়েছে!</b>")
        except: pass
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Usage: /addbal UserID Amount\nExample: /addbal 123456789 500")

@bot.message_handler(func=lambda m: m.text and "𝑷𝒓𝒐𝒇𝒊𝒍𝒆" in m.text)
def user_profile(message):
    if not check_ban_and_maintenance(message): return
    uid = message.from_user.id
    udata = db.get_user(uid)
    msg = (
        f"📋 <b>𝑰𝑵𝑺 𝑯𝑼𝑩𝑬 𝑷𝒓𝒐𝒇𝒊𝒍𝒆 𝑫𝒂𝒔𝒉𝒃𝒐𝒂𝒓𝒅</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 <b>𝑵𝒂𝒎𝒆:</b> {message.from_user.first_name}\n"
        f"🆔 <b>𝑼𝒔𝒆𝒓 𝑰𝒅:</b> <code>{uid}</code>\n"
        f"🏅 <b>𝑺𝒕𝒂𝒕𝒖𝒔:</b> 🟢 𝑺𝒕𝒂𝒏𝒅𝒂𝒓𝒅 𝑴𝒆𝒎𝒃𝒆𝒓\n"
        f"💵 <b>𝑩𝒂𝒍𝒂𝒏𝒄𝒆:</b> {db.data['settings']['currency']}{udata['balance']:.2f}\n"
        f"📱 <b>𝑵𝒖𝒎𝒃𝒆𝒓𝒔 𝑩𝒐𝒖𝒈𝒉𝒕:</b> {udata['numbers_taken']} 𝑻𝒊𝒎𝒆𝒔\n"
        f"📅 <b>𝑱𝒐𝒊𝒏𝒆𝒅 𝑶𝒏:</b> {udata['join_date'][:10]}\n"
    )
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text and "𝑾𝒂𝒍𝒍𝒆𝒕" in m.text)
def wallet_system(message):
    if not check_ban_and_maintenance(message): return
    uid = str(message.from_user.id)
    udata = db.get_user(uid)
    min_wd = db.data["settings"].get("min_withdraw", 50.0)
    msg = (
        f"💳 <b>𝑰𝑵𝑺 𝑯𝑼𝑩𝑬 𝑾𝒂𝒍𝒍𝒆𝒕 (𝑾𝒊𝒕𝒉𝒅𝒓𝒂𝒘)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>𝑪𝒖𝒓𝒓𝒆𝒏𝒕 𝑩𝒂𝒍𝒂𝒏𝒄𝒆:</b> {db.data['settings']['currency']}{udata['balance']:.2f}\n"
        f"📉 <b>𝑴𝒊𝒏𝒊𝒎𝒖𝒎 𝑾𝒊𝒕𝒉𝒅𝒓𝒂𝒘:</b> {db.data['settings']['currency']}{min_wd:.2f}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"💸 𝑾𝒊𝒕𝒉𝒅𝒓𝒂𝒘 𝑩𝒂𝒍𝒂𝒏𝒄𝒆", callback_data="user_withdraw_start"))
    bot.send_message(message.chat.id, msg, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and "𝑺𝒖𝒑𝒑𝒐𝒓𝒕" in m.text)
def support_system(message):
    if not check_ban_and_maintenance(message): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👨‍💻 𝑪𝒐𝒏𝒕𝒂𝒄𝒕 𝑨𝒅𝒎𝒊𝒏", url="https://t.me/Sanra03263"))
    bot.send_message(message.chat.id, "🎧 <b>𝑰𝑵𝑺 𝑯𝑼𝑩𝑬 𝑺𝒖𝒑𝒑𝒐𝒓𝒕</b>\n━━━━━━━━━━━━━━━━━━━━\nযেকোনো প্রয়োজনে সরাসরি ইনবক্সে মেসেজ দিন:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and "𝑨𝒅𝒎𝒊𝒏" in m.text)
def admin_panel(message):
    if message.from_user.id not in db.data["admins"]: return
    bot.send_message(message.chat.id, "👑 <b>অ্যাডমিন কন্ট্রোল প্যানেল</b>\n<i>যেকোনো একটি অপশন সিলেক্ট করুন:</i>", reply_markup=get_admin_panel_markup())

@bot.message_handler(func=lambda m: m.text and "𝑮𝒆𝒕 𝑵𝒖𝒎𝒃𝒆𝒓" in m.text)
def get_number_services(message):
    if not check_ban_and_maintenance(message): return
    uid = str(message.from_user.id)
    udata = db.get_user(uid)
    current_time = time.time()
    cooldown = db.data["settings"].get("cooldown_time", 10)
    time_passed = current_time - udata.get("last_number_time", 0)
    if time_passed < cooldown:
        wait_time = int(cooldown - time_passed)
        bot.send_message(message.chat.id, f"⌛ <b>Please Wait!</b>\nআপনি আরও {wait_time} সেকেন্ড পর নাম্বার নিতে পারবেন।")
        return
    available_services = set()
    for svc, c_dict in db.data["services"].items():
        for c_name, det in c_dict.items():
            if det["stock"] >= det.get("give_amount", 1):
                available_services.add(svc)
    if not available_services:
        bot.send_message(message.chat.id, "⚠️ <b>দুঃখিত!</b> এই মুহূর্তে কোনো সার্ভিস বা নাম্বার স্টকে নেই। কিছুক্ষণ পর চেষ্টা করুন।")
        return
    markup = types.InlineKeyboardMarkup(row_width=2)
    for s in available_services:
        markup.add(types.InlineKeyboardButton(f"📌 {s.upper()}", callback_data=f"ins_s|{s}"))
    bot.send_message(message.chat.id, "👇 <b>প্রথমে সার্ভিস/অ্যাপ সিলেক্ট করুন:</b>", reply_markup=markup)

# ================= 🔘 CALLBACK HANDLER =================
@bot.callback_query_handler(func=lambda call: True)
def handle_ins_callbacks(call):
    uid = str(call.from_user.id)
    udata = db.get_user(uid)

    if call.data == "verify_join":
        if check_ban_and_maintenance(call):
            bot.answer_callback_query(call.id, "✅ ভেরিফিকেশন সফল! এখন বট ব্যবহার করতে পারেন।", show_alert=True)
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            
            user = call.from_user
            welcome = (
                f"🌟 <b>{db.data['settings']['welcome_msg']}</b>\n"
                f"⚡ <i>সবচেয়ে দ্রুত এবং সিকিউর OTP সার্ভিস</i>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>𝑵𝒂𝒎𝒆:</b> {user.first_name}\n"
                f"🆔 <b>𝑼𝒔𝒆𝒓 𝑰𝒅:</b> <code>{user.id}</code>\n"
                f"💵 <b>𝑩𝒂𝒍𝒂𝒏𝒄𝒆:</b> {db.data['settings']['currency']}{udata['balance']:.2f}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👇 <i>নিচের মেনু থেকে 📞 𝑮𝒆𝒕 𝑵𝒖𝒎𝒃𝒆𝒓 এ ক্লিক করে নাম্বার নিন</i>"
            )
            bot.send_message(call.message.chat.id, welcome, reply_markup=ins_main_menu(user.id))

    elif call.data == "btn_copy_info":
        bot.answer_callback_query(call.id, "👆 উপরের নাম্বার বা ওটিপি তে ট্যাপ করলেই কপি হয়ে যাবে!", show_alert=True)

    elif call.data == "close_ui":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass

    elif call.data == "back_to_admin":
        bot.edit_message_text("👑 <b>অ্যাডমিন কন্ট্রোল প্যানেল</b>", call.message.chat.id, call.message.message_id, reply_markup=get_admin_panel_markup())

    elif call.data.startswith("ins_s|"):
        svc_name = call.data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=2)
        has_country = False
        if svc_name in db.data["services"]:
            for c_name, det in db.data["services"][svc_name].items():
                if det["stock"] >= det.get("give_amount", 1):
                    markup.add(types.InlineKeyboardButton(f"{c_name.title()}", callback_data=f"ins_g|{svc_name}|{c_name}"))
                    has_country = True
        if not has_country:
            bot.answer_callback_query(call.id, "❌ এই সার্ভিসের জন্য কোনো দেশের নাম্বার স্টকে নেই!", show_alert=True)
            return
        markup.add(types.InlineKeyboardButton(f"🔙 𝑩𝒂𝒄𝒌", callback_data="back_to_main_services"))
        bot.edit_message_text(f"📌 <b>𝑺𝒆𝒓𝒗𝒊𝒄𝒆: {svc_name.upper()}</b>\n<i>এবার কোন দেশের নাম্বার নিবেন তা সিলেক্ট করুন:</i>", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "back_to_main_services":
        available_services = set()
        for svc, c_dict in db.data["services"].items():
            for c_name, det in c_dict.items():
                if det["stock"] >= det.get("give_amount", 1):
                    available_services.add(svc)
        markup = types.InlineKeyboardMarkup(row_width=2)
        for s in available_services:
            markup.add(types.InlineKeyboardButton(f"📌 {s.upper()}", callback_data=f"ins_s|{s}"))
        bot.edit_message_text("👇 <b>প্রথমে সার্ভিস/অ্যাপ সিলেক্ট করুন:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("ins_can|"):
        parts = call.data.split("|")
        svc_name = parts[1]
        c_name = parts[2]
        with db_lock:
            prev_active = udata.get("active_numbers")
            if prev_active and prev_active.get("svc") == svc_name and prev_active.get("c") == c_name:
                prev_nums = prev_active.get("nums", [])
                
                if svc_name in db.data["services"] and c_name in db.data["services"][svc_name]:
                    db.data["services"][svc_name][c_name]["number_list"].extend(prev_nums)
                    db.data["services"][svc_name][c_name]["stock"] += len(prev_nums)
                
                udata["active_numbers"] = None
                db.save()
                bot.answer_callback_query(call.id, "✅ নাম্বার ক্যানসেল করা হয়েছে।", show_alert=True)
                try: bot.delete_message(call.message.chat.id, call.message.message_id)
                except: pass
            else:
                bot.answer_callback_query(call.id, "❌ কোনো অ্যাক্টিভ নাম্বার পাওয়া যায়নি!", show_alert=True)

    elif call.data.startswith("ins_g|") or call.data.startswith("ins_chg|"):
        try:
            is_change = call.data.startswith("ins_chg|")
            parts = call.data.split("|")
            svc_name = parts[1]
            c_name = parts[2]

            with db_lock:
                if not is_change:
                    current_time = time.time()
                    cooldown = db.data["settings"].get("cooldown_time", 10)
                    time_passed = current_time - udata.get("last_number_time", 0)
                    if time_passed < cooldown:
                        wait_time = int(cooldown - time_passed)
                        bot.answer_callback_query(call.id, f"⌛ Please Wait! আরও {wait_time} সেকেন্ড পর নাম্বার নিতে পারবেন।", show_alert=True)
                        return

                if svc_name not in db.data["services"] or c_name not in db.data["services"][svc_name]:
                    bot.answer_callback_query(call.id, "❌ দুঃখিত, নাম্বারটি স্টকে নেই বা শেষ হয়ে গেছে!", show_alert=True)
                    handle_ins_callbacks(type('obj', (object,), {'data': 'back_to_main_services', 'message': call.message, 'id': call.id, 'from_user': call.from_user}))
                    return

                if is_change:
                    prev_active = udata.get("active_numbers")
                    if prev_active and prev_active.get("svc") == svc_name and prev_active.get("c") == c_name:
                        prev_nums = prev_active.get("nums", [])
                        
                        if svc_name in db.data["services"] and c_name in db.data["services"][svc_name]:
                            db.data["services"][svc_name][c_name]["number_list"].extend(prev_nums)
                            db.data["services"][svc_name][c_name]["stock"] += len(prev_nums)

                item = db.data["services"][svc_name][c_name]
                give_amount = item.get("give_amount", 1)
                
                actual_nums = item.get("number_list", [])
                if not isinstance(actual_nums, list):
                    actual_nums = []
                    item["number_list"] = actual_nums
                real_stock = len(actual_nums)
                
                if item["stock"] != real_stock:
                    item["stock"] = real_stock

                if item["stock"] < give_amount:
                    bot.answer_callback_query(call.id, f"❌ পর্যাপ্ত স্টক নেই! (স্টক: {item['stock']} টি)", show_alert=True)
                    db.save()
                    return

                rate = float(item.get('otp_rate', 0.0))
                
                udata["last_number_time"] = time.time()
                udata["numbers_taken"] += give_amount
                udata["total_spent"] = udata.get("total_spent", 0.0) + (rate * give_amount)

                given = []
                for _ in range(give_amount):
                    given.append(item["number_list"].pop(0))
                item["stock"] -= give_amount

                if item["stock"] <= 0:
                    del db.data["services"][svc_name][c_name]
                    if not db.data["services"][svc_name]:
                        del db.data["services"][svc_name]

                udata["active_numbers"] = {
                    "svc": svc_name, "c": c_name, "nums": given, "otp_rate": rate, "buy_time": time.time()
                }
                db.save()

            bot.answer_callback_query(call.id, "✅ নাম্বার জেনারেট সফল হয়েছে!")

            currency = db.data['settings']['currency']
            header_msg = "✅ <b>𝑵𝒖𝒎𝒃𝒆𝒓𝒔 𝑮𝒆𝒏𝒆𝒓𝒂𝒕𝒆𝒅 𝑺𝒖𝒄𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚!</b>" if not is_change else "🔄 <b>𝑵𝒆𝒘 𝑵𝒖𝒎𝒃𝒆𝒓𝒔 𝑮𝒆𝒏𝒆𝒓𝒂𝒕𝒆𝒅!</b>"

            box_content = f"{c_name.title()} | {svc_name.upper()} | {rate} {currency}"
            border_len = len(box_content) + 2
            top_line = "╔" + ("═" * border_len) + "╗"
            bottom_line = "╚" + ("═" * border_len) + "╝"

            msg_text = (
                f"{header_msg}\n\n"
                f"<code>{top_line}\n"
                f"║ {box_content} ║\n"
                f"{bottom_line}</code>\n\n"
      
                f"⌛ <i>𝑾𝒂𝒊𝒕𝒊𝒏𝒈 𝑭𝒐𝒓 𝑺𝒎𝒔... (Max 20 mins)</i>"
            )

            markup = types.InlineKeyboardMarkup(row_width=1)
            
            for num in given:
                markup.add(types.InlineKeyboardButton(
                    text=f" {num}",
                    copy_text=types.CopyTextButton(text=str(num))
                ))

            markup.row(
                types.InlineKeyboardButton(f"♻️ 𝑪𝒉𝒂𝒏𝒈𝒆 𝑵𝒖𝒎𝒃𝒆𝒓", callback_data=f"ins_chg|{svc_name}|{c_name}"),
                types.InlineKeyboardButton(f"🌎 𝑪𝒉𝒂𝒏𝒈𝒆 𝑪𝒐𝒖𝒏𝒕𝒓𝒚", callback_data=f"ins_s|{svc_name}")
            )
            
            markup.add(
                types.InlineKeyboardButton(f"📩 𝑶𝑻𝑷 𝑮𝒓𝒐𝒖𝒑", url="https://t.me/kalamifxvvv223")
            )

            bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, reply_markup=markup, disable_web_page_preview=True)

        except Exception as e:
            bot.answer_callback_query(call.id, "❌ সিস্টেম এরর! আবার চেষ্টা করুন।", show_alert=True)
            logging.error(f"Error giving number: {e}")

    # ---------- ADMIN & WITHDRAW ----------
    elif call.data == "user_withdraw_start":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🟣 bKash", callback_data="wd_meth_bKash"),
            types.InlineKeyboardButton("🔴 Nagad", callback_data="wd_meth_Nagad")
        )
        bot.edit_message_text("💸 <b>𝑾𝒊𝒕𝒉𝒅𝒓𝒂𝒘 𝑩𝒂𝒍𝒂𝒏𝒄𝒆</b>\n\n🏦 <b>পেমেন্ট মেথড সিলেক্ট করুন:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("wd_meth_"):
        method = call.data.replace("wd_meth_", "")
        uid = str(call.from_user.id)
        user_sessions[uid] = {"method": method}
        
        prompt = f"🏦 <b>আপনার {method} নাম্বার দিন:</b>\n(যেমন: 017XXXXXXXX)"
            
        bot.delete_message(call.message.chat.id, call.message.message_id)
        msg = bot.send_message(call.message.chat.id, prompt)
        bot.register_next_step_handler(msg, process_withdraw_number)

    elif call.data == "adm_withdraw_reqs":
        reqs = db.data.get("withdraw_requests", {})
        if not reqs:
            bot.answer_callback_query(call.id, "কোনো পেন্ডিং উইথড্র রিকোয়েস্ট নেই!", show_alert=True)
            return
        bot.edit_message_text("💸 <b>Pending Withdraw Requests</b>", call.message.chat.id, call.message.message_id)
        for req_id, req in reqs.items():
            msg_text = (f"💳 <b>Request ID:</b> <code>{req_id}</code>\n👤 <b>Name:</b> {req['username']}\n💰 <b>Amount:</b> {req['amount']} {db.data['settings']['currency']}\n🏦 <b>Method:</b> {req['method']}\n📱 <b>Number:</b> <code>{req.get('number', 'N/A')}</code>\n📅 {req['date']}")
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton(f"✅ ACCEPT", callback_data=f"adm_wd_acc_{req_id}"), types.InlineKeyboardButton(f"❌ REJECT", callback_data=f"adm_wd_rej_{req_id}"))
            bot.send_message(call.message.chat.id, msg_text, reply_markup=markup)
        markup_back = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 BACK", callback_data="back_to_admin"))
        bot.send_message(call.message.chat.id, "ব্যাস, এগুলোই রিকোয়েস্ট।", reply_markup=markup_back)

    elif call.data.startswith("adm_wd_acc_"):
        req_id = call.data.replace("adm_wd_acc_", "")
        reqs = db.data.get("withdraw_requests", {})
        if req_id in reqs:
            with db_lock:
                req = reqs.pop(req_id)
                db.save()
            try: bot.send_message(req['uid'], f"🎉 <b>অভিনন্দন!</b>\nআপনার {req['amount']} {db.data['settings']['currency']} উইথড্র রিকোয়েস্টটি <b>অ্যাক্সেপ্ট</b> করা হয়েছে।")
            except: pass
            bot.edit_message_text(call.message.text + "\n\n✅ <b>ACCEPTED</b>", call.message.chat.id, call.message.message_id)
        else: bot.answer_callback_query(call.id, "Already processed!", show_alert=True)

    elif call.data.startswith("adm_wd_rej_"):
        req_id = call.data.replace("adm_wd_rej_", "")
        reqs = db.data.get("withdraw_requests", {})
        if req_id in reqs:
            with db_lock:
                req = reqs.pop(req_id)
                uid = req['uid']
                if uid in db.data["users"]: db.data["users"][uid]["balance"] += req['amount']
                db.save()
            try: bot.send_message(uid, f"❌ <b>দুঃখিত!</b>\nআপনার {req['amount']} {db.data['settings']['currency']} উইথড্র রিকোয়েস্টটি <b>রিজেক্ট</b> করা হয়েছে। ব্যালেন্স ফেরত দেওয়া হয়েছে।")
            except: pass
            bot.edit_message_text(call.message.text + "\n\n❌ <b>REJECTED & REFUNDED</b>", call.message.chat.id, call.message.message_id)
        else: bot.answer_callback_query(call.id, "Already processed!", show_alert=True)

    elif call.data == "adm_min_wd":
        msg = bot.send_message(call.message.chat.id, f"💰 <b>বর্তমান মিনিমাম উইথড্র:</b> {db.data['settings'].get('min_withdraw', 50.0)}\n\n<i>নতুন মিনিমাম উইথড্র অ্যামাউন্ট লিখুন:</i>", reply_markup=inline_back_btn("back_to_admin"))
        bot.register_next_step_handler(msg, set_min_withdraw_step)

    elif call.data == "adm_cooldown":
        msg = bot.send_message(call.message.chat.id, f"⏳ <b>বর্তমান কুলডাউন:</b> {db.data['settings'].get('cooldown_time', 10)}s\n\n<i>নতুন কুলডাউন সময় সেকেন্ডে লিখুন:</i>", reply_markup=inline_back_btn("back_to_admin"))
        bot.register_next_step_handler(msg, set_cooldown_step)

    elif call.data == "adm_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 <b>Broadcast Message</b>\n<i>যে মেসেজ, ছবি বা ভিডিও সবাইকে পাঠাতে চান, তা দিন:</i>", reply_markup=inline_back_btn("back_to_admin"))
        bot.register_next_step_handler(msg, process_broadcast_step)

    elif call.data == "adm_add_country":
        if not db.data["services"]:
            bot.answer_callback_query(call.id, "❌ আগে একটি ক্যাটাগরি তৈরি করুন!", show_alert=True)
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        for s in db.data["services"]: markup.add(types.InlineKeyboardButton(f"📁 {s}", callback_data=f"adm_file_svc_{s}"))
        markup.add(types.InlineKeyboardButton(f"🔙 BACK", callback_data="back_to_admin"))
        bot.edit_message_text("👇 <b>কোন সার্ভিসে (ক্যাটাগরিতে) নাম্বার আপলোড করবেন?</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("adm_file_svc_"):
        svc_name = call.data.replace("adm_file_svc_", "")
        msg = bot.send_message(call.message.chat.id, f"📁 <b>সার্ভিস: {svc_name}</b>\n\n📂 <b>Send Numbers File (.txt)</b>\n<i>একটি .txt ফাইল আপলোড করুন যেখানে প্রতি লাইনে একটি নাম্বার থাকবে:</i>", reply_markup=inline_back_btn("back_to_admin"))
        bot.register_next_step_handler(msg, process_numbers_file, svc_name)

    elif call.data == "adm_add_service":
        msg = bot.send_message(call.message.chat.id, "📁 <b>Add Category</b>\n<i>নতুন সার্ভিসের নাম লিখুন (যেমন: Facebook):</i>", reply_markup=inline_back_btn("back_to_admin"))
        bot.register_next_step_handler(msg, add_service_step)

    elif call.data == "adm_manage_num":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for s in db.data["services"]: 
            markup.add(types.InlineKeyboardButton(f"📁 {s}", callback_data=f"adm_mn_svc_{s}"))
        markup.add(types.InlineKeyboardButton(f"🔙 BACK", callback_data="back_to_admin"))
        bot.edit_message_text("📋 <b>Manage Numbers</b>\nকোন সার্ভিসের নাম্বার ম্যানেজ করবেন?", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("adm_mn_svc_"):
        svc = call.data.replace("adm_mn_svc_", "")
        markup = types.InlineKeyboardMarkup(row_width=2)
        if svc in db.data["services"]:
            for c in db.data["services"][svc]:
                markup.add(types.InlineKeyboardButton(f"❌ {c} ({db.data['services'][svc][c]['stock']})", callback_data=f"adm_mn_del_{svc}|{c}"))
        markup.add(types.InlineKeyboardButton(f"🔙 BACK", callback_data="adm_manage_num"))
        bot.edit_message_text(f"📋 <b>{svc} - Countries</b>\nকোন দেশের নাম্বার রিমুভ করবেন?", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("adm_mn_del_"):
        parts = call.data.replace("adm_mn_del_", "").split("|")
        svc = parts[0]
        c = parts[1]
        with db_lock:
            if svc in db.data["services"] and c in db.data["services"][svc]:
                del db.data["services"][svc][c]
                db.save()
                bot.answer_callback_query(call.id, f"✅ {c} রিমুভ হয়েছে!", show_alert=True)
        handle_ins_callbacks(type('obj', (object,), {'data': f'adm_mn_svc_{svc}', 'message': call.message, 'id': call.id, 'from_user': call.from_user}))

    elif call.data == "adm_del_cat_list":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for s in db.data["services"]: markup.add(types.InlineKeyboardButton(f"❌ {s}", callback_data=f"adm_delsvc_{s}"))
        markup.add(types.InlineKeyboardButton(f"🔙 BACK", callback_data="back_to_admin"))
        bot.edit_message_text("🗑 <b>Delete Category</b>\nকোন সার্ভিস মুছে ফেলবেন?", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("adm_delsvc_"):
        svc = call.data.replace("adm_delsvc_", "")
        with db_lock:
            if svc in db.data["services"]:
                del db.data["services"][svc]
                db.save()
                bot.answer_callback_query(call.id, f"✅ {svc} ডিলিট হয়েছে!", show_alert=True)
        handle_ins_callbacks(type('obj', (object,), {'data': 'adm_del_cat_list', 'message': call.message, 'id': call.id, 'from_user': call.from_user}))

    elif call.data == "adm_settings":
        power = "ON" if db.data["settings"]["bot_status"] else "OFF"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton(f"⚡ BOT POWER ({power})", callback_data="adm_power"))
        markup.add(types.InlineKeyboardButton(f"🔙 BACK", callback_data="back_to_admin"))
        bot.edit_message_text("⚙️ <b>Advanced Settings</b>\n<i>(চ্যানেল ফোর্স জয়েন এখন ডিফল্টভাবে যুক্ত আছে)</i>", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "adm_power":
        with db_lock:
            db.data["settings"]["bot_status"] = not db.data["settings"]["bot_status"]
            db.save()
        handle_ins_callbacks(type('obj', (object,), {'data': 'adm_settings', 'message': call.message, 'id': call.id, 'from_user': call.from_user}))

# ================= 🧩 STEP HANDLERS =================
def process_broadcast_step(message):
    if message.text == "🔙 𝑩𝒂𝒄𝒌": return
    bot.send_message(message.chat.id, "⏳ <b>ব্রডকাস্ট শুরু হয়েছে... অনুগ্রহ করে অপেক্ষা করুন।</b>")
    users = list(db.data["users"].keys())
    success = 0
    failed = 0
    for uid in users:
        try:
            bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
        except Exception:
            failed += 1
        time.sleep(0.05)
    bot.send_message(message.chat.id, f"✅ <b>ব্রডকাস্ট সম্পন্ন হয়েছে!</b>\n🟢 সফল: {success}\n🔴 ব্যর্থ: {failed}")

def process_withdraw_number(message):
    uid = str(message.from_user.id)
    if uid in user_sessions:
        user_sessions[uid]["number"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "💰 <b>কত টাকা উইথড্র করতে চান?</b>\n(শুধুমাত্র টাকার পরিমাণ লিখুন)")
    bot.register_next_step_handler(msg, process_withdraw_amount)

def process_withdraw_amount(message):
    uid = str(message.from_user.id)
    try:
        amount = float(message.text.strip())
        udata = db.get_user(uid)
        min_wd = db.data["settings"].get("min_withdraw", 50.0)
        
        if amount < min_wd:
            bot.send_message(message.chat.id, f"❌ <b>অ্যামাউন্ট খুব কম!</b>\nসর্বনিম্ন উইথড্র হলো {min_wd} {db.data['settings']['currency']}।")
            return
            
        if amount > udata['balance']:
            bot.send_message(message.chat.id, "❌ আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই।")
            return
            
        session = user_sessions.get(uid)
        if not session: return
            
        with db_lock:
            db.data["users"][uid]["balance"] -= amount
            req_id = f"req_{int(time.time())}"
            db.data["withdraw_requests"][req_id] = {
                "uid": uid,
                "username": message.from_user.first_name,
                "amount": amount,
                "method": session.get("method"),
                "number": session.get("number"),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            db.save()
        del user_sessions[uid]
        
        bot.send_message(message.chat.id, f"✅ <b>উইথড্র রিকোয়েস্ট সফলভাবে পাঠানো হয়েছে!</b>\n\nঅ্যামাউন্ট: <b>{amount} {db.data['settings']['currency']}</b>\nমেথড: <b>{session.get('method')}</b>\nনাম্বার: <code>{session.get('number')}</code>\n\n<i>অ্যাডমিন চেক করে দ্রুত পেমেন্ট করে দেবে।</i>")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা দিন!")

def set_min_withdraw_step(message):
    try:
        val = float(message.text)
        with db_lock:
            db.data["settings"]["min_withdraw"] = val
            db.save()
        bot.send_message(message.chat.id, f"✅ <b>মিনিমাম উইথড্র আপডেট হয়েছে:</b> {val} {db.data['settings']['currency']}")
    except ValueError:
        bot.send_message(message.chat.id, "❌ শুধুমাত্র সংখ্যা দিন!")

def set_cooldown_step(message):
    try:
        val = int(message.text)
        with db_lock:
            db.data["settings"]["cooldown_time"] = val
            db.save()
        bot.send_message(message.chat.id, f"✅ <b>কুলডাউন টাইম আপডেট হয়েছে:</b> {val} সেকেন্ড।")
    except ValueError:
        bot.send_message(message.chat.id, "❌ শুধুমাত্র সংখ্যা দিন!")

def add_service_step(message):
    svc = message.text
    with db_lock:
        if svc not in db.data["services"]:
            db.data["services"][svc] = {}
            db.save()
            bot.send_message(message.chat.id, f"✅ <b>Category Added:</b> {svc}")
        else:
            bot.send_message(message.chat.id, "⚠️ Already exists!")

def process_numbers_file(message, svc_name):
    if not message.document or not message.document.file_name.endswith('.txt'):
        bot.send_message(message.chat.id, "❌ <b>শুধুমাত্র .txt ফাইল দিন!</b>")
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        lines = downloaded.decode('utf-8').strip().split('\n')
        
        valid_nums = [line.strip() for line in lines if line.strip()]
        
        if not valid_nums:
            bot.send_message(message.chat.id, "❌ ফাইলে কোনো নাম্বার পাওয়া যায়নি।")
            return
            
        admin_sessions[message.from_user.id] = {"svc_name": svc_name, "numbers": valid_nums, "count": len(valid_nums)}
        
        msg = bot.send_message(message.chat.id, f"✅ <b>ফাইল রিড সাকসেসফুল!</b>\n📄 মোট নাম্বার: {len(valid_nums)} টি\n\n<b>এখন দেশের নাম ও পতাকা দিন:</b>\n<i>(যেমন: 🇧🇩 Bangladesh)</i>")
        bot.register_next_step_handler(msg, ask_country_manual_step)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>Error:</b> {e}")

def ask_country_manual_step(message):
    if message.text == "🔙 𝑩𝒂𝒄𝒌": return
    c_name = message.text.strip()
    if message.from_user.id in admin_sessions:
        admin_sessions[message.from_user.id]["c_name"] = c_name
        msg = bot.send_message(message.chat.id, "🔢 <b>এক ক্লিকে কয়টি করে নাম্বার দিতে চান?</b>\n<i>(যেমন: 1, 2 বা 3)</i>")
        bot.register_next_step_handler(msg, ask_give_amount_step)
    else:
        bot.send_message(message.chat.id, "⚠️ সেশন শেষ! আবার ফাইল আপলোড করুন।")

def ask_give_amount_step(message):
    try:
        give_amount = int(message.text.strip())
        if message.from_user.id in admin_sessions:
            admin_sessions[message.from_user.id]["give_amount"] = give_amount
            msg = bot.send_message(message.chat.id, "💰 <b>প্রতিটি OTP এর রেট (দাম) কত হবে?</b>\n<i>(যেমন: 2.50)</i>")
            bot.register_next_step_handler(msg, add_price_and_save_step)
        else:
            bot.send_message(message.chat.id, "⚠️ সেশন শেষ! আবার ফাইল আপলোড করুন।")
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ শুধুমাত্র সংখ্যা দিন! <b>এক ক্লিকে কয়টি করে নাম্বার দিতে চান?</b>")
        bot.register_next_step_handler(msg, ask_give_amount_step)

def add_price_and_save_step(message):
    try:
        otp_rate = float(message.text.strip())
        session = admin_sessions.get(message.from_user.id)
        if not session:
            bot.send_message(message.chat.id, "⚠️ সেশন শেষ! আবার ফাইল আপলোড করুন।")
            return
            
        svc_name = session["svc_name"]
        c_name = session["c_name"]
        num_list = session["numbers"]
        cnt = session["count"]
        give_amount = session.get("give_amount", 1)
        
        with db_lock:
            if c_name in db.data["services"][svc_name]:
                db.data["services"][svc_name][c_name]["stock"] += cnt
                db.data["services"][svc_name][c_name]["number_list"].extend(num_list)
                db.data["services"][svc_name][c_name]["otp_rate"] = otp_rate
                db.data["services"][svc_name][c_name]["give_amount"] = give_amount
            else:
                db.data["services"][svc_name][c_name] = {"otp_rate": otp_rate, "give_amount": give_amount, "stock": cnt, "number_list": num_list}
            db.save()
            
        del admin_sessions[message.from_user.id]
        
        bot.send_message(message.chat.id, f"🔥 <b>সাকসেসফুল!</b>\n✨ সার্ভিস: {svc_name}\n🌍 দেশ: {c_name}\n📱 নাম্বার যোগ হয়েছে: {cnt} টি।\n🎯 একবারে পাবে: {give_amount} টি\n💸 OTP রেট: {otp_rate}{db.data['settings']['currency']}")
    except ValueError:
        bot.send_message(message.chat.id, "❌ রেট ভুল! সঠিক সংখ্যা দিন।")


if __name__ == "__main__":
    logging.info("Starting 𝑰𝑵𝑺 𝑯𝑼𝑩𝑬 Power Engine with DUAL API Routing & Force Join...")
    
    # ⚙️ Background Thread for DUAL OTP Polling & Expiry Checking (INBOX SENDER)
    otp_thread = threading.Thread(target=background_otp_poller)
    otp_thread.daemon = True 
    otp_thread.start()
    
    print("✅ 𝑰𝑵𝑺 𝑯𝑼𝑩𝑬 IS NOW ONLINE AND FULLY OPTIMIZED WITH DUAL API!")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
