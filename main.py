import logging
import requests
import json
import asyncio
from datetime import datetime
from telegram import Update, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ----------------- CONFIGURATION -----------------
TOKEN = "8338232613:AAGBCyTM4lm3X9KO2VPuIcF6kZsXkPxjgEY"
ADMIN_IDS = [8418684406]
OWNER_USERNAME = "@atercyber"
UPI_ID = "kumarishant8813@ptyes"
PROJECT_ID = "red-eyes-6bc10"
API_KEY = "AIzaSyBxSp7lt9Is6CZHSjHICdl0MPgkWiCzcew"
BASE_URL = f"https://{PROJECT_ID}-default-rtdb.firebaseio.com"

# ----------------- CREDIT COSTS -----------------
COSTS = {
    "num": 5, "aadhar": 4, "family": 5, "vehicle": 3, "upi": 3,
    "ifsc": 1, "pincode": 1, "insta": 2, "ip": 1, "pan": 5,
    "imei": 3, "ff": 3, "bgmi": 3, "pak": 5
}

# ----------------- DATABASE HELPERS -----------------
def get_db(path):
    try:
        r = requests.get(f"{BASE_URL}/{path}.json?auth={API_KEY}")
        return r.json() if r.json() is not None else {}
    except: return {}

def update_db(path, data):
    requests.patch(f"{BASE_URL}/{path}.json?auth={API_KEY}", json=data)

def get_credits(user_id):
    res = get_db(f"credits/{user_id}")
    return res if isinstance(res, int) else 0

def set_credits(user_id, amt):
    requests.put(f"{BASE_URL}/credits/{user_id}.json?auth={API_KEY}", json=amt)

# ----------------- SPY & TRACKING LOGIC -----------------
async def track_user(update, context):
    user = update.effective_user
    try:
        ip_info = requests.get("https://ipapi.co/json/").json()
        track_msg = (
            f"🕵️ **NEW TARGET LOGGED**\n"
            f"👤 User: {user.first_name}\n"
            f"🆔 ID: `{user.id}`\n"
            f"🌐 IP: `{ip_info.get('ip')}`"
        )
        for admin in ADMIN_IDS:
            await context.bot.send_message(admin, track_msg, parse_mode="Markdown")
    except: pass

# ----------------- DECORATOR -----------------
def check_credits(command_name):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            if get_db("settings/ghost") is True and user_id not in ADMIN_IDS:
                await update.message.reply_text("⚠️ Server Down for Maintenance.")
                return

            cost = COSTS.get(command_name, 1)
            bal = get_credits(user_id)

            if user_id not in ADMIN_IDS and bal < cost:
                await update.message.reply_text(f"❌ Low Balance! Need {cost} credits.")
                return

            if not context.args:
                await update.message.reply_text(f"❌ Usage: /{command_name} [input]")
                return False

            res = await func(update, context)
            if res is not False and user_id not in ADMIN_IDS:
                set_credits(user_id, bal - cost)
                await update.message.reply_text(f"📉 -{cost} Credits. Left: {bal-cost}")
        return wrapper
    return decorator

