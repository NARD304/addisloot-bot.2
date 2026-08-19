import telebot
from telebot import types
import json
import os
import time

# ============================================================
# ADMIN BOT CONFIG
# ============================================================

# PASTE YOUR NEW ADMIN BOT TOKEN HERE (From BotFather)
ADMIN_BOT_TOKEN = "8222010017:AAEoPg2_Fxb3gq9cMWn-g2bv3_79BVH0wnQ"

# Your personal Telegram User ID (where the alerts will go)
ADMIN_CHAT_ID = "1049263489"

# ============================================================
# INIT BOT
# ============================================================
bot = telebot.TeleBot(ADMIN_BOT_TOKEN)

# Temporary storage for pending alerts
pending_queue = []

# ============================================================
# COMMANDS
# ============================================================

@bot.message_handler(commands=["start", "dashboard"])
def send_dashboard(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📋 View Queue (Stuck Orders)", callback_data="view_queue"),
        types.InlineKeyboardButton("✅ Auto-Delivered Today", callback_data="view_delivered"),
        types.InlineKeyboardButton("📊 Check Earnings", callback_data="view_earnings")
    )

    text = (
        "📊 <b>ADDISLOOT ADMIN DASHBOARD</b>\n\n"
        "Welcome back, Boss! 👋\n\n"
        "Use the buttons below to manage your store:"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=keyboard)


@bot.message_handler(commands=["alert"])
def manual_alert(message):
    """Secret command for the MAIN BOT to send alerts here."""
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    
    # This is just a placeholder. The real alerts come via the API/Webhook integration.
    bot.send_message(message.chat.id, "🔔 Admin Bot is active and listening.")


# ============================================================
# CALLBACKS (Button Handlers)
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "view_queue")
def show_queue(call):
    bot.answer_callback_query(call.id)
    # In the real version, this would fetch data from your main bot's database.
    bot.send_message(call.message.chat.id, "📭 No pending orders in the queue right now.")


@bot.callback_query_handler(func=lambda call: call.data == "view_delivered")
def show_delivered(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "✅ Auto-Delivered Today: 0 orders.")


@bot.callback_query_handler(func=lambda call: call.data == "view_earnings")
def show_earnings(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "💰 Total Earnings Today: 0 Birr.")


# ============================================================
# START THE ADMIN BOT
# ============================================================
if __name__ == "__main__":
    print("Admin Bot is running...")
    bot.infinity_polling()
