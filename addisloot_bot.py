import telebot
from telebot import types
import requests
import json
import os
import time
import random
import string
import hmac
import hashlib
import uuid
import html

# ============================================================
# ADDISLOOT - AUTOMATIC BOT (API VERSION)
# ============================================================

# ============================================================
# 1. CONFIG
# ============================================================

BOT_TOKEN = "8998441498:AAEV-jEkIwkxCoMpkKNSlfscedz25C_bdVs"

ADMIN_CHAT_ID = "1049263489"

SHEGERPAY_API_KEY = "sk_live_jpI-xxTgrR3Xj_bRSzoVqEC5wSiLroxV"

RECEIVER_NAME = "NAROBIKA"
RECEIVER_ACCOUNT = "0983762777"
MERCHANT_PAY_TO = "0983762777"

# ============================================================
# FLASHTOPUP API CONFIG (FROM YOUR SCREENSHOT)
# ============================================================
FT_API_ID = "RS8XTD55WTQ0RU7V"
FT_API_KEY = "88a2bdcd1e2973cd06b858aa430fda063e49bc4d54bb91ae6627233a4406673a"
FT_BASE_URL = "https://api.flashtopup.com/api/reseller/v2"


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
E_LABEL = "\U0001F3F7\uFE0F"
E_TRUCK = "\U0001F69A"


# ============================================================
# 3. GAME CATALOG (23% PROFIT)
# ============================================================

