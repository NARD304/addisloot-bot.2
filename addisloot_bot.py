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


# ============================================================
# ADDISLOOT - FRESH BOT (with FlashTopup auto-fulfillment)
# ============================================================

# ============================================================
# 1. CONFIG
# ============================================================

BOT_TOKEN = "8998441498:AAEV-jEkIwkxCoMpkKNSlfscedz25C_bdVs"

ADMIN_CHAT_ID = "PUT_YOUR_EXISTING_ADMIN_CHAT_ID_HERE"

QBIRR_API_KEY = "vaBjgkb5.vtd74ZJ_NoKG07rFQtAVjmTaw_8gHTIG"

PAYMENT_PROVIDER = "telebirr"

RECEIVER_NAME = "NAROBIKA"

RECEIVER_ACCOUNT = "0983762777"

MERCHANT_PAY_TO = "0983762777"


# ============================================================
# 1b. FLASHTOPUP CONFIG (reseller order placement)
# ============================================================

FT_API_ID = "YOUR_FLASHTOPUP_API_ID"

FT_API_KEY = "YOUR_NEW_FLASHTOPUP_API_KEY"

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
E_GLOBE = "\U0001F310"
E_TRUCK = "\U0001F69A"


# ============================================================
# 3. GAME CATALOG
#
# IMPORTANT:
# "service_code" is what FlashTopup needs to know
# WHICH product/package to fulfill.
#
# Replace the placeholders with the REAL service codes
# from your FlashTopup reseller dashboard.
# ============================================================

CATALOG = {

    "pubg": {

        "name": "PUBG Mobile",

        "product": "UC",

        "icon": E_GAME,

        "packages": [

            {
                "id": "pubg_60",
                "name": "60 UC",
                "price": 220,
                "service_code": "FT_SERVICE_CODE_PUBG_60"
            },

            {
                "id": "pubg_325",
                "name": "325 UC",
                "price": 800,
                "service_code": "FT_SERVICE_CODE_PUBG_325"
            },

            {
                "id": "pubg_660",
                "name": "660 UC",
                "price": 1500,
                "service_code": "FT_SERVICE_CODE_PUBG_660"
            },

            {
                "id": "pubg_1800",
                "name": "1800 UC",
                "price": 3200,
                "service_code": "FT_SERVICE_CODE_PUBG_1800"
            },

            {
                "id": "pubg_3850",
                "name": "3850 UC",
                "price": 8400,
                "service_code": "FT_SERVICE_CODE_PUBG_3850"
            }

        ]
    },


    "freefire": {

        "name": "Free Fire",

        "product": "Diamonds",

        "icon": E_FIRE,

        "packages": [

            {
                "id": "ff_100",
                "name": "100 Diamonds",
                "price": 220,
                "service_code": "FT_SERVICE_CODE_FF_100"
            },

            {
                "id": "ff_310",
                "name": "310 Diamonds",
                "price": 500,
                "service_code": "FT_SERVICE_CODE_FF_310"
            },

            {
                "id": "ff_520",
                "name": "520 Diamonds",
                "price": 820,
                "service_code": "FT_SERVICE_CODE_FF_520"
            },

            {
                "id": "ff_1080",
                "name": "1080 Diamonds",
                "price": 1530,
                "service_code": "FT_SERVICE_CODE_FF_1080"
            },

            {
                "id": "ff_2200",
                "name": "2200 Diamonds",
                "price": 3750,
                "service_code": "FT_SERVICE_CODE_FF_2200"
            }

        ]
    }

}


# ============================================================
# 4. DATABASE
# ============================================================

DB_FILE = "orders.json"


def load_orders():

    if not os.path.exists(DB_FILE):
        return {}

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

    if order_id not in data:

        return None

    data[order_id].update(changes)

    save_orders(data)

    return data[order_id]


def get_user_orders(user_id):

    data = load_orders()

    orders = [

        order

        for order in data.values()

        if str(order["user_id"]) == str(user_id)

    ]

    return sorted(
        orders,
        key=lambda x: x["created_at"],
        reverse=True
    )


# ============================================================
# 5. ORDER ID
# ============================================================

def generate_order_id():

    timestamp = str(
        int(time.time() * 1000)
    )[-7:]

    random_part = "".join(

        random.choices(

            string.ascii_uppercase + string.digits,

            k=4

        )

    )

    return "AL" + timestamp + random_part


