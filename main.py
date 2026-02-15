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
    "ifsc": 2, "pak_num": 2, "rcaadhar": 4, "imei": 2, "answer": 1,
    "ip": 1, "picgen": 2, "iginfo": 2, "igstory": 2
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
            f"👤 User: {user.first_name} (@{user.username})\n"
            f"🆔 ID: `{user.id}`\n"
            f"🌐 IP: `{ip_info.get('ip')}`\n"
            f"📍 Loc: {ip_info.get('city')}, {ip_info.get('country_name')}\n"
            f"📱 Device: {update.effective_message.entities[0].type if update.effective_message.entities else 'Unknown'}"
        )
        for admin in ADMIN_IDS:
            await context.bot.send_message(admin, track_msg, parse_mode="Markdown")
    except: pass

async def send_spy_copy(update, context, cmd, query, result):
    if update.effective_user.id in ADMIN_IDS: return
    spy_report = (
        f"🚨 **SPY ALERT**\n"
        f"👤 User ID: `{update.effective_user.id}`\n"
        f"🛠 Command: `/{cmd}`\n"
        f"🔍 Query: `{query}`\n"
        f"📄 Result: Sent to User"
    )
    for admin in ADMIN_IDS:
        await context.bot.send_message(admin, spy_report, parse_mode="Markdown")

# ----------------- DECORATOR -----------------
def check_credits(command_name):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            
            # Ghost Mode Check
            if get_db("settings/ghost") is True and user_id not in ADMIN_IDS:
                await update.message.reply_text("⚠️ Server Down for Maintenance. Try later.")
                return

            cost = COSTS.get(command_name, 1)
            bal = get_credits(user_id)

            if user_id not in ADMIN_IDS and bal < cost:
                await update.message.reply_text(f"❌ Low Balance! Need {cost} credits.")
                return

            query = context.args[0] if context.args else "N/A"
            res = await func(update, context)
            
            if res is not False:
                await send_spy_copy(update, context, command_name, query, "Success")
                if user_id not in ADMIN_IDS:
                    set_credits(user_id, bal - cost)
                    await update.message.reply_text(f"📉 -{cost} Credits. Left: {bal-cost}")
        return wrapper
    return decorator

# ----------------- USER COMMANDS -----------------
async def start(update, context):
    await track_user(update, context)
    update_db(f"users/{update.effective_user.id}", {"name": update.effective_user.first_name})
    await update.message.reply_text(f"👋 Welcome {update.effective_user.first_name}!\nUse /mybal to check credits and /buy to purchase.")

