# RANA INFO 2.0 Bot - COMPLETE ERROR-FREE VERSION
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

# All APIs Included
AADHAR_API = "https://darkietech.site/numapi.php?action=api&key=CODER&aadhaf="
NUMBER_API = "https://darkietech.site/numapi.php?action=api&key=CODER&numberr="
NUMBER_API_BACKUP = "https://darkietech.site/numapi.php?action=api&key=CODER&number="
AADHAR_FAMILY_API = "https://darkietech.site/numapi.php?action=api&key=CODER&aadhar_family="
UPI_API_BASE = "https://darkietech.site/numapi.php?action=api&key=CODER&upi={upi}"
VEHICLE_API_BASE = "https://darkietech.site/numapi.php?action=api&key=CODER&vehicle={rc}"
IFSC_API = "https://ifsc.razorpay.com/"
PAK_NUMBER_API = "https://darkietech.site/numapi.php?action=api&key=CODER&pak_num="

# Costs Settings
VEHICLE_LOOKUP_COST = 3
UPI_LOOKUP_COST = 3
IFSC_LOOKUP_COST = 2
AADHAR_LOOKUP_COST = 4
NUMBER_LOOKUP_COST = 5
PAK_NUMBER_LOOKUP_COST = 2
FAMILY_LOOKUP_COST = 5

DEFAULT_CHANNELS = [
    {"id": "-1003019430565", "name": "📢 MAIN CHANNEL", "link": "https://t.me/+ax8_tkp3pts4NDE1"},
]

# ------------------- Data Store Logic -------------------
DATA_FILE = 'data_store.json'
class DataStore:
    def __init__(self):
        if not os.path.exists(DATA_FILE):
            self._data = {"users": {}, "redeem_codes": {}, "banned_users": []}
            self.save()
        else:
            with open(DATA_FILE, 'r') as f: self._data = json.load(f)

    def save(self):
        with open(DATA_FILE, 'w') as f: json.dump(self._data, f, indent=4)

    def ensure_user(self, user_id, referrer=None):
        uid = str(user_id)
        if uid not in self._data['users']:
            self._data['users'][uid] = {"credits": 2, "referrals": [], "referred_by": referrer}
            if referrer and str(referrer) in self._data['users']:
                self._data['users'][str(referrer)]['credits'] += 1 # Bonus for refer
                self._data['users'][str(referrer)]['referrals'].append(user_id)
            self.save()

    def get_user(self, user_id): return self._data['users'].get(str(user_id), {"credits": 0, "referrals": []})
    
    def update_credits(self, user_id, amount):
        uid = str(user_id)
        if uid in self._data['users']:
            self._data['users'][uid]['credits'] += amount
            self.save()
            return True
        return False

    def is_banned(self, user_id): return user_id in self._data['banned_users']

data_store = DataStore()

# ------------------- API Helper -------------------
def call_api(url):
    try:
        r = requests.get(url, timeout=15)
        return r.json() if r.status_code == 200 else {"error": "API Offline"}
    except: return {"error": "Connection Timeout"}