# ============================================================
# 6. MONEY
# ============================================================

def money(amount):

    return f"{amount:,} Birr"


# ============================================================
# 7. QBIRR
# ============================================================

QBIRR_BASE_URL = "https://verify.qbirr.com"


def verify_payment(transaction_reference, amount):

    payload = {

        "provider": PAYMENT_PROVIDER,

        "ref": transaction_reference,

        "amount": amount,

        "receiver_name": RECEIVER_NAME

    }

    if PAYMENT_PROVIDER in ("cbe", "abyssinia"):

        payload["receiver_account"] = RECEIVER_ACCOUNT

    try:

        response = requests.post(

            QBIRR_BASE_URL + "/api/v1/verify",

            json=payload,

            headers={

                "X-API-Key": QBIRR_API_KEY,

                "Content-Type": "application/json"

            },

            timeout=15

        )

        response.raise_for_status()

        return response.json()

    except Exception as error:

        print("QBIRR ERROR:", error)

        return {

            "verified": False,

            "error": "verification_service_error"

        }


# ============================================================
# 7b. FLASHTOPUP
# ============================================================

def place_flashtopup_order(
    service_code,
    player_id,
    reference_id,
    server_id=None
):

    """
    Place an order on FlashTopup after QBirr verification succeeds.
    """

    path = "/api/reseller/v2/order"

    method = "POST"

    timestamp = str(int(time.time()))

    nonce = str(uuid.uuid4())

    body_dict = {

        "service_code": service_code,

        "reference_id": str(reference_id),

        "quantity": 1,

        "user_id": str(player_id)

    }

    if server_id:

        body_dict["server_id"] = str(server_id)

    body = json.dumps(

        body_dict,

        separators=(",", ":")

    )

    body_hash = hashlib.sha256(

        body.encode("utf-8")

    ).hexdigest()

    string_to_sign = (

        f"{method}"
        f"{path}"
        f"{timestamp}"
        f"{nonce}"
        f"{body_hash}"

    )

    signature = hmac.new(

        FT_API_KEY.encode("utf-8"),

        string_to_sign.encode("utf-8"),

        hashlib.sha256

    ).hexdigest()

    headers = {

        "Content-Type": "application/json",

        "X-FT-API-ID": FT_API_ID,

        "X-FT-Timestamp": timestamp,

        "X-FT-Nonce": nonce,

        "X-FT-Signature": signature

    }

    try:

        response = requests.post(

            FT_BASE_URL + "/order",

            headers=headers,

            data=body,

            timeout=30

        )

        try:

            return response.json()

        except Exception:

            return {

                "success": False,

                "error": "non_json_response",

                "status_code": response.status_code,

                "raw": response.text[:500]

            }

    except Exception as error:

        print("FLASHTOPUP ERROR:", error)

        return {

            "success": False,

            "error": str(error)

        }


def flashtopup_looks_successful(ft_result):

    if not isinstance(ft_result, dict):

        return False

    if ft_result.get("success") is True:

        return True

    status = str(

        ft_result.get("status", "")

    ).lower()

    if status in (

        "success",
        "completed",
        "processing",
        "pending"

    ):

        return True

    return False


# ============================================================
# 8. BOT
# ============================================================

bot = telebot.TeleBot(BOT_TOKEN)


# ============================================================
# 9. TEMPORARY USER STATE
# ============================================================

user_state = {}


# ============================================================
# 10. MAIN MENU
# ============================================================

def main_menu():

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

    keyboard.add(

        types.InlineKeyboardButton(

            E_GAME + " PUBG Mobile UC",

            callback_data="game_pubg"

        ),

        types.InlineKeyboardButton(

            E_FIRE + " Free Fire Diamonds",

            callback_data="game_freefire"

        )

    )

    keyboard.add(

        types.InlineKeyboardButton(

            E_PACKAGE + " My Orders",

            callback_data="orders"

        ),

        types.InlineKeyboardButton(

            E_HELP + " Help",

            callback_data="help"

        )

    )

    return keyboard