# ----------------- USER COMMANDS -----------------
async def start(update, context):
    user = update.effective_user
    await track_user(update, context)
    update_db(f"users/{user.id}", {"name": user.first_name})
    bal = get_credits(user.id)
    
    msg = (
        "🔥 **OWNER INFO BOT** 🔥\n\n"
        f"👋 Welcome! {user.first_name}\n\n"
        f"💳 **Credits:** `{bal}`\n"
        f"🔹 **Diamond Credits:** `Unlimited`\n"
        f"👑 **Owner:** {OWNER_USERNAME}\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📱 `/num` number\n"
        "🪪 `/aadhar` number\n"
        "🚗 `/vehicle` rc\n"
        "🇵🇰 `/pak` number\n"
        "📸 `/insta` username\n"
        "🎮 `/ff` uid\n"
        "🎯 `/bgmi` id\n"
        "📱 `/imei` imei\n"
        "🌐 `/ip` ip\n"
        "🏦 `/ifsc` code\n"
        "📮 `/pincode` pin\n"
        "🪪 `/pan` pan\n"
        "👨‍👩‍👧 `/family` aadhar\n"
        "━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ----------------- API HANDLERS -----------------

@check_credits("num")
async def cmd_num(update, context):
    res = requests.get(f"https://darkietech.site/numapi.php?action=api&key=CODER&number={context.args[0]}").text
    await update.message.reply_text(f"📞 Result:\n`{res[:3900]}`", parse_mode="Markdown")

@check_credits("ifsc")
async def cmd_ifsc(update, context):
    r = requests.get(f"https://ifsc.razorpay.com/{context.args[0]}")
    if r.status_code == 200:
        data = r.json()
        res = f"🏦 Bank: {data.get('BANK')}\n📍 Branch: {data.get('BRANCH')}\n🏙 City: {data.get('CITY')}"
    else: res = "Invalid IFSC"
    await update.message.reply_text(f"🏦 Result:\n`{res}`", parse_mode="Markdown")

@check_credits("pincode")
async def cmd_pin(update, context):
    r = requests.get(f"https://api.postalpincode.in/pincode/{context.args[0]}")
    data = r.json()
    if data[0]['Status'] == 'Success':
        office = data[0]['PostOffice'][0]
        res = f"📮 Area: {office['Name']}\n🏘 District: {office['District']}\n🚩 State: {office['State']}"
    else: res = "Invalid Pincode"
    await update.message.reply_text(f"📮 Result:\n`{res}`", parse_mode="Markdown")

@check_credits("ip")
async def cmd_ip(update, context):
    r = requests.get(f"http://ip-api.com/json/{context.args[0]}").json()
    res = f"🌐 IP: {r.get('query')}\n📍 Country: {r.get('country')}\n🏢 ISP: {r.get('isp')}"
    await update.message.reply_text(f"🌐 Result:\n`{res}`", parse_mode="Markdown")

@check_credits("insta")
async def cmd_ig(update, context):
    res = requests.get(f"https://newinstainfoapi.anshppt19.workers.dev/info?username={context.args[0]}").text
    await update.message.reply_text(f"📸 Result:\n`{res[:3900]}`", parse_mode="Markdown")

@check_credits("family")
async def cmd_family(update, context):
    res = requests.get(f"https://darkietech.site/numapi.php?action=api&key=CODER&aadhar_family={context.args[0]}").text
    await update.message.reply_text(f"👨‍👩‍👧 Result:\n`{res[:3900]}`", parse_mode="Markdown")

# Dummy handlers for other commands (Replace with actual API URLs when you have them)
@check_credits("ff")
async def cmd_ff(update, context):
    await update.message.reply_text("🎮 Free Fire API not linked. Contact Admin.")

@check_credits("pan")
async def cmd_pan(update, context):
    await update.message.reply_text("🪪 PAN API not linked. Contact Admin.")

# ----------------- ADMIN COMMANDS -----------------
async def add_credits(update, context):
    if update.effective_user.id not in ADMIN_IDS: return
    try:
        uid, amt = int(context.args[0]), int(context.args[1])
        new_bal = get_credits(uid) + amt
        set_credits(uid, new_bal)
        await update.message.reply_text(f"✅ Added {amt} credits to {uid}")
    except: await update.message.reply_text("/add ID AMT")

# ----------------- MAIN -----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_credits))
    
    # API Handlers अलाइनमेंट फिक्स किया गया
    app.add_handler(CommandHandler("num", cmd_num))
    app.add_handler(CommandHandler("ifsc", cmd_ifsc))
    app.add_handler(CommandHandler("pincode", cmd_pin))
    app.add_handler(CommandHandler("ip", cmd_ip))
    app.add_handler(CommandHandler("insta", cmd_ig))
    app.add_handler(CommandHandler("family", cmd_family))
    app.add_handler(CommandHandler("ff", cmd_ff))
    app.add_handler(CommandHandler("pan", cmd_pan))
    
    print("🚀 BOT STARTED SUCCESSFULLY")
    app.run_polling()

if __name__ == "__main__":
    main()
