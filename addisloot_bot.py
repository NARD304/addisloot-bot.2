import telebot
from telebot import types
import requests
import json
import os
import time
import random
import string

# ============================================================
# 1. CONFIG (Load from Railway Env Variables)
# ============================================================
BOT_TOKEN = os.environ.get("8998441498:AAEV-jEkIwkxCoMpkKNSlfscedz25C_bdVs")
ADMIN_CHAT_ID = os.environ.get("1049263489") 

if not BOT_TOKEN: BOT_TOKEN = "DUMMY_TOKEN"
if not ADMIN_CHAT_ID: ADMIN_CHAT_ID = "123456789"

SHEGERPAY_API_KEY = "sk_live_jpI-xxTgrR3Xj_bRSzoVqEC5wSiLroxV"
PAYMENT_PROVIDER = "telebirr"
MERCHANT_PAY_TO = "0983762777"

# ============================================================
# 2. EMOJIS
# ============================================================
E_GAME = "\U0001F3AE"
E_DIAMOND = "\U0001F48E"
E_MONEY = "\U0001F4B0"
E_FIRE = "\U0001F525"
E_ROCKET = "\U0001F680"
E_CHECK = "\u2705"
E_CROSS = "\u274C"
E_WARNING = "\u26A0\uFE0F"
E_SHIELD = "\U0001F6E1\uFE0F"
E_LIGHTNING = "\u26A1"
E_PACKAGE = "\U0001F4E6"
E_HELP = "\u2753"
E_WAVE = "\U0001F44B"
E_ID = "\U0001F194"
E_CARD = "\U0001F4B3"
E_RECEIPT = "\U0001F9FE"
E_SEARCH = "\U0001F50D"
E_HOME = "\U0001F3E0"
E_CLOCK = "\u23F3"
E_PERSON = "\U0001F464"
E_PHONE = "\U0001F4F1"
E_BELL = "\U0001F514"
E_CHAT = "\U0001F4AC"
E_TRUCK = "\U0001F69A"

# ============================================================
# 3. GAME CATALOG
# ============================================================
CATALOG = {
    "pubg": {
        "name": "PUBG Mobile",
        "product": "UC",
        "icon": E_GAME,
        "packages": [
            {"id": "pubg_60", "name": "60 UC", "price": 220, "service_code": "404"},
            {"id": "pubg_325", "name": "325 UC", "price": 800, "service_code": "405"},
            {"id": "pubg_660", "name": "660 UC", "price": 1500, "service_code": "406"},
            {"id": "pubg_1800", "name": "1800 UC", "price": 3200, "service_code": "407"},
            {"id": "pubg_3850", "name": "3850 UC", "price": 8400, "service_code": "408"}
        ]
    },
    "freefire": {
        "name": "Free Fire",
        "product": "Diamonds",
        "icon": E_FIRE,
        "packages": [
            {"id": "ff_100", "name": "100 Diamonds", "price": 220, "service_code": "FT_SERVICE_CODE_FF_100"},
            {"id": "ff_310", "name": "310 Diamonds", "price": 500, "service_code": "FT_SERVICE_CODE_FF_310"},
            {"id": "ff_520", "name": "520 Diamonds", "price": 820, "service_code": "FT_SERVICE_CODE_FF_520"},
            {"id": "ff_1080", "name": "1080 Diamonds", "price": 1530, "service_code": "FT_SERVICE_CODE_FF_1080"},
            {"id": "ff_2200", "name": "2200 Diamonds", "price": 3750, "service_code": "FT_SERVICE_CODE_FF_2200"}
        ]
    }
}

# ============================================================
# 4. DATABASE
# ============================================================
DB_FILE = "orders.json"

def load_orders():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}

def save_orders(data):
    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def create_order(order):
    data = load_orders()
    data[order["id"]] = order
    save_orders(data)
    return order

def get_order(order_id):
    data = load_orders()
    return data.get(order_id)

def update_order(order_id, changes):
    data = load_orders()
    if order_id not in data: return None
    data[order_id].update(changes)
    save_orders(data)
    return data[order_id]

def get_user_orders(user_id):
    data = load_orders()
    orders = [order for order in data.values() if str(order["user_id"]) == str(user_id)]
    return sorted(orders, key=lambda x: x["created_at"], reverse=True)

def get_pending_orders():
    data = load_orders()
    return [order for order in data.values() if order["status"] == "paid"]

# ============================================================
# 5. ORDER ID & MONEY
# ============================================================
def generate_order_id():
    timestamp = str(int(time.time() * 1000))[-7:]
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return "AL" + timestamp + random_part