def welcome_message(name):

    return (

        E_WAVE
        + " <b>WELCOME TO ADDISLOOT!</b>\n\n"

        + "Hello <b>"
        + name
        + "</b>! "
        + E_GAME
        + "\n\n"

        + E_DIAMOND
        + " <b>GAME TOP-UP STORE</b>\n\n"

        + E_LIGHTNING
        + " Fast top-ups\n"

        + E_MONEY
        + " Pay in Birr\n"

        + E_SHIELD
        + " Secure payment\n"

        + E_CHECK
        + " Payment verification\n\n"

        + "━━━━━━━━━━━━━━━━━━\n\n"

        + E_GAME
        + " <b>Choose your game below:</b>"

    )


# ============================================================
# 11. /START
# ============================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    name = (
        message.from_user.first_name
        or "Gamer"
    )

    bot.send_message(

        message.chat.id,

        welcome_message(name),

        parse_mode="HTML",

        reply_markup=main_menu()

    )


# ============================================================
# 12. GAME MENU
# ============================================================

def show_game_menu(
    chat_id,
    message_id,
    game_id
):

    game = CATALOG.get(game_id)

    if not game:

        return

    keyboard = types.InlineKeyboardMarkup()

    for package in game["packages"]:

        button = (

            E_DIAMOND
            + " "
            + package["name"]
            + "  -  "
            + money(package["price"])

        )

        keyboard.add(

            types.InlineKeyboardButton(

                button,

                callback_data=(
                    "package:"
                    + game_id
                    + ":"
                    + package["id"]
                )

            )

        )

    keyboard.add(

        types.InlineKeyboardButton(

            E_HOME + " Main Menu",

            callback_data="home"

        )

    )

    if game_id == "pubg":

        title = (
            E_GAME
            + " <b>PUBG MOBILE UC</b>"
        )

        extra = (

            E_SHIELD
            + " Secure  "
            + E_LIGHTNING
            + " Fast\n"

            + E_GAME
            + " PUBG Mobile"

        )

    else:

        title = (
            E_FIRE
            + " <b>FREE FIRE DIAMONDS</b>"
        )

        extra = (

            E_SHIELD
            + " Secure  "
            + E_LIGHTNING
            + " Fast\n"

            + E_FIRE
            + " Free Fire"

        )

    text = (

        title
        + "\n\n"

        + extra
        + "\n\n"

        + "━━━━━━━━━━━━━━━━━━\n\n"

        + "💰 <b>PRICES</b>\n\n"

        + "Choose the package you want:"

    )

    bot.edit_message_text(

        text,

        chat_id,

        message_id,

        parse_mode="HTML",

        reply_markup=keyboard

    )


# ============================================================
# 13. CALLBACKS
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "home"
)
def home_callback(call):

    bot.answer_callback_query(call.id)

    name = (
        call.from_user.first_name
        or "Gamer"
    )

    bot.edit_message_text(

        welcome_message(name),

        call.message.chat.id,

        call.message.message_id,

        parse_mode="HTML",

        reply_markup=main_menu()

    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("game_")
)
def game_callback(call):

    bot.answer_callback_query(call.id)

    game_id = call.data.replace(
        "game_",
        "",
        1
    )

    show_game_menu(

        call.message.chat.id,

        call.message.message_id,

        game_id

    )


# ============================================================
# 14. PACKAGE SELECTION
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("package:")
)
def package_callback(call):

    parts = call.data.split(":")

    if len(parts) != 3:

        return

    game_id = parts[1]

    package_id = parts[2]

    game = CATALOG.get(game_id)

    if not game:

        return

    package = next(

        (
            item
            for item in game["packages"]
            if item["id"] == package_id
        ),

        None

    )

    if not package:

        return

    user_state[call.from_user.id] = {

        "game_id": game_id,

        "package_id": package_id

    }

    bot.answer_callback_query(call.id)

    text = (

        "3️⃣ <b>PLAYER INFORMATION</b>\n\n"

        + "━━━━━━━━━━━━━━━━━━\n\n"

        + game["icon"]
        + " Game: <b>"
        + game["name"]
        + "</b>\n"

        + E_DIAMOND
        + " Package: <b>"
        + package["name"]
        + "</b>\n"

        + E_MONEY
        + " Price: <b>"
        + money(package["price"])
        + "</b>\n\n"

        + "━━━━━━━━━━━━━━━━━━\n\n"

        + E_ID
        + " <b>SEND YOUR PLAYER ID</b>\n\n"

        + "Please send your "
        + game["name"]
        + " Player ID."

    )

    bot.send_message(

        call.message.chat.id,

        text,

        parse_mode="HTML"

    )


