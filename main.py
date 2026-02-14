import json
import os
import logging
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ------------------- Configuration -------------------
BOT_TOKEN = "8338232613:AAEi995yXNytZt6HvVBxWcf3HM1M4yxvPoY"
ADMINS = {8418684406}
WELCOME_IMAGE = "https://ibb.co/8DC6NQ71"
MY_UPI_ID = "kumarishant8813@ptys" # आपकी UPI ID

# --- सभी API की सूची ---
AADHAR_API = "https://darkietech.site/numapi.php?action=api&key=CODER&aadhaf="
NUMBER_API = "https://darkietech.site/numapi.php?action=api&key=CODER&numberr="
NUMBER_API_BACKUP = "https://darkietech.site/numapi.php?action=api&key=CODER&number="
AADHAR_FAMILY_API = "https://darkietech.site/numapi.php?action=api&key=CODER&aadhar_family="
UPI_API_BASE = "https://darkietech.site/numapi.php?action=api&key=CODER&upi="
VEHICLE_API_BASE = "https://darkietech.site/numapi.php?action=api&key=CODER&vehicle="
IFSC_API_BASE = "https://ifsc.razorpay.com/"

# --- खर्च (Costs) ---
COSTS = {
    "aadhar": 4,
    "number": 5,
    "family": 5,
    "ifsc": 2,
    "upi": 3,
    "vehicle": 3
}

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
        if not os.path.exists(self.path):
            self._write(DEFAULT_DATA)
        self._load()

    def _load(self):
        try:
            with open(self.path, 'r') as f:
                self._data = json.load(f)
        except: self._data = DEFAULT_DATA.copy()

    def _write(self, data):
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=4)

    def save(self): self._write(self._data)

    def get_users(self): return self._data.get('users', {})

    def ensure_user(self, user_id):
        uid = str(user_id)
        if uid not in self._data['users']:
            self._data['users'][uid] = {"credits": 2, "referrals": []}
            self.save()

    def add_credits(self, user_id, amount):
        uid = str(user_id)
        if uid in self._data['users']:
            self._data['users'][uid]['credits'] += amount
            self.save()
            return True
        return False

    def debit_credits(self, user_id, amount):
        uid = str(user_id)
        if self._data['users'][uid]['credits'] >= amount:
            self._data['users'][uid]['credits'] -= amount
            self.save()
            return True
        return False

data_store = DataStore()

# ------------------- API Services -------------------
def call_api(url):
    try:
        resp = requests.get(url, timeout=15)
        return resp.json()
    except: return {"error": "API Response Error"}

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
    await query.answer()

    if query.data == "profile":
        uid = str(user_id)
        credits = data_store._data['users'][uid]['credits']
        await query.message.reply_text(f"👤 **User ID:** `{user_id}`\n💰 **Credits:** `{credits}`")

    elif query.data == "buy":
        # QR कोड से नाम हटा दिया गया है
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={MY_UPI_ID}&cu=INR"
        
        caption_text = (
            "💳 **PAYMENT GATEWAY**\n\n"
            f"🆔 **UPI ID:** `{MY_UPI_ID}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💰 **Price List:**\n"
            "• ₹50  👉  75 Credits\n"
            "• ₹100 👉  150 Credits\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ **Note:** पेमेंट के बाद स्क्रीनशॉट @atercyber को भेजें।"
        )
        await query.message.reply_photo(photo=qr_url, caption=caption_text, parse_mode="Markdown")

    elif query.data in COSTS:
        context.user_data['step'] = f"lookup_{query.data}"
        await query.message.reply_text(f"🔍 इनपुट भेजें (Input Required)...\n💳 Cost: {COSTS[query.data]} credits")

    elif query.data == "redeem_user":
        context.user_data['step'] = 'use_code'
        await query.message.reply_text("🎟 रिडीम कोड भेजें:")

    elif query.data == "admin_main" and user_id in ADMINS:
        keyboard = [
            [InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"), InlineKeyboardButton("📊 Stats", callback_data="adm_st")],
            [InlineKeyboardButton("➕ Add Credits", callback_data="adm_add"), InlineKeyboardButton("🎟 Create Code", callback_data="adm_gen_code")]
        ]
        await query.message.reply_text("🛠 **ADMIN PANEL**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "adm_gen_code":
        context.user_data['step'] = 'gen_code'
        await query.message.reply_text("Format: `CODE AMOUNT` (e.g. `TEST50 50`)")

    elif query.data == "adm_add":
        context.user_data['step'] = 'add_c'
        await query.message.reply_text("Format: `USER_ID AMOUNT` (e.g. `12345 100`)")

    elif query.data == "adm_bc":
        context.user_data['step'] = 'bc'
        await query.message.reply_text("ब्रॉडकास्ट मैसेज भेजें:")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    step = context.user_data.get('step')

    if not step: return

    # Lookup Logic
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

            result = call_api(url)
            await msg.edit_text(f"✅ **Result:**\n`{json.dumps(result, indent=2)}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Insufficient credits.")
        context.user_data['step'] = None

    # Admin: Add Credits
    elif step == 'add_c' and user_id in ADMINS:
        try:
            tid, amt = text.split()
            if data_store.add_credits(tid, int(amt)):
                await update.message.reply_text(f"✅ Added {amt} to {tid}")
        except: await update.message.reply_text("Format: `UID AMT`")
        context.user_data['step'] = None

    # Admin: Gen Code
    elif step == 'gen_code' and user_id in ADMINS:
        try:
            name, amt = text.split()
            data_store._data['redeem_codes'][name.upper()] = int(amt)
            data_store.save()
            await update.message.reply_text(f"✅ Code `{name.upper()}` created.")
        except: await update.message.reply_text("Format: `CODE AMT`")
        context.user_data['step'] = None

    # User: Use Code
    elif step == 'use_code':
        code = text.strip().upper()
        codes = data_store._data.get('redeem_codes', {})
        if code in codes:
            val = codes.pop(code)
            data_store.add_credits(user_id, val)
            data_store.save()
            await update.message.reply_text(f"✅ Received {val} credits!")
        else: await update.message.reply_text("❌ Invalid code.")
        context.user_data['step'] = None

    # Admin: Broadcast
    elif step == 'bc' and user_id in ADMINS:
        context.user_data['step'] = None
        users = data_store.get_users()
        for uid in users:
            try: await update.message.copy(chat_id=int(uid))
            except: pass
        await update.message.reply_text("✅ Broadcast complete.")

# ------------------- Main -------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
    print("Bot started without name in payment!")
    app.run_polling()

if __name__ == "__main__":
    main()