def money(amount):
    return f"{amount:,} Birr"

# ============================================================
# 6. SHEGERPAY VERIFICATION
# ============================================================
SHEGERPAY_BASE_URL = "https://api.shegerpay.com/api/v1"

def verify_payment(transaction_reference, amount):
    payload = {
        "provider": PAYMENT_PROVIDER,
        "transaction_id": transaction_reference,
        "amount": amount
    }
    try:
        response = requests.post(
            SHEGERPAY_BASE_URL + "/verify",
            json=payload,
            headers={"X-API-Key": SHEGERPAY_API_KEY, "Content-Type": "application/json"},
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        return {"verified": result.get("verified", False)}
    except Exception as error:
        print(f"SHEGERPAY ERROR: {error}")
        return {"verified": False, "error": "verification_service_error"}

# ============================================================
# 7. BOT INIT
# ============================================================
bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}

# ============================================================
# 8. MENUS
# ============================================================
def main_menu():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(E_GAME + " PUBG Mobile UC", callback_data="game_pubg"),
        types.InlineKeyboardButton(E_FIRE + " Free Fire Diamonds", callback_data="game_freefire")
    )
    keyboard.add(
        types.InlineKeyboardButton(E_PACKAGE + " My Orders", callback_data="orders"),
        types.InlineKeyboardButton(E_CHAT + " Support", url="https://t.me/Kuro4321")
    )
    return keyboard

def welcome_message(name):
    return (E_WAVE + " <b>WELCOME TO ADDISLOOT!</b>\n\nHello <b>" + name + "</b>! " + E_GAME + "\n\n" + 
            E_DIAMOND + " <b>GAME TOP-UP STORE</b>\n\n" + E_LIGHTNING + " Fast top-ups\n" + 
            E_MONEY + " Pay in Birr\n" + E_SHIELD + " Secure payment\n" + E_CHECK + " Payment verification\n\n" + 
            E_GAME + " <b>Choose your game below:</b>")

@bot.message_handler(commands=["start"])
def start_command(message):
    name = message.from_user.first_name or "Gamer"
    bot.send_message(message.chat.id, welcome_message(name), parse_mode="HTML", reply_markup=main_menu())

# ============================================================
# 9. CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "home")
def home_callback(call):
    bot.answer_callback_query(call.id)
    name = call.from_user.first_name or "Gamer"
    bot.edit_message_text(welcome_message(name), call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def game_callback(call):
    bot.answer_callback_query(call.id)
    game_id = call.data.replace("game_", "", 1)
    game = CATALOG.get(game_id)
    if not game: return
    
    keyboard = types.InlineKeyboardMarkup()
    for package in game["packages"]:
        keyboard.add(types.InlineKeyboardButton(E_DIAMOND + " " + package["name"] + "  -  " + money(package["price"]), 
                                                callback_data="package:" + game_id + ":" + package["id"]))
    keyboard.add(types.InlineKeyboardButton(E_HOME + " Main Menu", callback_data="home"))
    
    bot.edit_message_text(game["icon"] + " <b>" + game["name"] + "</b>\n\nChoose your package:", 
                          call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("package:"))
def package_callback(call):
    parts = call.data.split(":")
    if len(parts) != 3: return
    game_id, package_id = parts[1], parts[2]
    game, package = CATALOG.get(game_id), next((item for item in CATALOG.get(game_id, {}).get("packages", []) if item["id"] == package_id), None)
    if not game or not package: return
    
    user_state[call.from_user.id] = {"game_id": game_id, "package_id": package_id}
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, 
        E_ID + " <b>SEND YOUR PLAYER ID</b>\n\nPlease send your " + game["name"] + " Player ID.", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "orders")
def orders_callback(call):
    bot.answer_callback_query(call.id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(E_HOME + " Main Menu", callback_data="home"))
    bot.edit_message_text(E_PACKAGE + " <b>YOUR ORDERS</b>\n\nCheck your status via /myorders", 
                          call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=keyboard)