# ============================================================
# 15. MY ORDERS
# ============================================================

def orders_text(user_id):

    orders = get_user_orders(user_id)[:10]

    if not orders:

        return (

            E_PACKAGE
            + " <b>NO ORDERS YET</b>\n\n"

            + "You haven't made an order yet.\n\n"

            + E_GAME
            + " Choose a game from the main menu to get started."

        )

    status_icons = {

        "awaiting_payment": E_CLOCK,

        "paid": E_CARD,

        "pending_review": E_SEARCH,

        "processing_delivery": E_TRUCK,

        "supplier_order_failed": E_WARNING,

        "delivered": E_CHECK,

        "rejected": E_CROSS

    }

    lines = [

        E_PACKAGE
        + " <b>MY ORDERS</b>\n",

        "━━━━━━━━━━━━━━━━━━"

    ]

    for order in orders:

        icon = status_icons.get(

            order["status"],

            E_LABEL

        )

        status = (

            order["status"]
            .replace("_", " ")
            .title()

        )

        lines.append(

            "\n"
            + icon
            + " <b>"
            + order["id"]
            + "</b>\n"

            + E_GAME
            + " "
            + order["game"]
            + "\n"

            + E_DIAMOND
            + " "
            + order["package"]
            + "\n"

            + E_MONEY
            + " "
            + money(order["amount"])
            + "\n"

            + E_LABEL
            + " "
            + status

        )

    return "\n".join(lines)


@bot.callback_query_handler(
    func=lambda call: call.data == "orders"
)
def orders_callback(call):

    bot.answer_callback_query(call.id)

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(

        types.InlineKeyboardButton(

            E_HOME + " Main Menu",

            callback_data="home"

        )

    )

    bot.edit_message_text(

        orders_text(call.from_user.id),

        call.message.chat.id,

        call.message.message_id,

        parse_mode="HTML",

        reply_markup=keyboard

    )


@bot.message_handler(commands=["myorders"])
def myorders_command(message):

    bot.send_message(

        message.chat.id,

        orders_text(message.from_user.id),

        parse_mode="HTML",

        reply_markup=main_menu()

    )


# ============================================================
# 16. HELP
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "help"
)
def help_callback(call):

    bot.answer_callback_query(call.id)

    text = (

        E_HELP
        + " <b>HOW TO ORDER</b>\n\n"

        + "━━━━━━━━━━━━━━━━━━\n\n"

        + "1️⃣ "
        + E_GAME
        + " Choose your game\n\n"

        + "2️⃣ "
        + E_DIAMOND
        + " Choose your package\n\n"

        + "3️⃣ "
        + E_ID
        + " Enter your Player ID\n\n"

        + "4️⃣ "
        + E_CARD
        + " Send the exact payment amount\n\n"

        + "5️⃣ "
        + E_RECEIPT
        + " Send your transaction reference\n\n"

        + "6️⃣ "
        + E_SEARCH
        + " Payment is checked\n\n"

        + "7️⃣ "
        + E_ROCKET
        + " Your top-up is processed\n\n"

        + "━━━━━━━━━━━━━━━━━━\n\n"

        + E_CHAT
        + " <b>NEED HELP?</b>\n\n"

        + "Contact the AddisLoot support team."

    )

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(

        types.InlineKeyboardButton(

            E_HOME + " Main Menu",

            callback_data="home"

        )

    )

    bot.edit_message_text(

        text,

        call.message.chat.id,

        call.message.message_id,

        parse_mode="HTML",

        reply_markup=keyboard

    )


# ============================================================
# 17. PLAYER ID / PAYMENT FLOW
# ============================================================