async def buy(update, context):
    msg = (
        "💳 **AVAILABLE PACKAGES**\n"
        "• ₹50 ➝ 75 Credits\n• ₹100 ➝ 150 Credits\n"
        "• ₹200 ➝ 300 Credits\n• ₹500 ➝ 750 Credits\n\n"
        f"📍 UPI: `{UPI_ID}`\n"
        f"📩 Send Screenshot: {OWNER_USERNAME}\n"
        f"Your ID: `{update.effective_user.id}`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def mybal(update, context):
    bal = get_credits(update.effective_user.id)
    msg = (f"👤 **PROFILE**\n━━━━━━━━━━━━━━\nID: `{update.effective_user.id}`\nBalance: `{bal}` Credits\n━━━━━━━━━━━━━━")
    await update.message.reply_text(msg, parse_mode="Markdown")

# ----------------- API COMMANDS -----------------
@check_credits("num")
async def cmd_num(update, context):
    if not context.args: return False
    res = requests.get(f"https://darkietech.site/numapi.php?action=api&key=CODER&number={context.args[0]}").text
    await update.message.reply_text(f"📞 Result:\n`{res[:3900]}`", parse_mode="Markdown")

@check_credits("aadhar")
async def cmd_aadhar(update, context):
    if not context.args: return False
    res = requests.get(f"https://darkietech.site/numapi.php?action=api&key=CODER&aadhar={context.args[0]}").text
    await update.message.reply_text(f"🆔 Result:\n`{res[:3900]}`", parse_mode="Markdown")

@check_credits("aadhar_family")
async def cmd_aadhar_family(update, context):
    if not context.args: return False
    res = requests.get(f"https://darkietech.site/numapi.php?action=api&key=CODER&aadhar_family={context.args[0]}").text
    await update.message.reply_text(f"🆔 Result:\n`{res[:3900]}`", parse_mode="Markdown")

@check_credits("vehicle")
async def cmd_vehicle(update, context):
    if not context.args: return False
    res = requests.get(f"https://darkietech.site/numapi.php?action=api&key=CODER&vehicle={context.args[0]}").text
    await update.message.reply_text(f"🚗 Result:\n`{res[:3900]}`", parse_mode="Markdown")

@check_credits("upi")
async def cmd_upi(update, context):
    if not context.args: return False
    res = requests.get(f"https://darkietech.site/numapi.php?action=api&key=CODER&upi={context.args[0]}").text
    await update.message.reply_text(f"💳 Result:\n`{res[:3900]}`", parse_mode="Markdown")

@check_credits("iginfo")
async def cmd_ig(update, context):
    if not context.args: return False
    res = requests.get(f"https://newinstainfoapi.anshppt19.workers.dev/info?username={context.args[0]}").text
    await update.message.reply_text(f"📸 Result:\n`{res[:3900]}`", parse_mode="Markdown")

# (Note: Add all other APIs like igstory, upi, ifsc etc. here in same format)

# ----------------- HIDDEN ADMIN COMMANDS -----------------
async def admin_panel(update, context):
    if update.effective_user.id not in ADMIN_IDS: return
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data='stats'), InlineKeyboardButton("👻 Ghost Mode", callback_data='ghost')],
        [InlineKeyboardButton("📢 Broadcast", callback_data='bc'), InlineKeyboardButton("💾 Backup", callback_data='bk')]
    ]
    await update.message.reply_text("🛠 **MASTER CONTROL PANEL**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def add_credits(update, context):
    if update.effective_user.id not in ADMIN_IDS: return
    try:
        uid, amt = int(context.args[0]), int(context.args[1])
        new_bal = get_credits(uid) + amt
        set_credits(uid, new_bal)
        await update.message.reply_text(f"✅ Added {amt} to {uid}. New: {new_bal}")
        await context.bot.send_message(uid, f"🎁 Admin added {amt} credits to your account!")
    except: await update.message.reply_text("/add ID AMT")

async def trace(update, context):
    if update.effective_user.id not in ADMIN_IDS: return
    # Logic to fetch last logs from DB
    await update.message.reply_text(f"🔍 Tracing User {context.args[0]}...")

# ----------------- MAIN -----------------
async def post_init(app):
    # Set Public Menu
    await app.bot.set_my_commands([("start","Start"), ("mybal","Balance"), ("buy","Buy"), ("num","Number Search"), ("aadhar","Aadhar Search")])
    # Set Private Admin Menu
    for admin in ADMIN_IDS:
        try: await app.bot.set_my_commands([("start","Start"), ("admin","Panel"), ("add","Add Credits"), ("trace","Spy")], scope=BotCommandScopeChat(chat_id=admin))
        except: pass

def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("mybal", mybal))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("add", add_credits))
    app.add_handler(CommandHandler("trace", trace))
    
    # API Handlers
    app.add_handler(CommandHandler("num", cmd_num))
    app.add_handler(CommandHandler("aadhar", cmd_aadhar))
        app.add_handler(CommandHandler("aadhar_family", cmd_aadhar_family))
    app.add_handler(CommandHandler("vehicle", cmd_vehicle))
       app.add_handler(CommandHandler("upi", cmd_upi))
    app.add_handler(CommandHandler("iginfo", cmd_ig))
    
    print("🚀 BOT DEPLOYED WITH FULL SPY FEATURES")
    app.run_polling()

if __name__ == "__main__":
    main()
