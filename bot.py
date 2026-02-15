import telebot
from telebot import types
import json
import os

# ==================== SOZLAMALAR ====================
TOKEN = "8542065155:AAFLxjDCYyi3JdVQ_q8_cnDIGB-P2Brt2mg"
ADMIN_ID = 5791947157

bot = telebot.TeleBot(TOKEN)

# ==================== MA'LUMOTLAR BAZASI ====================
DATA_FILE = "anime_database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

anime_db = load_data()
admin_session = {}
user_session = {}

# ==================== START ====================
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    
    if uid == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Anime qo'shish", "📋 Animelar ro'yhati")
        bot.send_message(uid, "🎬 Admin paneliga xush kelibsiz!", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🔎 Animelarni qidirish")
        bot.send_message(uid, "🎬 Xush kelibsiz!", reply_markup=markup)

# ==================== DONE BUYRUG'I (YUQORIGA KO‘CHIRILDI) ====================
@bot.message_handler(commands=['done'])
def done_command(message):
    uid = message.from_user.id
    
    if uid != ADMIN_ID:
        return
    
    if uid not in admin_session or admin_session[uid]["step"] != "awaiting_videos":
        bot.send_message(uid, "⚠️ Hozir hech qanday jarayon yo'q.")
        return
    
    if not admin_session[uid]["videos"]:
        bot.send_message(uid, "❌ Hech qanday video yuborilmadi.")
        return
    
    session = admin_session[uid]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Xatolik yo'q", callback_data="confirm_yes"),
        types.InlineKeyboardButton("❌ Xatolik bor", callback_data="confirm_no")
    )
    
    msg = f"🔍 MA'LUMOTLARNI TEKSHIRING:\n\n"
    msg += f"🔢 Kod: {session['code']}\n"
    msg += f"📺 Nomi: {session['name']}\n"
    msg += f"🎭 Janr: {session['genre']}\n"
    msg += f"📹 Videolar soni: {len(session['videos'])} ta"
    
    bot.send_message(uid, msg, reply_markup=markup)

# ==================== ADMIN PANEL ====================
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID 
                     and m.content_type == 'text' 
                     and not m.text.startswith('/'))
def admin_text_handler(message):
    uid = message.from_user.id
    text = message.text
    
    if text == "➕ Anime qo'shish":
        admin_session[uid] = {"step": "awaiting_code", "videos": []}
        bot.send_message(uid, "🔢 Anime kodini kiriting:")
        return
    
    if text == "📋 Animelar ro'yhati":
        if not anime_db:
            bot.send_message(uid, "❌ Hozircha animelar yo'q.")
        else:
            msg = "📋 ANIMELAR RO'YXATI:\n\n"
            for code, data in anime_db.items():
                msg += f"🔢 Kod: {code}\n📺 Nomi: {data['name']}\n🎭 Janr: {data['genre']}\n📹 Videolar: {len(data['videos'])} ta\n\n"
            bot.send_message(uid, msg)
        return
    
    if uid in admin_session:
        session = admin_session[uid]
        
        if session["step"] == "awaiting_code":
            code = text.strip()
            if code in anime_db:
                bot.send_message(uid, "⚠️ Bu kod allaqachon mavjud. Boshqa kod kiriting:")
                return
            session["code"] = code
            session["step"] = "awaiting_name"
            bot.send_message(uid, "✍️ Animening nomini kiriting:")
            return
        
        if session["step"] == "awaiting_name":
            session["name"] = text.strip()
            session["step"] = "awaiting_genre"
            bot.send_message(uid, "🎭 Animening janrini kiriting:")
            return
        
        if session["step"] == "awaiting_genre":
            session["genre"] = text.strip()
            session["step"] = "awaiting_videos"
            bot.send_message(uid, "📹 Barcha qismlarni yuboring.\nTugatgach /done yozing.")
            return

# ==================== VIDEO ====================
@bot.message_handler(content_types=['video'])
def handle_video(message):
    uid = message.from_user.id
    
    if uid != ADMIN_ID:
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(uid, "⛔ Botda ortiqcha gaplarni yozmang.")
        return
    
    if uid not in admin_session or admin_session[uid]["step"] != "awaiting_videos":
        bot.send_message(uid, "⚠️ Avval '➕ Anime qo'shish' tugmasini bosing.")
        return
    
    admin_session[uid]["videos"].append(message.video.file_id)
    bot.send_message(uid, f"✅ Video qabul qilindi ({len(admin_session[uid]['videos'])} ta)")