@bot.message_handler(
    func=lambda message: True,
    content_types=["text"]
)
def text_handler(message):

    text = message.text.strip()

    user_id = message.from_user.id

    if text.startswith("/"):

        return


    # --------------------------------------------------------
    # PLAYER ID STAGE
    # --------------------------------------------------------

    if user_id in user_state:

        state = user_state[user_id]

        game = CATALOG.get(
            state["game_id"]
        )

        if not game:

            del user_state[user_id]

            return

        package = next(

            (
                item
                for item in game["packages"]
                if item["id"] == state["package_id"]
            ),

            None

        )

        if not package:

            del user_state[user_id]

            return

        order_id = generate_order_id()

        order = {

            "id": order_id,

            "user_id": user_id,

            "username": (
                message.from_user.username
                or message.from_user.first_name
                or "Unknown"
            ),

            "game": game["name"],

            "package": package["name"],

            "amount": package["price"],

            "player_id": text,

            "service_code": package.get(
                "service_code"
            ),

            "status": "awaiting_payment",

            "transaction_reference": "",

            "created_at": time.time()

        }

        create_order(order)

        del user_state[user_id]

        payment_message = (

            E_CARD
            + " <b>PAYMENT</b>\n\n"

            + "━━━━━━━━━━━━━━━━━━\n\n"

            + game["icon"]
            + " Game: <b>"
            + game["name"]
            + "</b>\n"

            + E_DIAMOND
            + " Package: <b>"
            + package["name"]
            + "</b>\n"

            + E_ID
            + " Player ID: <code>"
            + text
            + "</code>\n\n"

            + E_MONEY
            + " <b>TOTAL: "
            + money(package["price"])
            + "</b>\n\n"

            + "━━━━━━━━━━━━━━━━━━\n\n"

            + E_PHONE
            + " <b>PAY WITH "
            + PAYMENT_PROVIDER.upper()
            + "</b>\n\n"

            + E_PERSON
            + " Account:\n"
            + "<code>"
            + MERCHANT_PAY_TO
            + "</code>\n\n"

            + E_MONEY
            + " Send exactly:\n"
            + "<b>"
            + money(package["price"])
            + "</b>\n\n"

            + "━━━━━━━━━━━━━━━━━━\n\n"

            + E_RECEIPT
            + " <b>AFTER PAYMENT</b>\n\n"

            + "Send your transaction reference here.\n\n"

            + E_SEARCH
            + " We will check the payment."

        )

        bot.send_message(

            message.chat.id,

            payment_message,

            parse_mode="HTML"

        )

        return


    # --------------------------------------------------------
    # TRANSACTION REFERENCE STAGE
    # --------------------------------------------------------

    if len(text) < 4:

        bot.send_message(

            message.chat.id,

            "Please send your transaction reference after completing the payment."

        )

        return

    orders = get_user_orders(user_id)

    active_order = None

    for order in orders:

        if order["status"] == "awaiting_payment":

            active_order = order

            break

    if not active_order:

        bot.send_message(

            message.chat.id,

            E_HELP
            + " Please use /start to choose a game and create an order first.",

            parse_mode="HTML"

        )

        return

    bot.send_message(

        message.chat.id,

        E_CLOCK
        + " <b>CHECKING YOUR PAYMENT...</b>\n\n"

        + "Please wait while we verify your transaction.",

        parse_mode="HTML"

    )

    result = verify_payment(

        text,

        active_order["amount"]

    )


    # --------------------------------------------------------
    # VERIFIED -> mark paid, then place order with FlashTopup
    # --------------------------------------------------------

    if result.get("verified"):

        update_order(

            active_order["id"],

            {

                "status": "paid",

                "transaction_reference": text,

                "payer": result.get("payer")

            }

        )

        service_code = active_order.get(
            "service_code"
        )

        if not service_code:

            update_order(

                active_order["id"],

                {
                    "status": "pending_review"
                }

            )

            bot.send_message(

                message.chat.id,

                E_CHECK
                + " <b>PAYMENT VERIFIED!</b>\n\n"

                + "Your payment has been confirmed. Our team will process "
                + "your order shortly.\n\n"

                + "Order: <code>"
                + active_order["id"]
                + "</code>",

                parse_mode="HTML"

            )

            bot.send_message(

                ADMIN_CHAT_ID,

                E_WARNING
                + " <b>MISSING SERVICE CODE</b>\n\n"

                + "Order <code>"
                + active_order["id"]
                + "</code> was paid but has "
                + "no FlashTopup service_code configured. Fulfill manually "
                + "and run:\n<code>/confirm "
                + active_order["id"]
                + "</code>",

                parse_mode="HTML"

            )

            return


        ft_result = place_flashtopup_order(

            service_code=service_code,

            player_id=active_order["player_id"],

            reference_id=active_order["id"]

        )

        ft_success = flashtopup_looks_successful(
            ft_result
        )

        update_order(

            active_order["id"],

            {

                "status":
                    "processing_delivery"
                    if ft_success
                    else "supplier_order_failed",

                "flashtopup_response": ft_result

            }

        )

        if ft_success:

            bot.send_message(

                message.chat.id,

                E_CHECK
                + " <b>PAYMENT VERIFIED!</b>\n\n"

                + "Your payment has been confirmed and your order has been "
                + "sent for delivery.\n\n"

                + E_ROCKET
                + " Your top-up is now being processed.\n\n"

                + "Order: <code>"
                + active_order["id"]
                + "</code>",

                parse_mode="HTML"

            )

            admin_message = (

                E_BELL
                + " <b>ORDER PLACED WITH FLASHTOPUP</b>\n\n"

                + "━━━━━━━━━━━━━━━━━━\n\n"

                + "Order: <code>"
                + active_order["id"]
                + "</code>\n"

                + E_PERSON
                + " Buyer: @"
                + str(active_order["username"])
                + "\n\n"

                + E_GAME
                + " "
                + active_order["game"]
                + "\n"

                + E_DIAMOND
                + " "
                + active_order["package"]
                + "\n"

                + E_MONEY
                + " "
                + money(active_order["amount"])
                + "\n"

                + E_ID
                + " Player ID: <code>"
                + str(active_order["player_id"])
                + "</code>\n\n"

                + E_RECEIPT
                + " Reference: <code>"
                + text
                + "</code>\n\n"

                + E_TRUCK
                + " FlashTopup response:\n<code>"

                + json.dumps(ft_result)[:600]

                + "</code>\n\n"

                + E_CHECK
                + " Once delivery is confirmed:\n"

                + "<code>/confirm "
                + active_order["id"]
                + "</code>"

            )

            bot.send_message(

                ADMIN_CHAT_ID,

                admin_message,

                parse_mode="HTML"

            )

        else:

            bot.send_message(

                message.chat.id,

                E_CHECK
                + " <b>PAYMENT VERIFIED!</b>\n\n"

                + "Your payment has been confirmed. Your order is being "
                + "finalized and you'll be notified shortly.\n\n"

                + "Order: <code>"
                + active_order["id"]
                + "</code>",

                parse_mode="HTML"

            )

            admin_message = (

                E_WARNING
                + " <b>PAID BUT SUPPLIER ORDER FAILED</b>\n\n"

                + "━━━━━━━━━━━━━━━━━━\n\n"

                + "Order: <code>"
                + active_order["id"]
                + "</code>\n"

                + E_PERSON
                + " Buyer: @"
                + str(active_order["username"])
                + "\n\n"

                + E_GAME
                + " "
                + active_order["game"]
                + "\n"

                + E_DIAMOND
                + " "
                + active_order["package"]
                + "\n"

                + E_MONEY
                + " "
                + money(active_order["amount"])
                + "\n"

                + E_ID
                + " Player ID: <code>"
                + str(active_order["player_id"])
                + "</code>\n\n"

                + E_RECEIPT
                + " Reference: <code>"
                + text
                + "</code>\n\n"

                + E_CROSS
                + " FlashTopup error:\n<code>"

                + json.dumps(ft_result)[:600]

                + "</code>\n\n"

                + "Fulfill manually (or fix service_code) then run:\n"

                + "<code>/confirm "
                + active_order["id"]
                + "</code>\n\n"

                + "Or reject:\n"

                + "<code>/reject "
                + active_order["id"]
                + "</code>"

            )

            bot.send_message(

                ADMIN_CHAT_ID,

                admin_message,

                parse_mode="HTML"

            )

        return


    # --------------------------------------------------------
    # MANUAL REVIEW
    # --------------------------------------------------------

    update_order(

        active_order["id"],

        {

            "status": "pending_review",

            "transaction_reference": text

        }

    )

    bot.send_message(

        message.chat.id,

        E_SEARCH
        + " <b>PAYMENT RECEIVED</b>\n\n"

        + "We could not automatically verify the transaction.\n\n"

        + E_PERSON
        + " Our team will check it manually.\n\n"

        + "Please wait for confirmation.",

        parse_mode="HTML"

    )

    admin_review = (

        E_WARNING
        + " <b>PAYMENT NEEDS REVIEW</b>\n\n"

        + "━━━━━━━━━━━━━━━━━━\n\n"

        + "Order: <code>"
        + active_order["id"]
        + "</code>\n"

        + E_PERSON
        + " Buyer: @"
        + str(active_order["username"])
        + "\n\n"

        + E_GAME
        + " "
        + active_order["game"]
        + "\n"

        + E_DIAMOND
        + " "
        + active_order["package"]
        + "\n"

        + E_MONEY
        + " "
        + money(active_order["amount"])
        + "\n"

        + E_ID
        + " Player ID: <code>"
        + str(active_order["player_id"])
        + "</code>\n\n"

        + E_RECEIPT
        + " Reference:\n<code>"
        + text
        + "</code>\n\n"

        + "QBIRR response:\n"
        + str(
            result.get(
                "error",
                "Not verified"
            )
        )
        + "\n\n"

        + E_CHECK
        + " Confirm:\n"

        + "<code>/confirm "
        + active_order["id"]
        + "</code>\n\n"

        + E_CROSS
        + " Reject:\n"

        + "<code>/reject "
        + active_order["id"]
        + "</code>"

    )

    bot.send_message(

        ADMIN_CHAT_ID,

        admin_review,

        parse_mode="HTML"

    )


