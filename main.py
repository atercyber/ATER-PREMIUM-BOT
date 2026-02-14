import json
import os
import logging
import asyncio
import requests
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- Render Port Binding Fix (Web Server) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"
def run(): app.run(host='0.0.0.0', port=10000) # Render default port

# ------------------- Configuration -------------------
BOT_TOKEN = "8338232613:AAEi995yXNytZt6HvVBxWcf3HM1M4yxvPoY"
ADMINS = {8418684406}
WELCOME_IMAGE = "https://ibb.co/8DC6NQ71"
MY_UPI_ID = "kumarishant8813@ptys"

# --- API की सूची ---
AADHAR_API = "https://darkietech.site/numapi.php?action=api&key=CODER&aadhaf="
NUMBER_API = "https://darkietech.site/numapi.php?action=api&key=CODER&numberr="
AADHAR_FAMILY_API = "https://darkietech.site/numapi.php?action=api&key=CODER&aadhar_family="
UPI_API_BASE = "https://darkietech.site/numapi.php?action=api&key=CODER&upi="
VEHICLE_API_BASE = "https://darkietech.site/numapi.php?action=api&key=CODER&vehicle="
IFSC_API_BASE = "https://ifsc.razorpay.com/"

COSTS = {"aadhar": 4, "number": 5, "family": 5, "ifsc": 2, "upi": 3, "vehicle": 3}

# ------------------- Data Store -------------------
DATA_FILE = 'data_store.json'
DEFAULT_DATA = {
    "users": {},
    "redeem_codes": {},
    "banned_users": [],
    "channels": [{"id": "-1003019430565", "link": "https://t.me/+ax8_tkp3pts4NDE1", "name": "📢 MAIN CHANNEL"}]
}

class DataStore:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self._data = DEFAULT_DATA.copy()
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r') as f:
                    self._data = json.load(f)
            except: pass

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self._data, f, indent=4)

    def ensure_user(self, user_id):
        uid = str(user_id)
        if uid not in self._data['users']:
            self._data['users'][uid] = {"credits": 2, "referrals": []}
            self.save()
        return uid

    def add_credits(self, user_id, amount):
        uid = self.ensure_user(user_id)
        self._data['users'][uid]['credits'] += amount
        self.save()
        return True

    def debit_credits(self, user_id, amount):
        uid = self.ensure_user(user_id) # KeyError से बचने के लिए
        if self._data['users'][uid]['credits'] >= amount:
            self._data['users'][uid]['credits'] -= amount
            self.save()
            return True
        return False

data_store = DataStore()

# ------------------- Handlers -------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data_store.ensure_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("👤 Profile", callback_data="profile"), InlineKeyboardButton("💳 Buy Credits", callback_data="buy")],
        [InlineKeyboardButton("🆔 Aadhar Info", callback_data="aadhar"), InlineKeyboardButton("📞 Number Info", callback_data="number")],
        [InlineKeyboardButton("👨‍👩‍👧 Family Info", callback_data="family"), InlineKeyboardButton("🏦 IFSC Info", callback_data="ifsc")],
        [InlineKeyboardButton("💸 UPI Info", callback_data="upi"), InlineKeyboardButton("🚗 Vehicle Info", callback_data="vehicle")],
        [InlineKeyboardButton("🎟 Redeem Code", callback_data="redeem_user"), InlineKeyboardButton("📢 Refer", callback_data="refer")],
    ]
    if user_id in ADMINS:
        keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_main")])

    await update.message.reply_photo(photo=WELCOME_IMAGE, caption="👋 **Welcome to ATER INFO 2.0**", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    uid = data_store.ensure_user(user_id) # Fix KeyError
    await query.answer()

    if query.data == "profile":
        credits = data_store._data['users'][uid]['credits']
        await query.message.reply_text(f"👤 **User ID:** `{user_id}`\n💰 **Credits:** `{credits}`")

    elif query.data == "buy":
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={MY_UPI_ID}&cu=INR"
        caption = f"💳 **PAYMENT**\n\n🆔 **UPI:** `{MY_UPI_ID}`\n\n💰 ₹50 = 75 Credits\n💰 ₹100 = 150 Credits\n\n⚠️ स्क्रीनशॉट @atercyber को भेजें।"
        await query.message.reply_photo(photo=qr_url, caption=caption)

    elif query.data in COSTS:
        context.user_data['step'] = f"lookup_{query.data}"
        await query.message.reply_text(f"🔍 इनपुट भेजें...\n💳 खर्च: {COSTS[query.data]} क्रेडिट्स")

    elif query.data == "admin_main" and user_id in ADMINS:
        keyboard = [[InlineKeyboardButton("➕ Add Credits", callback_data="adm_add"), InlineKeyboardButton("🎟 Create Code", callback_data="adm_gen_code")]]
        await query.message.reply_text("🛠 ADMIN PANEL", reply_markup=InlineKeyboardMarkup(keyboard))

    # अन्य admin handlers यहाँ जोड़ सकते हैं...

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    step = context.user_data.get('step')

    if not step: return

    if step.startswith("lookup_"):
        l_type = step.split("_")[1]
        cost = COSTS.get(l_type, 0)
        
        if data_store.debit_credits(user_id, cost):
            msg = await update.message.reply_text("⏳ Processing...")
            url = ""
            if l_type == "aadhar": url = f"{AADHAR_API}{text}"
            elif l_type == "number": url = f"{NUMBER_API}{text}"
            elif l_type == "family": url = f"{AADHAR_FAMILY_API}{text}"
            elif l_type == "upi": url = f"{UPI_API_BASE}{text}"
            elif l_type == "vehicle": url = f"{VEHICLE_API_BASE}{text}"
            elif l_type == "ifsc": url = f"{IFSC_API_BASE}{text}"

            try:
                resp = requests.get(url, timeout=15).text
                await msg.edit_text(f"✅ **Result:**\n`{resp}`")
            except:
                await msg.edit_text("❌ API Error!")
        else:
            await update.message.reply_text("❌ क्रेडिट्स कम हैं।")
        context.user_data['step'] = None

    # Admin: Add Credits Logic
    elif step == 'adm_add' and user_id in ADMINS:
        try:
            target_id, amt = text.split()
            data_store.add_credits(target_id, int(amt))
            await update.message.reply_text(f"✅ {amt} क्रेडिट्स {target_id} को दिए गए।")
        except: await update.message.reply_text("Format: `UID AMOUNT`")
        context.user_data['step'] = None

# ------------------- Main -------------------
def main():
    # Start Flask Web Server in a separate thread
    Thread(target=run).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