CATALOG = {
    "pubg": {
        "name": "PUBG Mobile",
        "product": "UC",
        "icon": E_GAME,
        "packages": [
            {"id": "pubg_60", "name": "60 UC", "price": 197, "service_code": "404"},
            {"id": "pubg_325", "name": "325 UC", "price": 1008, "service_code": "405"},
            {"id": "pubg_660", "name": "660 UC", "price": 2018, "service_code": "406"},
            {"id": "pubg_1800", "name": "1800 UC", "price": 5043, "service_code": "407"},
            {"id": "pubg_3850", "name": "3850 UC", "price": 10088, "service_code": "408"}
        ]
    },
    "freefire": {
        "name": "Free Fire",
        "product": "Diamonds",
        "icon": E_FIRE,
        "packages": [
            {"id": "ff_110", "name": "110 Diamonds", "price": 173, "service_code": "441"},
            {"id": "ff_341", "name": "341 Diamonds", "price": 523, "service_code": "442"},
            {"id": "ff_572", "name": "572 Diamonds", "price": 856, "service_code": "443"},
            {"id": "ff_1166", "name": "1166 Diamonds", "price": 1713, "service_code": "444"},
            {"id": "ff_2398", "name": "2398 Diamonds", "price": 3429, "service_code": "445"},
            {"id": "ff_6160", "name": "6160 Diamonds", "price": 8683, "service_code": "446"}
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
        "provider": "telebirr",
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
# 7. FLASHTOPUP API (AUTOMATIC ORDER PLACEMENT)
# ============================================================

def place_flashtopup_order(service_code, player_id, reference_id):
    path = "/order"
    method = "POST"

    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4())

    body_dict = {
        "service_code": service_code,
        "reference_id": str(reference_id),
        "quantity": 1,
        "user_id": str(player_id),
    }

    body = json.dumps(body_dict, separators=(",", ":"))
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    signing_path = "/api/reseller/v2" + path

    string_to_sign = f"{method}{signing_path}{timestamp}{nonce}{body_hash}"
    signature = hmac.new(FT_API_KEY.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-FT-API-ID": FT_API_ID,
        "X-FT-Timestamp": timestamp,
        "X-FT-Nonce": nonce,
        "X-FT-Signature": signature,
    }

    try:
        response = requests.post(FT_BASE_URL + path, headers=headers, data=body, timeout=30)
        try:
            response.raise_for_status()
            return response.json()
        except ValueError:
            return {
                "success": False,
                "error": "non_json_response",
                "status_code": response.status_code,
                "raw": response.text[:500],
            }
        except requests.HTTPError:
            try:
                details = response.json()
            except ValueError:
                details = response.text[:500]
            return {"success": False, "error": "http_error", "status_code": response.status_code, "details": details}
    except Exception as error:
        print("FLASHTOPUP ERROR:", error)
        return {"success": False, "error": str(error)}


def flashtopup_looks_successful(ft_result):
    if not isinstance(ft_result, dict): return False
    if ft_result.get("success") is True: return True
    status = str(ft_result.get("status", "")).lower()
    return status in ("success", "completed", "processing", "pending")


# ============================================================
# 8. BOT
# ============================================================
bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}


# ============================================================
# 9. MAIN MENU
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
    safe_name = html.escape(name)
    return (E_WAVE + " <b>WELCOME TO ADDISLOOT!</b>\n\nHello <b>" + safe_name + "</b>! " + E_GAME + "\n\n" + 
            E_DIAMOND + " <b>GAME TOP-UP STORE</b>\n\n" + E_LIGHTNING + " Fast top-ups\n" + 
            E_MONEY + " Pay in Birr\n" + E_SHIELD + " Secure payment\n" + E_CHECK + " Payment verification\n\n" + 
            "━━━━━━━━━━━━━━━━━━\n\n" + E_GAME + " <b>Choose your game below:</b>")


# ============================================================
# 10. /START
# ============================================================
@bot.message_handler(commands=["start"])
def start_command(message):
    name = message.from_user.first_name or "Gamer"
    bot.send_message(message.chat.id, welcome_message(name), parse_mode="HTML", reply_markup=main_menu())


# ============================================================
# 11. CALLBACKS
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
# 12. AUTO-REPLY FAQ
# ============================================================
@bot.message_handler(func=lambda message: message.text.lower() in ["price", "prices", "list", "menu"])
def auto_reply_prices(message):
    bot.send_message(message.chat.id, 
        "📋 <b>PUBG & Free Fire Price List</b>\n\n" +
        "🎮 PUBG: 60 UC (197 Birr) to 3850 UC (10,088 Birr)\n" +
        "🔥 Free Fire: 110 Diamonds (173 Birr) to 6160 Diamonds (8,683 Birr)\n\n" +
        "👉 Tap /start and choose your game to see full package details!",
        parse_mode="HTML")

@bot.message_handler(func=lambda message: "how to pay" in message.text.lower() or "pay" in message.text.lower() or "telebirr" in message.text.lower())
def auto_reply_pay(message):
    bot.send_message(message.chat.id, 
        "💳 <b>How to Pay</b>\n\n" +
        "1️⃣ Choose your game & package in the bot.\n" +
        "2️⃣ Send your Player ID.\n" +
        "3️⃣ Pay the exact amount shown to <code>" + MERCHANT_PAY_TO + "</code> via Telebirr.\n" +
        "4️⃣ Send your Transaction Reference.\n\n" +
        "⚠️ <b>Important:</b> Send the EXACT amount, or the bot will reject it!",
        parse_mode="HTML")

@bot.message_handler(func=lambda message: "my order" in message.text.lower() or "status" in message.text.lower() or "where" in message.text.lower())
def auto_reply_status(message):
    orders = get_user_orders(message.from_user.id)
    if not orders:
        bot.send_message(message.chat.id, E_PACKAGE + " You have no orders yet. Tap /start to make one!")
        return
    recent = orders[0]
    bot.send_message(message.chat.id, 
        E_PACKAGE + " <b>Your Latest Order</b>\n\n" +
        "Order: <code>" + recent["id"] + "</code>\n" +
        "Game: " + recent["game"] + "\n" +
        "Package: " + recent["package"] + "\n" +
        "Status: " + recent["status"].title(),
        parse_mode="HTML")


# ============================================================
# 13. PLAYER ID / PAYMENT FLOW
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

        # Go straight to Telebirr payment details
        payment_message = (
            E_CARD + " <b>PAYMENT</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            + game["icon"] + " Game: <b>" + game["name"] + "</b>\n"
            + E_DIAMOND + " Package: <b>" + package["name"] + "</b>\n"
            + E_ID + " Player ID: <code>" + html.escape(text) + "</code>\n\n"
            + E_MONEY + " <b>TOTAL: " + money(package["price"]) + "</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            + E_PHONE + " <b>PAY WITH TELEBIRR</b>\n\n"
            + E_PERSON + " Account:\n<code>" + html.escape(MERCHANT_PAY_TO) + "</code>\n\n"
            + E_MONEY + " Send exactly:\n<b>" + money(package["price"]) + "</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            + E_RECEIPT + " <b>AFTER PAYMENT</b>\n\n"
            "Send your transaction reference here.\n\n"
            + E_SEARCH + " We will check the payment."
        )
        
        bot.send_message(message.chat.id, payment_message, parse_mode="HTML")
        return

    # Transaction Reference Stage
    orders = get_user_orders(user_id)
    active_order = next((order for order in orders if order["status"] == "awaiting_payment"), None)

    if not active_order:
        bot.send_message(message.chat.id, E_HELP + " Please use /start to choose a game and create an order first.", parse_mode="HTML")
        return

    # AMOUNT MISMATCH CHECK
    if text.isdigit() and int(text) != active_order["amount"]:
        bot.send_message(message.chat.id, 
            E_WARNING + " <b>AMOUNT MISMATCH!</b>\n\n" +
            "You sent <b>" + money(int(text)) + "</b>, but the package costs <b>" + money(active_order["amount"]) + "</b>.\n\n" +
            "Please send the EXACT amount shown in the PAYMENT screen.\n" +
            "If you overpaid, please contact support for a refund.",
            parse_mode="HTML"
        )
        return
        
    if len(text) < 4:
        bot.send_message(message.chat.id, "Please send your transaction reference after completing the payment.")
        return

    bot.send_message(message.chat.id, E_CLOCK + " <b>VERIFYING...</b>", parse_mode="HTML")
    
    result = verify_payment(text, active_order["amount"])

    if result.get("verified"):
        update_order(active_order["id"], {"status": "paid", "transaction_reference": text})
        bot.send_message(message.chat.id, E_CHECK + " <b>PAYMENT CONFIRMED!</b>\n\nWe are sending your top-up now. Wait a few moments.", parse_mode="HTML")
        
        # --- AUTOMATIC FLASHTOPUP API CALL ---
        service_code = active_order.get("service_code")
        
        if not service_code:
            update_order(active_order["id"], {"status": "pending_review"})
            bot.send_message(ADMIN_CHAT_ID, E_WARNING + " Order " + active_order["id"] + " has no service code. Manual review needed.")
            return

        ft_result = place_flashtopup_order(
            service_code=service_code,
            player_id=active_order["player_id"],
            reference_id=active_order["id"]
        )
        
        ft_success = flashtopup_looks_successful(ft_result)
        update_order(active_order["id"], {"status": "processing_delivery" if ft_success else "supplier_order_failed"})

        if ft_success:
            update_order(active_order["id"], {"status": "delivered"})
            bot.send_message(message.chat.id, E_ROCKET + " <b>TOP-UP DELIVERED!</b>\n\nEnjoy your game!", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, E_CHECK + " <b>PAYMENT CONFIRMED!</b>\n\nOur system is processing your order. You will be notified shortly.", parse_mode="HTML")
            bot.send_message(ADMIN_CHAT_ID, E_WARNING + " FlashTopup API failed for order " + active_order["id"] + ". Check logs.")

    else:
        update_order(active_order["id"], {"status": "pending_review", "transaction_reference": text})
        bot.send_message(message.chat.id, E_SEARCH + " <b>PAYMENT NEEDS REVIEW</b>\n\nOur team will check it manually.", parse_mode="HTML")
        bot.send_message(ADMIN_CHAT_ID, E_WARNING + " MANUAL REVIEW: " + active_order["id"])


# ============================================================
# 14. ADMIN COMMANDS
# ============================================================
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

@bot.message_handler(commands=["confirm"])
def confirm_command(message):
    if str(message.chat.id) != str(ADMIN_CHAT_ID): return
    parts = message.text.split()
    if len(parts) != 2: return bot.reply_to(message, "Usage: /confirm ORDER_ID")
    
    order = get_order(parts[1])
    if not order: return bot.reply_to(message, E_CROSS + " Order not found.")
    
    update_order(order["id"], {"status": "delivered"})
    bot.reply_to(message, E_CHECK + f" Order {order['id']} marked delivered!")
    try:
        bot.send_message(order["user_id"], E_CHECK + " <b>TOP-UP DELIVERED!</b>\n\nEnjoy your game!", parse_mode="HTML")
    except:
        pass

@bot.message_handler(commands=["deliverall"])
def deliver_all_command(message):
    pending = [o for o in load_orders().values() if o["status"] == "paid"]
    if not pending: return bot.reply_to(message, "No pending orders.")
    count = 0
    for order in pending:
        update_order(order["id"], {"status": "delivered"})
        try:
            bot.send_message(order["user_id"], E_CHECK + " <b>TOP-UP DELIVERED!</b>\n\nEnjoy your game!", parse_mode="HTML")
            count += 1
        except:
            pass
    bot.reply_to(message, f"✅ Delivered {count} orders successfully!")

@bot.message_handler(commands=["queue"])
def queue_command(message):
    pending = [o for o in load_orders().values() if o["status"] in ["paid", "pending_review", "supplier_order_failed"]]
    if not pending:
        bot.reply_to(message, "📭 No pending orders.")
        return
    lines = ["📋 <b>ORDER QUEUE</b>\n"]
    for o in pending:
        lines.append(f"<code>{o['id']}</code> - {o['game']} - {o['package']}\n   👤 ID: {o['player_id']}\n   📌 Status: {o['status']}")
    bot.reply_to(message, "\n".join(lines), parse_mode="HTML")


# ============================================================
# 15. START BOT
# ============================================================
if __name__ == "__main__":
    print("======================================")
    print(" ADDISLOOT AUTO BOT STARTED")
    print("======================================")
    print("API ID: " + FT_API_ID)
    print("Status: LIVE")
    print("======================================")
    bot.infinity_polling()
