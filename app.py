import os
import threading
from flask import Flask, send_from_directory, jsonify

# Render provides RENDER_EXTERNAL_URL on deployed services. It is used as the
# Mini App URL unless WEB_APP_URL is explicitly supplied.
if not os.getenv("WEB_APP_URL") and os.getenv("RENDER_EXTERNAL_URL"):
    os.environ["WEB_APP_URL"] = os.getenv("RENDER_EXTERNAL_URL").rstrip("/")

from TGGUILDGOLORYBOT import load_db, poll, TOKEN

app = Flask(__name__, static_folder="web", static_url_path="")

_bot_started = False
_lock = threading.Lock()

def start_bot_once():
    global _bot_started
    with _lock:
        if _bot_started:
            return
        _bot_started = True
        load_db()
        if not TOKEN:
            print("ERROR: BOT_TOKEN environment variable is empty")
            return
        thread = threading.Thread(target=poll, name="telegram-bot", daemon=True)
        thread.start()

start_bot_once()

@app.get("/")
def index():
    return send_from_directory("web", "index.html")

@app.get("/health")
def health():
    return jsonify({"ok": True, "bot_token_configured": bool(TOKEN)})
