from flask import Flask, render_template, request, jsonify
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)
DB_PATH = "history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            amount    REAL    NOT NULL,
            from_cur  TEXT    NOT NULL,
            to_cur    TEXT    NOT NULL,
            result    REAL    NOT NULL,
            rate      REAL    NOT NULL,
            created   TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_conversion(amount, from_cur, to_cur, result, rate):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO history (amount, from_cur, to_cur, result, rate, created) VALUES (?,?,?,?,?,?)",
        (amount, from_cur, to_cur, result, rate, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

def get_history(limit=20):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT amount, from_cur, to_cur, result, rate, created FROM history ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [
        {"amount": r[0], "from": r[1], "to": r[2], "result": r[3], "rate": r[4], "created": r[5]}
        for r in rows
    ]

FALLBACK_RATES = {
    "USD":1,"EUR":0.92,"GBP":0.79,"UAH":41.2,"PLN":3.95,"CHF":0.89,
    "JPY":149.5,"CNY":7.24,"CAD":1.36,"AUD":1.53,"SEK":10.42,"NOK":10.55,
    "DKK":6.88,"CZK":22.8,"HUF":355.0,"RON":4.57,"BGN":1.80,"HRK":7.0,
    "RSD":108.0,"TRY":30.5,"BRL":4.97,"MXN":17.1,"INR":83.1,"KRW":1325.0,
    "SGD":1.34,"HKD":7.82,"NZD":1.63,"ZAR":18.6,"AED":3.67,"SAR":3.75,
}

FALLBACK_CURRENCIES = {
    "AED":"United Arab Emirates Dirham","AUD":"Australian Dollar","BGN":"Bulgarian Lev",
    "BRL":"Brazilian Real","CAD":"Canadian Dollar","CHF":"Swiss Franc","CNY":"Chinese Yuan",
    "CZK":"Czech Koruna","DKK":"Danish Krone","EUR":"Euro","GBP":"British Pound",
    "HKD":"Hong Kong Dollar","HUF":"Hungarian Forint","INR":"Indian Rupee",
    "JPY":"Japanese Yen","KRW":"South Korean Won","MXN":"Mexican Peso","NOK":"Norwegian Krone",
    "NZD":"New Zealand Dollar","PLN":"Polish Zloty","RON":"Romanian Leu","SAR":"Saudi Riyal",
    "SEK":"Swedish Krona","SGD":"Singapore Dollar","TRY":"Turkish Lira","UAH":"Ukrainian Hryvnia",
    "USD":"US Dollar","ZAR":"South African Rand",
}

def get_currencies():
    try:
        r = requests.get("https://api.frankfurter.app/currencies", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return FALLBACK_CURRENCIES

def convert(amount, from_cur, to_cur):
    if from_cur == to_cur:
        return amount, 1.0
    try:
        r = requests.get(
            "https://api.frankfurter.app/latest",
            params={"amount": amount, "from": from_cur, "to": to_cur},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            result = data["rates"][to_cur]
            rate   = result / amount
            return result, rate
    except Exception:
        pass

    if from_cur not in FALLBACK_RATES or to_cur not in FALLBACK_RATES:
        raise RuntimeError(f"Валюта {from_cur} або {to_cur} не підтримується офлайн-режимом")
    usd    = amount / FALLBACK_RATES[from_cur]
    result = usd * FALLBACK_RATES[to_cur]
    rate   = result / amount
    return result, rate

@app.route("/")
def index():
    currencies = get_currencies()
    return render_template("index.html", currencies=currencies)

@app.route("/convert", methods=["POST"])
def do_convert():
    try:
        data     = request.get_json()
        amount   = float(data["amount"])
        from_cur = data["from"].upper()
        to_cur   = data["to"].upper()

        if amount <= 0:
            return jsonify({"error": "Сума повинна бути більше нуля"}), 400

        result, rate = convert(amount, from_cur, to_cur)
        save_conversion(amount, from_cur, to_cur, result, rate)

        return jsonify({
            "result": round(result, 4),
            "rate":   round(rate, 6),
            "from":   from_cur,
            "to":     to_cur,
            "amount": amount
        })
    except ValueError:
        return jsonify({"error": "Невірна сума"}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 502

@app.route("/history")
def history():
    return jsonify(get_history())

@app.route("/clear_history", methods=["POST"])
def clear_history():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

if __name__ == "__main__":
    init_db()
    print("✅  Запуск: http://127.0.0.1:5000")
    app.run(debug=True)
