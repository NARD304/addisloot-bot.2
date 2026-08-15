from telegram import Update
from telegram.ext import Application, CommandHandler, filters, ContextTypes
from flask import Flask, request, jsonify
import threading

# === CONFIG ===
BOT_TOKEN = "8222010018:AATOPGZ_FXD3Q9CIPWN-GZBV3_YBYH0WNU"
ADMIN_IDS = [1049263489]

flask_app = Flask(__name__)
app = Application.builder().token(BOT_TOKEN).build()

@flask_app.route("/send_order", methods=["POST"])
def receive_order():
    data = request.json
    msg = (
        f"✅ **VERIFIED ORDER**\n"
        f"Order #: {data['order_number']}\n"
        f"Player ID: {data['player_id']}\n"
        f"Package: {data['package']}\n"
        f"Game: {data['game']}\n"
        f"Amount: {data['amount']} Birr"
    )
    for admin in ADMIN_IDS:
        try:
            app.bot.send_message(chat_id=admin, text=msg)
        except:
            pass
    return jsonify({"status": "ok"}), 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app.run_polling()