# ==================== TASDIQLASH ====================
@bot.callback_query_handler(func=lambda call: call.from_user.id == ADMIN_ID)
def confirm_callback(call):
    uid = call.from_user.id
    
    if uid not in admin_session:
        return
    
    session = admin_session[uid]
    
    if call.data == "confirm_yes":
        anime_db[session["code"]] = {
            "name": session["name"],
            "genre": session["genre"],
            "videos": session["videos"]
        }
        save_data(anime_db)
        del admin_session[uid]
        
        bot.edit_message_text("✅ Anime qo'shildi!",
                              call.message.chat.id,
                              call.message.message_id)
        
    elif call.data == "confirm_no":
        del admin_session[uid]
        bot.edit_message_text("❌ Jarayon bekor qilindi.",
                              call.message.chat.id,
                              call.message.message_id)

# ==================== FOYDALANUVCHI PANELI ====================
@bot.message_handler(func=lambda m: m.from_user.id != ADMIN_ID)
def user_handler(message):
    uid = message.from_user.id
    text = message.text
    
    if text == "🔎 Animelarni qidirish":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🔢 Kodi orqali", "📺 Nomi orqali")
        markup.add("🎭 Janri orqali")
        markup.add("🔙 Orqaga")
        bot.send_message(uid, "Qidirish turini tanlang:", reply_markup=markup)
        return
    
    if text == "🔙 Orqaga":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🔎 Animelarni qidirish")
        bot.send_message(uid, "Bosh menyu:", reply_markup=markup)
        if uid in user_session:
            del user_session[uid]
        return
    
    if text == "🔢 Kodi orqali":
        user_session[uid] = "search_code"
        bot.send_message(uid, "🔢 Anime kodini kiriting:")
        return
    
    if text == "📺 Nomi orqali":
        user_session[uid] = "search_name"
        bot.send_message(uid, "📺 Anime nomini kiriting:")
        return
    
    if text == "🎭 Janri orqali":
        genres = list(set([data["genre"] for data in anime_db.values()]))
        
        if not genres:
            bot.send_message(uid, "❌ Hozircha animelar yo'q.")
            return
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for genre in genres:
            markup.add(genre)
        markup.add("🔙 Orqaga")
        
        user_session[uid] = "search_genre"
        bot.send_message(uid, "🎭 Janrni tanlang:", reply_markup=markup)
        return
    
    if uid in user_session:
        search_type = user_session[uid]
        
        if search_type == "search_code":
            if text in anime_db:
                send_anime_info(uid, text, anime_db[text])
            else:
                bot.send_message(uid, "❌ Topilmadi.")
            del user_session[uid]
            return
        
        if search_type == "search_name":
            found = False
            for code, data in anime_db.items():
                if data["name"].lower() == text.lower():
                    send_anime_info(uid, code, data)
                    found = True
                    break
            if not found:
                bot.send_message(uid, "❌ Topilmadi.")
            del user_session[uid]
            return
        
        if search_type == "search_genre":
            found = []
            for code, data in anime_db.items():
                if data["genre"].lower() == text.lower():
                    found.append((code, data))
            
            if found:
                for code, data in found:
                    send_anime_info(uid, code, data)
            else:
                bot.send_message(uid, "❌ Topilmadi.")
            
            del user_session[uid]
            return
    
    bot.send_message(uid, "⛔ Botda ortiqcha gaplarni yozmang.")

# ==================== ANIME YUBORISH ====================
def send_anime_info(uid, code, data):
    msg = f"📺 {data['name']}\n\n"
    msg += f"🔢 Kod: {code}\n"
    msg += f"🎭 Janr: {data['genre']}\n"
    msg += f"📹 Qismlar: {len(data['videos'])} ta"
    
    bot.send_message(uid, msg)
    
    for video_id in data["videos"]:
        bot.send_video(uid, video_id)

# ==================== ISHGA TUSHIRISH ====================
print("✅ Bot ishga tushdi...")
bot.infinity_polling()
