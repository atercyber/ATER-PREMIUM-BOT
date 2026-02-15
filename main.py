        
# RANA INFO 2.0 Bot - Merged single-file implementation

import json
import os
import logging
import asyncio
import requests
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ------------------- Configuration (config.py) -------------------
BOT_TOKEN = "8338232613:AAEi995yXNytZt6HvVBxWcf3HM1M4yxvPoY"
# Admins and general settings
ADMINS = {8418684406}
WELCOME_IMAGE = "https://ibb.co/8DC6NQ71"

# APIs
AADHAR_API = "https://darkietech.site/numapi.php?action=api&key=CODER&aadhaf="
NUMBER_API = "https://darkietech.site/numapi.php?action=api&key=CODER&numberr="
NUMBER_API_BACKUP = "https://darkietech.site/numapi.php?action=api&key=CODER&number="
AADHAR_FAMILY_API = "https://darkietech.site/numapi.php?action=api&key=CODER&aadhar_family="
UPI_API_BASE = "https://darkietech.site/numapi.php?action=api&key=CODER&upi"
VEHICLE_API_BASE = "https://darkietech.site/numapi.php?action=api&key=CODER&vehicle="

# Costs
VEHICLE_LOOKUP_COST = 3
UPI_LOOKUP_COST = 3
IFSC_LOOKUP_COST = 2
AADHAR_LOOKUP_COST = 4
NUMBER_LOOKUP_COST = 5
PAK_NUMBER_LOOKUP_COST = 2
AADHAR_FAMILY_LOOKUP_COST = 5

