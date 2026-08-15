from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

DB_FILE = "orders.json"
PASSWORD = "admin123"  # Change this!

# === Login Required Decorator ===
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# === Load Orders ===
def load_orders():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_orders(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# === Routes ===
@app.route("/")
@login_required
def dashboard():
    orders = load_orders()
    orders_list = list(orders.values())
    orders_list.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    
    total = len(orders_list)
    pending = sum(1 for o in orders_list if o.get("status") == "awaiting_payment")
    paid = sum(1 for o in orders_list if o.get("status") == "paid")
    delivered = sum(1 for o in orders_list if o.get("status") == "delivered")
    revenue = sum(o.get("amount", 0) for o in orders_list if o.get("status") in ["paid", "delivered"])
    
    return render_template("dashboard.html", 
        orders=orders_list[:50],
        total=total,
        pending=pending,
        paid=paid,
        delivered=delivered,
        revenue=revenue
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return "Wrong password!"
    return '''
        <form method="post">
            <h2>Admin Login</h2>
            <input type="password" name="password" placeholder="Enter password">
            <button type="submit">Login</button>
        </form>
    '''

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/confirm/<order_id>")
@login_required
def confirm_order(order_id):
    data = load_orders()
    if order_id in data:
        data[order_id]["status"] = "delivered"
        save_orders(data)
    return redirect(url_for("dashboard"))

@app.route("/api/stats")
@login_required
def api_stats():
    orders = load_orders()
    orders_list = list(orders.values())
    pending = sum(1 for o in orders_list if o.get("status") == "paid")
    return jsonify({"pending": pending})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