# ------------------- Handlers -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if data_store.is_banned(user_id): return

    # Referral Check
    ref_id = None
    if context.args and context.args[0].startswith('ref_'):
        try: ref_id = context.args[0].split('_')[1]
        except: pass
    
    data_store.ensure_user(user_id, referrer=ref_id)

    keyboard = [
        [InlineKeyboardButton("👤 Profile", callback_data="profile"), InlineKeyboardButton("💳 Buy Credits", callback_data="buy")],
        [InlineKeyboardButton("🆔 Aadhar Info", callback_data="ask_aadhar"), InlineKeyboardButton("📞 Number Info", callback_data="ask_number")],
        [InlineKeyboardButton("🇵🇰 Pak Number", callback_data="ask_pak"), InlineKeyboardButton("👨‍👩‍👧‍👦 Aadhar Family", callback_data="ask_family")],
        [InlineKeyboardButton("🚗 Vehicle RC", callback_data="ask_rc"), InlineKeyboardButton("💸 UPI Lookup", callback_data="ask_upi")],
        [InlineKeyboardButton("🏦 IFSC Info", callback_data="ask_ifsc"), InlineKeyboardButton("📢 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("🎟 Redeem Code", callback_data="redeem")]
    ]
    if user_id in ADMINS:
        keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_menu")])

    await update.message.reply_photo(WELCOME_IMAGE, caption="👋 *Welcome to ATER INFO 2.0*\n\nIntelligence at your fingertips.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "profile":
        u = data_store.get_user(user_id)
        await query.message.reply_text(f"👤 *Profile Details*\n\nID: `{user_id}`\n💰 Credits: *{u['credits']}*\n👥 Referrals: *{len(u['referrals'])}*", parse_mode="Markdown")
    
    elif query.data == "refer":
        link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref_{user_id}"
        await query.message.reply_text(f"📢 *Refer & Earn*\n\nShare this link. You get *1 Credit* for every user who joins!\n\n`{link}`", parse_mode="Markdown")

    elif query.data == "buy":
        await query.message.reply_text("💳 *Buy Credits*\n\nContact: @Crazyrana07\n\n50₹ = 75 Credits\n100₹ = 150 Credits", parse_mode="Markdown")

    elif query.data == "admin_menu" and user_id in ADMINS:
        kb = [[InlineKeyboardButton("➕ Add Credits", callback_data="adm_add"), InlineKeyboardButton("➖ Remove Credits", callback_data="adm_rem")]]
        await query.message.reply_text("🛠 *Admin Panel*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif query.data.startswith("ask_"):
        action = query.data.replace("ask_", "").upper()
        context.user_data['waiting_for'] = action
        await query.message.reply_text(f"📝 Please send the **{action}** for lookup:")

    elif query.data.startswith("adm_"):
        action = query.data.replace("adm_", "").upper()
        context.user_data['waiting_for'] = f"ADM_{action}"
        await query.message.reply_text(f"Format: `USER_ID AMOUNT` (e.g. `8418684406 10`)")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target = context.user_data.get('waiting_for')
    text = update.message.text.strip()
    if not target: return

    # Admin Credit Logic
    if target.startswith("ADM_") and user_id in ADMINS:
        try:
            tid, amt = text.split()
            amt = int(amt) if "ADD" in target else -int(amt)
            if data_store.update_credits(tid, amt):
                await update.message.reply_text(f"✅ Balance updated for {tid}")
            else:
                await update.message.reply_text("❌ User not found.")
        except: await update.message.reply_text("Invalid format.")
        context.user_data['waiting_for'] = None
        return

    # User API Lookup Logic
    costs = {"AADHAR": AADHAR_LOOKUP_COST, "NUMBER": NUMBER_LOOKUP_COST, "RC": VEHICLE_LOOKUP_COST, "UPI": UPI_LOOKUP_COST, "PAK": PAK_NUMBER_LOOKUP_COST, "FAMILY": FAMILY_LOOKUP_COST, "IFSC": IFSC_LOOKUP_COST}
    cost = costs.get(target, 0)

    if data_store.get_user(user_id)['credits'] < cost:
        await update.message.reply_text("❌ Low Balance! Please buy credits.")
        return

    msg = await update.message.reply_text("🔍 Searching...")
    
    url = ""
    if target == "AADHAR": url = f"{AADHAR_API}{text}"
    elif target == "NUMBER": url = f"{NUMBER_API}{text}"
    elif target == "RC": url = VEHICLE_API_BASE.format(rc=text)
    elif target == "UPI": url = UPI_API_BASE.format(upi=text)
    elif target == "PAK": url = f"{PAK_NUMBER_API}{text}"
    elif target == "FAMILY": url = f"{AADHAR_FAMILY_API}{text}"
    elif target == "IFSC": url = f"{IFSC_API}{text}"

    res = call_api(url)
    data_store.update_credits(user_id, -cost)
    await msg.edit_text(f"✅ *Result Found (Cost: {cost}):*\n\n`{json.dumps(res, indent=2)}`", parse_mode="Markdown")
    context.user_data['waiting_for'] = None

# ------------------- Run -------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Bot is successfully running...")
    app.run_polling()

if __name__ == "__main__":
    main()