# ============================================================
# 18. ADMIN CONFIRM
# ============================================================

@bot.message_handler(commands=["confirm"])
def confirm_command(message):

    if str(message.chat.id) != str(ADMIN_CHAT_ID):

        return

    parts = message.text.split()

    if len(parts) != 2:

        bot.reply_to(
            message,
            "Usage: /confirm ORDER_ID"
        )

        return

    order_id = parts[1]

    order = get_order(order_id)

    if not order:

        bot.reply_to(

            message,

            E_CROSS + " Order not found."

        )

        return

    update_order(

        order_id,

        {
            "status": "delivered"
        }

    )

    bot.reply_to(

        message,

        E_CHECK
        + " Order "
        + order_id
        + " marked as delivered."

    )

    bot.send_message(

        order["user_id"],

        E_ROCKET
        + " <b>TOP-UP DELIVERED!</b>\n\n"

        + E_CHECK
        + " Your <b>"
        + order["package"]
        + "</b> has been delivered.\n\n"

        + E_GAME
        + " Game: "
        + order["game"]
        + "\n"

        + E_ID
        + " Player ID: <code>"
        + str(order["player_id"])
        + "</code>\n\n"

        + "Thank you for using AddisLoot!",

        parse_mode="HTML"

    )


# ============================================================
# 19. ADMIN REJECT
# ============================================================

