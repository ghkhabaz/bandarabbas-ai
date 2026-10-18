"""Parsik — Printing & Advertising Agency: static site server + contact API."""
from datetime import datetime
from json import dumps, loads

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) or {}
    entry = {
        "name": str(data.get("name", "")).strip()[:100],
        "phone": str(data.get("phone", "")).strip()[:20],
        "service": str(data.get("service", "")).strip()[:100],
        "message": str(data.get("message", "")).strip()[:2000],
        "received_at": datetime.now().isoformat(timespec="seconds"),
    }
    if not entry["name"] or not entry["phone"]:
        return jsonify({"ok": False, "error": "نام و شماره تماس الزامی است."}), 400
    with open("contacts.json", "a", encoding="utf-8") as f:
        f.write(dumps(entry, ensure_ascii=False) + "\n")
    return jsonify({"ok": True})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