# Defaults / constants
BLOCKED_NUMBERS = {
   

DEFAULT_CHANNELS = [
    {"id": "-1003019430565", "link": "https://t.me/+ax8_tkp3pts4NDE1", "name": "📢  MAIN CHANNEL"},
]

# ------------------- Logger (utils/logger.py) -------------------
def configure_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

# ------------------- Data Store (storage/data_store.py) -------------------
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data_store.json')
DEFAULT_DATA = {
    "users": {},
    "redeem_codes": {},
    "admins": [8418684406] "nned_users": [],
    "channels": []
}

class DataStore:
    def __init__(self, path=DATA_FILE):
        self.path = path
        if not os.path.exists(self.path):
            self._write(DEFAULT_DATA.copy())
        self._load()
        self._pending = {}

    def _load(self):
        with open(self.path, 'r') as f:
            self._data = json.load(f)

    def _write(self, data):
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=4)
        self._data = data

    def save(self):
        self._write(self._data)

    def get_channels(self):
        return self._data.get('channels') or []

    def save_channels(self, channels):
        self._data['channels'] = channels
        self.save()

    def get_admins(self):
        return set(self._data.get('admins', []))

    def ensure_user(self, user_id: int, default_credits=0, ref_arg=None):
        users = self._data.setdefault('users', {})
        if str(user_id) not in users:
            users[str(user_id)] = {"credits": default_credits, "referrals": [], "referrer": None}
            if ref_arg and len(ref_arg) > 0 and str(ref_arg[0]).startswith('ref_'):
                try:
                    referrer = int(str(ref_arg[0]).split('_')[1])
                    if referrer != user_id:
                        users[str(user_id)]['referrer'] = referrer
                except: pass
            self.save()

    def get_credits(self, user_id: int) -> int:
        return self._data['users'].get(str(user_id), {}).get('credits', 0)

    def debit_credits(self, user_id: int, amount: int) -> bool:
        users = self._data['users']
        u = users.setdefault(str(user_id), {"credits":0,"referrals":[],"referrer":None})
        if u['credits'] < amount:
            return False
        u['credits'] -= amount
        self.save()
        return True

    def add_credits(self, user_id: int, amount: int):
        users = self._data['users']
        u = users.setdefault(str(user_id), {"credits":0,"referrals":[],"referrer":None})
        u['credits'] += amount
        self.save()

    def get_referrals(self, user_id: int):
        return self._data['users'].get(str(user_id), {}).get('referrals', [])

    def redeem_code(self, code: str) -> bool:
        rc = self._data.get('redeem_codes', {})
        if code in rc:
            self.add_credits(0, rc.pop(code))
            self.save()
            return True
        return False

    def is_banned(self, user_id: int) -> bool:
        return user_id in self._data.get('banned_users', [])

    def ban_user(self, user_id: int):
        lst = self._data.setdefault('banned_users', [])
        if user_id not in lst:
            lst.append(user_id)
            self.save()

    def unban_user(self, user_id: int):
        lst = self._data.setdefault('banned_users', [])
        if user_id in lst:
            lst.remove(user_id)
            self.save()

    def set_pending_action(self, admin_id: int, action: str):
        self._pending[admin_id] = action

    def pop_pending_action(self, admin_id: int) -> Optional[str]:
        return self._pending.pop(admin_id, None)

    def get_buy_text(self):
        return """💳 *Get More Credits*

**Available Packages:**
• *₹50* ➝  75 Credits
• *₹100* ➝  150 Credits
• *₹200* ➝  300 Credits
• *₹300* ➝  450 Credits
• *₹500* ➝  750 Credits
• *₹1000* ➝  1500 Credits

**📩 To Purchase:** Message 👉 @atercyber"

data_store = DataStore()

# ------------------- Membership Service (services/membership.py) -------------------
async def check_membership(bot, user_id: int, channels: list) -> bool:
    logger = logging.getLogger(__name__)
    try:
        for ch in channels:
            member = await bot.get_chat_member(ch['id'], user_id)
            logger.info(f"Checking membership for user {user_id} in channel {ch['id']} - Status: {member.status}")
            if member.status not in ['member', 'administrator', 'creator']:
                logger.warning(f"User {user_id} is not a member of channel {ch['id']}")
                return False
        logger.info(f"User {user_id} is a member of all required channels")
        return True
    except Exception as e:
        logger.exception(f'Membership check failed for user {user_id}: {str(e)}')
        return False

# ------------------- API Clients (services/api_clients.py) -------------------
logger = logging.getLogger(__name__)

def fetch_aadhar_info(aadhar_number: str) -> dict:
    try:
        resp = requests.get(f"{AADHAR_API}{aadhar_number}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return {"status":"failed","error":"No data"}
        details = data[0] if isinstance(data, list) and data else data
        return {"status":"success","details":details}
    except Exception as e:
        logger.exception("Aadhar API error")
        return {"status":"error","error":str(e)}

def fetch_number(number: str) -> dict:
    urls = [
        (f"{NUMBER_API}{number}", "Primary"),
        (f"{NUMBER_API_BACKUP}{number}", "Backup"),
    ]
    for url, label in urls:
        try:
            resp = requests.get(url, timeout=10, verify=False)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return {"status": "success", "details": data}
            logger.warning("%s API returned empty or invalid data", label)
        except requests.exceptions.SSLError as e:
            logger.error("%s API SSL error: %s", label, e)
        except Exception as e:
            logger.error("%s API failed: %s", label, e)
    return {"status": "error", "error": "All APIs failed to fetch number data."}

def fetch_pakistan_number(number: str) -> dict:
    try:
        resp = requests.get(f"{PAK_NUMBER_API}{number}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and "results" in data and len(data["results"])>0:
            return {"status":"success","details":data["results"]}
        return {"status":"failed","error":"No results"}
    except Exception as e:
        logger.exception("Pakistan API error")
        return {"status":"error","error":str(e)}
        
        
def fetch_pakistan_number(number: str) -> dict:
    try:
        resp = requests.get(f"{AADHAR_FAMILY_API}{AADHAR}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and "results" in data and len(data["results"])>0:
            return {"status":"success","details":data["results"]}
        return {"status":"failed","error":"No results"}
    except Exception as e:
        logger.exception("AADHAR FAMILY API error")
        return {"status":"error","error":str(e)}
        
        

def fetch_ifsc_info(ifsc_code: str) -> dict:
    try:
        resp = requests.get(f"{IFSC_API}{ifsc_code}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data or data.get('BANK') is None:
            return {"status":"failed","error":"No data"}
        return {"status":"success","details":data}
    except Exception as e:
        logger.exception("IFSC API error")
        return {"status":"error","error":str(e)}

def fetch_upi_info(upi_id: str) -> dict:
    try:
        resp = requests.get(UPI_API_BASE.format(upi=upi_id), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return {"status":"failed","error":"No data"}
        return {"status":"success","details":data}
    except Exception as e:
        logger.exception("UPI API error")
        return {"status":"error","error":str(e)}

def fetch_vehicle_info(rc_number: str) -> dict:
    try:
        resp = requests.get(VEHICLE_API_BASE.format(rc=rc_number), timeout=10)
        resp.raise_for_status()
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        if not data:
            return {"status":"failed","error":"No data"}
        return {"status":"success","details":data}
    except Exception as e:
        logger.exception("Vehicle API error")
        return {"status":"error","error":str(e)}

# ------------------- Handlers (handlers/*) -------------------
# start.py
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if data_store.is_banned(user_id):
        await update.message.reply_text("❌ You have been banned from using this bot.")
        return

    channels = data_store.get_channels() or DEFAULT_CHANNELS
    is_member = await check_membership(context.bot, user_id, channels)
    if not is_member:
        buttons = [[InlineKeyboardButton(ch['name'], url=ch['link'])] for ch in channels]
        buttons.append([InlineKeyboardButton("✅ Verify My Membership", callback_data="verify_join")])
        await update.message.reply_text(
            "⚠️ *Access Denied.* ⚠️\n\n"
            "To use this bot, you must be a member of all our channels. Please join them below and click **Verify** to gain access.",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
        return

    data_store.ensure_user(user_id, default_credits=2, ref_arg=context.args if context.args else None)

    keyboard = [
        [InlineKeyboardButton("👤 My Profile", callback_data="profile"), InlineKeyboardButton("💳 Buy Credits", callback_data="buy_credits")],
        [InlineKeyboardButton("🆔 Aadhar Info", callback_data="aadhar"), InlineKeyboardButton("📞 Number Info", callback_data="number")],
        [InlineKeyboardButton("🇵🇰 Num Info", callback_data="pak_number"), InlineKeyboardButton("🏦 IFSC Info", callback_data="ifsc")],
        [InlineKeyboardButton("💸 UPI Info", callback_data="upi"), InlineKeyboardButton("🚗 Vehicle Info", callback_data="vehicle")],
        [InlineKeyboardButton("🎟 Redeem Code", callback_data="redeem"), InlineKeyboardButton("📢 Refer & Earn", callback_data="refer_earn")],
        [InlineKeyboardButton("❓ Help", url="https://t.me/Crazyrana07")]
    ]

    if user_id in ADMINS:
        keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin")])

    await update.message.reply_photo(
        photo=WELCOME_IMAGE,
        caption=(
            "👋 *Welcome to ATER INFO 2.0!* 🤖\n\n"
            "🔎 Your reliable OSINT companion for fast and secure intelligence. 👇"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# buttons.py
async def admin_panel(query):
    keyboard = [
        [InlineKeyboardButton("📊 User Analytics", callback_data="admin_users"),
         InlineKeyboardButton("➕ Add Credits", callback_data="admin_add_credit")],
        [InlineKeyboardButton("➖ Remove Credits", callback_data="admin_remove_credit"),
         InlineKeyboardButton("👑 Manage Admins", callback_data="admin_manage_admins")],
        [InlineKeyboardButton("🎟 Create Redeem Code", callback_data="admin_redeem_create"),
         InlineKeyboardButton("📢 Send Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📸 Change Welcome Photo", callback_data="admin_change_photo"),
         InlineKeyboardButton("⚙️ Change APIs", callback_data="admin_change_apis")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="start_menu")]
    ]

    await query.message.reply_text(
        "🛠️ *Admin Management Panel*\n\n"
        "Control and monitor all bot operations from this centralized panel.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    user_id = query.from_user.id
    if user_id not in data_store.get_admins():
        await query.message.reply_text("⚠️ You are not authorized to perform this action.")
        return

    if query.data == "admin":
        await admin_panel(query)
    else:
        data_store.set_pending_action(user_id, query.data)
        await query.message.reply_text("✏️ Please send the required input for this admin action (follow the prompts).")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        await query.answer("Processing...", show_alert=False)
    except Exception:
        pass

    if data_store.is_banned(user_id):
        await query.message.reply_text("❌ You have been banned from using this bot.")
        return

    if query.data == "verify_join":
        checking_msg = await query.message.reply_text("⏳ *Checking membership status...*")
        await asyncio.sleep(1)
        channels = data_store.get_channels() or DEFAULT_CHANNELS
        is_member = await check_membership(context.bot, user_id, channels)
        try:
            await checking_msg.delete()
        except: pass
        if is_member:
            await context.bot.send_message(user_id, "✅ *Membership Verified!* You now have full access. Use /start to begin.", parse_mode="Markdown")
        else:
            await context.bot.send_message(user_id, "⚠️ *Access Denied.* ⚠️\n\nYou must be a member of all our channels. Please join them and try again.", parse_mode="Markdown")
        return

    if query.data == "profile":
        credits = data_store.get_credits(user_id)
        referrals = data_store.get_referrals(user_id)
        formatted = (
            "👤 *Your Profile Details*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 User ID: `{user_id}`\n"
            f"💰 Credits: *{credits}*\n"
            f"👥 Referrals: *{len(referrals)}*\n"
        )
        await query.message.reply_text(formatted, parse_mode="Markdown")
        return

    if query.data == "refer_earn":
        ref_link = f"https://t.me/+D4qLPRptiIFmMmQ9?start=ref_{user_id}"
        formatted = (
            "📢 *Refer and Earn!* 🎁\n\n"
            "Share your unique referral link with your friends. For every user who joins and verifies their membership using your link, you will automatically receive **+1 credit**!\n\n"
            "🔗 *Your Referral Link:*\n"
            f"`{ref_link}`\n\n"
            "Start sharing now to get free credits!"
        )
        await query.message.reply_text(formatted, parse_mode="Markdown")
        return

    if query.data == "aadhar":
        await query.message.reply_text(f"🆔 *Aadhar Information*\n\nEnter 12-digit Aadhar number (e.g., `123456789012`)\n💳 Cost: *{AADHAR_LOOKUP_COST} credit*", parse_mode="Markdown")
        context.user_data["awaiting_aadhar"] = True
        return

    if query.data == "number":
        await query.message.reply_text(f"📞 *Number Lookup*\n\nEnter 10-digit number (e.g., `98xxxxxxxx`)\n💳 Cost: *{NUMBER_LOOKUP_COST} credit*", parse_mode="Markdown")
        context.user_data["awaiting_number"] = True
        return

    if query.data == "pak_number":
        await query.message.reply_text(f"🇵🇰 *Pakistan Number Lookup*\n\nEnter 12-digit number (e.g., `923xxxxxxxxx`)\n💳 Cost: *{PAK_NUMBER_LOOKUP_COST} credit*", parse_mode="Markdown")
        context.user_data["awaiting_pak_number"] = True
        return

    if query.data == "ifsc":
        await query.message.reply_text(f"🏦 *IFSC Info*\n\nEnter a valid 11-character IFSC code (e.g., `SBIN0004843`)\n💳 Cost: *{IFSC_LOOKUP_COST} credit*", parse_mode="Markdown")
        context.user_data["awaiting_ifsc"] = True
        return

    if query.data == "upi":
        await query.message.reply_text(f"💸 *UPI Lookup*\n\nEnter a UPI ID (e.g., `9779448000@paytm`)\nNote: Example API key used internally.\n💳 Cost: *{UPI_LOOKUP_COST} credit*", parse_mode="Markdown")
        context.user_data["awaiting_upi"] = True
        return

    if query.data == "vehicle":
        await query.message.reply_text(f"🚗 *Vehicle/RC Lookup*\n\nEnter a vehicle registration number (e.g., `TS07JL0389`)\n💳 Cost: *{VEHICLE_LOOKUP_COST} credit*", parse_mode="Markdown")
        context.user_data["awaiting_vehicle"] = True
        return

    if query.data == "buy_credits":
        keyboard = [[InlineKeyboardButton("📩 Contact to Buy Credits", url="https://t.me/Crazyrana07")]]
        await query.message.reply_text(data_store.get_buy_text(), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if query.data == "redeem":
        await query.message.reply_text("🎟 *Redeem Your Code*\n\nPlease enter your redeem code to claim your credits.")
        context.user_data["awaiting_redeem"] = True
        return

    if query.data == "start_menu":
        await context.bot.send_message(user_id, "Returning to main menu. Use /start to open the menu.")
        return

    if query.data.startswith("admin"):
        await handle_admin_action(update, context, query)
        return

# messages.py
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if data_store.is_banned(user_id):
        return

    text = update.message.text.strip()

    if context.user_data.get("awaiting_redeem"):
        context.user_data["awaiting_redeem"] = False
        code = text.upper()
        if data_store.redeem_code(code):
            credits = data_store.get_credits(user_id)
            await update.message.reply_text(
                f"✅ *Redeem Successful!* 🎉\n🎟 Code: `{code}`\n💳 Credits Added. Total: *{credits}*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ *Invalid or expired code.* Please double-check and try again.")
        return

    pending = data_store.pop_pending_action(user_id)
    if pending:
        await update.message.reply_text("✅ Admin action processed.")
        return

    if context.user_data.get("awaiting_aadhar"):
        context.user_data["awaiting_aadhar"] = False
        if data_store.get_credits(user_id) < AADHAR_LOOKUP_COST:
            await update.message.reply_text(f"⚠️ You have insufficient credits. Aadhar lookup requires {AADHAR_LOOKUP_COST} credit.")
            return
        if not text.isdigit() or len(text) != 12:
            await update.message.reply_text("❌ *Invalid Aadhar Number!*\n\nPlease enter a valid 12-digit Aadhar number.", parse_mode="Markdown")
            return
        data = fetch_aadhar_info(text)
        if data.get('status') == 'success':
            data_store.debit_credits(user_id, AADHAR_LOOKUP_COST)
            await update.message.reply_text(f"*Result:*\n```{json.dumps(data, indent=2)}```", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ *Aadhar Lookup Failed!*\n\nError: {data.get('error', 'Unknown error')}", parse_mode="Markdown")
        return

    if context.user_data.get("awaiting_number"):
        context.user_data["awaiting_number"] = False
        if text in BLOCKED_NUMBERS:
            await update.message.reply_text("⚠️ *Security Alert!*\n🛑 Suspicious request denied.")
            return
        if data_store.get_credits(user_id) < NUMBER_LOOKUP_COST:
            await update.message.reply_text(f"⚠️ You have insufficient credits. Number lookup requires {NUMBER_LOOKUP_COST} credit(s).", parse_mode="Markdown")
            return
        data = fetch_number(text)
        if data.get('status') == 'success':
            data_store.debit_credits(user_id, NUMBER_LOOKUP_COST)
            await update.message.reply_text(f"*Result:*\n```{json.dumps(data, indent=2)}```", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ *Incorrect Number or No Data Found!*", parse_mode="Markdown")
        return

    if context.user_data.get("awaiting_pak_number"):
        context.user_data["awaiting_pak_number"] = False
        if data_store.get_credits(user_id) < PAK_NUMBER_LOOKUP_COST:
            await update.message.reply_text(f"⚠️ You have insufficient credits. Pakistan number lookup requires {PAK_NUMBER_LOOKUP_COST} credit.", parse_mode="Markdown")
            return
        if not text.startswith('92') or len(text) != 12 or not text.isdigit():
            await update.message.reply_text("❌ *Invalid Pakistan Number!*\n\nPlease enter a valid 12-digit number starting with `92`.", parse_mode="Markdown")
            return
        data = fetch_pakistan_number(text)
        if data.get('status') == 'success':
            data_store.debit_credits(user_id, PAK_NUMBER_LOOKUP_COST)
            await update.message.reply_text(f"*Result:*\n```{json.dumps(data, indent=2)}```", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ *Pakistan Number Lookup Failed!*", parse_mode="Markdown")
        return

    if context.user_data.get('awaiting_ifsc'):
        context.user_data['awaiting_ifsc'] = False
        if data_store.get_credits(user_id) < IFSC_LOOKUP_COST:
            await update.message.reply_text(f"⚠️ You have insufficient credits. IFSC lookup requires {IFSC_LOOKUP_COST} credit.")
            return
        if not (len(text) == 11 and text[:4].isalpha() and text[4] == '0' and text[5:].isalnum()):
            await update.message.reply_text("❌ *Invalid IFSC Code!*\n\nPlease enter a valid 11-character IFSC code (e.g., `SBIN0004843`).", parse_mode="Markdown")
            return
        data = fetch_ifsc_info(text)
        if data.get('status') == 'success':
            data_store.debit_credits(user_id, IFSC_LOOKUP_COST)
            await update.message.reply_text(f"*Result:*\n```{json.dumps(data, indent=2)}```", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ *IFSC Lookup Failed!*", parse_mode="Markdown")
        return

    if context.user_data.get('awaiting_upi'):
        context.user_data['awaiting_upi'] = False
        upi_id = text.strip()
        if "@" not in upi_id or len(upi_id) < 3:
            await update.message.reply_text("❌ *Invalid UPI ID!*\nPlease enter a valid UPI ID like `9779448000@paytm`.", parse_mode="Markdown")
            return
        if data_store.get_credits(user_id) < UPI_LOOKUP_COST:
            await update.message.reply_text(f"⚠️ You have insufficient credits. UPI lookup requires {UPI_LOOKUP_COST} credit.", parse_mode="Markdown")
            return
        data = fetch_upi_info(upi_id)
        if data.get('status') == 'success':
            data_store.debit_credits(user_id, UPI_LOOKUP_COST)
            await update.message.reply_text(f"*Result:*\n```{json.dumps(data, indent=2)}```", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ *UPI Lookup Failed!*", parse_mode="Markdown")
        return

    if context.user_data.get('awaiting_vehicle'):
        context.user_data['awaiting_vehicle'] = False
        rc_number = text.strip().upper()
        if len(rc_number) < 5:
            await update.message.reply_text("❌ *Invalid vehicle number!*\nPlease enter a valid registration number like `TS07JL0389`.", parse_mode="Markdown")
            return
        if data_store.get_credits(user_id) < VEHICLE_LOOKUP_COST:
            await update.message.reply_text(f"⚠️ You have insufficient credits. Vehicle lookup requires {VEHICLE_LOOKUP_COST} credit.", parse_mode="Markdown")
            return
        data = fetch_vehicle_info(rc_number)
        if data.get('status') == 'success':
            data_store.debit_credits(user_id, VEHICLE_LOOKUP_COST)
            await update.message.reply_text(f"*Result:*\n```{json.dumps(data, indent=2)}```", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ *Vehicle Lookup Failed!*", parse_mode="Markdown")
        return

# ------------------- Main (bot.py) -------------------
def main():
    configure_logging()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