@bot.message_handler(commands=["reject"])
def reject_command(message):

    if str(message.chat.id) != str(ADMIN_CHAT_ID):

        return

    parts = message.text.split()

    if len(parts) != 2:

        bot.reply_to(

            message,

            "Usage: /reject ORDER_ID"

        )

        return

    order_id = parts[1]

    order = get_order(order_id)

    if not order:

        bot.reply_to(

            message,

            E_CROSS + " Order not found."

        )

        return

    update_order(

        order_id,

        {
            "status": "rejected"
        }

    )

    bot.reply_to(

        message,

        E_CROSS
        + " Order "
        + order_id
        + " rejected."

    )

    bot.send_message(

        order["user_id"],

        E_WARNING
        + " <b>PAYMENT NOT VERIFIED</b>\n\n"

        + "We could not verify your payment.\n\n"

        + E_RECEIPT
        + " Please check your transaction reference and contact support.",

        parse_mode="HTML"

    )


# ============================================================
# 20. RUN
# ============================================================

print("======================================")
print(" ADDISLOOT BOT STARTED")
print("======================================")
print("Game top-ups: ON")
print("Payment verification: QBirr")
print("Order fulfillment: FlashTopup")
print("Emoji mode: Unicode")
print("======================================")


while True:

    try:

        bot.infinity_polling(

            skip_pending=True,

            timeout=20,

            long_polling_timeout=20

        )

    except Exception as e:

        print(
            "Polling crashed, restarting in 5s:",
            e
        )

        time.sleep(5)
