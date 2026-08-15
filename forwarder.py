import json
import time
import requests
import os

ADMIN_BOT_API = "http://localhost:5000/send_order"
DB_FILE = "orders.json"
CHECK_INTERVAL = 5
PROCESSED_FILE = "processed_orders.txt"

def load_processed():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_processed(order_id):
    with open(PROCESSED_FILE, "a") as f:
        f.write(order_id + "\n")

def check_orders():
    processed = load_processed()
    if not os.path.exists(DB_FILE):
        return
    with open(DB_FILE, "r") as f:
        orders = json.load(f)
    for order_id, order in orders.items():
        if order_id in processed:
            continue
        if order.get("status") == "paid":
            payload = {
                "order_number": order["id"],
                "player_id": order["player_id"],
                "package": order["package"],
                "game": order["game"],
                "amount": order["amount"],
                "user_id": order["user_id"],
                "username": order["username"]
            }
            try:
                resp = requests.post(ADMIN_BOT_API, json=payload, timeout=5)
                if resp.status_code == 200:
                    print(f"✅ Forwarded: {order_id}")
                    save_processed(order_id)
                else:
                    print(f"⚠️ Failed: {order_id}")
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Forwarder started. Monitoring orders.json...")
    while True:
        check_orders()
        time.sleep(CHECK_INTERVAL)