# ============================================================
# 10. TEXT HANDLER (PAYMENT FLOW)
# ============================================================
@bot.message_handler(func=lambda message: True, content_types=["text"])
def text_handler(message):
    text = message.text.strip()
    user_id = message.from_user.id
    if text.startswith("/"): return

    # Player ID Stage
    if user_id in user_state:
        state = user_state[user_id]
        game = CATALOG.get(state["game_id"])
        if not game: del user_state[user_id]; return
        package = next((item for item in game["packages"] if item["id"] == state["package_id"]), None)
        if not package: del user_state[user_id]; return

        order_id = generate_order_id()
        order = {
            "id": order_id, "user_id": user_id, 
            "username": (message.from_user.username or message.from_user.first_name or "Unknown"),
            "game": game["name"], "package": package["name"], "amount": package["price"],
            "player_id": text, "status": "awaiting_payment", "transaction_reference": "", "created_at": time.time()
        }
        create_order(order)
        del user_state[user_id]

        bot.send_message(message.chat.id, 
            E_CARD + " <b>PAYMENT</b>\n\nPay <b>" + money(package["price"]) + "</b> to:\n<code>" + MERCHANT_PAY_TO + "</code>\n\n" + 
            E_RECEIPT + " After sending, reply with your Transaction Reference.", parse_mode="HTML")
        return

    # Transaction Reference Stage
    if len(text) < 4:
        bot.send_message(message.chat.id, "Please send your transaction reference after paying.")
        return

    orders = get_user_orders(user_id)
    active_order = next((order for order in orders if order["status"] == "awaiting_payment"), None)
    if not active_order:
        bot.send_message(message.chat.id, E_HELP + " Use /start to make an order first.", parse_mode="HTML")
        return

    bot.send_message(message.chat.id, E_CLOCK + " <b>VERIFYING...</b>", parse_mode="HTML")
    result = verify_payment(text, active_order["amount"])

    if result.get("verified"):
        update_order(active_order["id"], {"status": "paid", "transaction_reference": text})
        bot.send_message(message.chat.id, E_CHECK + " <b>PAYMENT CONFIRMED!</b>\n\nWe are sending your top-up now. Wait a few moments.", parse_mode="HTML")
        
        # NOTIFICATION TO ADMIN: This is where you get the order
        bot.send_message(ADMIN_CHAT_ID, 
            E_BELL + " <b>NEW ORDER READY</b>\n\n" +
            "Order: <code>" + active_order["id"] + "</code>\n" +
            "Game: " + active_order["game"] + "\n" +
            "Package: " + active_order["package"] + " (" + active_order.get("service_code", "N/A") + ")\n" +
            "Player ID: <code>" + str(active_order["player_id"]) + "</code>", parse_mode="HTML")
    else:
        update_order(active_order["id"], {"status": "pending_review", "transaction_reference": text})
        bot.send_message(message.chat.id, E_SEARCH + " <b>PAYMENT NEEDS REVIEW</b>\n\nOur team will check it manually.", parse_mode="HTML")
        bot.send_message(ADMIN_CHAT_ID, E_WARNING + " MANUAL REVIEW: " + active_order["id"])

# ============================================================
# 11. NEW ADMIN BATCH COMMANDS
# ============================================================
@bot.message_handler(commands=["batch"])
def batch_command(message):
    if str(message.chat.id) != str(ADMIN_CHAT_ID): return
    
    pending = get_pending_orders()
    if not pending:
        bot.reply_to(message, "No pending orders to fulfill right now.")
        return

    lines = ["📦 <b>PENDING BATCH</b>\n\n"]
    for i, order in enumerate(pending, 1):
        lines.append(f"{i}. ID: <code>{order['player_id']}</code>")
        lines.append(f"   📦 {order['game']} - {order['package']}")
        lines.append(f"   🔑 Code: {order.get('service_code', 'N/A')}")
        lines.append("")
    
    bot.reply_to(message, "\n".join(lines), parse_mode="HTML")

@bot.message_handler(commands=["deliverall"])
def deliver_all_command(message):
    if str(message.chat.id) != str(ADMIN_CHAT_ID): return
    
    pending = get_pending_orders()
    if not pending:
        bot.reply_to(message, "No orders to deliver.")
        return

    count = 0
    for order in pending:
        update_order(order["id"], {"status": "delivered"})
        try:
            bot.send_message(order["user_id"], E_CHECK + " <b>TOP-UP DELIVERED!</b>\n\nEnjoy your game!", parse_mode="HTML")
            count += 1
        except:
            pass
    
    bot.reply_to(message, f"✅ Delivered {count} orders successfully!")

@bot.message_handler(commands=["myorders"])
def myorders_command(message):
    orders = get_user_orders(message.from_user.id)[:5]
    if not orders:
        bot.send_message(message.chat.id, E_PACKAGE + " You have no orders.")
        return
    text = E_PACKAGE + " <b>YOUR ORDERS</b>\n\n"
    for o in orders:
        text += "ID: <code>" + o["id"] + "</code>\nStatus: " + o["status"].title() + "\n\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ============================================================
# 12. START BOT
# ============================================================
if __name__ == "__main__":
    print("AddisLoot Bot is running (Batch Method)...")
    bot.infinity_polling()
