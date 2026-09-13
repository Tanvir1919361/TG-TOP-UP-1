#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANBIR CODEX - FF GUILD GOLORY + UID TopUp + Weekly/Monthly Telegram Bot
No web admin panel. Owner/admin controls are available only to ADMIN_ID.
"""

import json
import os
import time
import uuid
from pathlib import Path

import requests

# ========================= CONFIG =========================
TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEB_APP_URL = os.getenv("WEB_APP_URL", "").strip()
ADMIN_ID = 7198873848
OWNER_USERNAME = "@Tanvir_owne"

# Payment numbers from the previous bot setup.
BKASH_NUMBER = os.getenv("BKASH_NUMBER", "01708647854")
NAGAD_NUMBER = os.getenv("NAGAD_NUMBER", "01708647854")

DB_FILE = Path("database.json")
PROOF_DIR = Path("payment_proofs")
PROOF_DIR.mkdir(exist_ok=True)

# Guild Glory packages
GUILD_PACKAGES = {
    "4": {"name": "4 BOT", "price": 200},
    "8": {"name": "8 BOT", "price": 400},
    "12": {"name": "12 BOT", "price": 600},
    "16": {"name": "16 BOT", "price": 800},
    "20": {"name": "20 BOT", "price": 1000},
}

# UID TopUp Bd packages
UID_PACKAGES = {
    "uid_25": ("25 Diamond", 18),
    "uid_50": ("50 Diamond", 34),
    "uid_115": ("115 Diamond", 69),
    "uid_240": ("240 Diamond", 160),
    "uid_355": ("355 Diamond", 235),
    "uid_480": ("480 Diamond", 300),
    "uid_610": ("610 Diamond", 370),
    "uid_850": ("850 Diamond", 520),
    "uid_1090": ("1090 Diamond", 630),
    "uid_1240": ("1240 Diamond", 700),
    "uid_2530": ("2530 Diamond", 1400),
    "uid_5060": ("5060 Diamond", 2720),
    "uid_level": ("Level Up Pass", 162),
    "uid_weekly": ("Weekly", 159),
    "uid_monthly": ("Monthly", 700),
}

# Weekly/Monthly packages (prices exactly as provided in the user's screenshot)
WEEKLY_MONTHLY_PACKAGES = {
    "wm_weekly": ("Weekly", 158),
    "wm_weekly_lite": ("weekly lite", 45),
    "wm_monthly": ("Monthly", 790),
    "wm_2x_weekly": ("2X Weekly", 316),
    "wm_3x_weekly": ("3X Weekly", 474),
    "wm_5x_weekly": ("5X Weekly", 790),
    "wm_2x_monthly": ("2X Monthly", 1580),
    "wm_1weekly_1monthly": ("1Weekly + 1Monthly", 948),
    "wm_4weekly_1monthly": ("4Weekly + 1Monthly", 1422),
    "wm_2x_weekly_lite": ("2x weekly lite", 90),
    "wm_3x_weekly_lite": ("3x weekly lite", 135),
    "wm_5x_weekly_lite": ("5x Weekly Lite", 225),
}

WELCOME = """🔥 <b>TANBIR CODEX গিল্ড গ্লোরি বট</b> 💎

👋 স্বাগতম <b>{name}</b>

🆔 আপনার আইডি: <code>{user_id}</code>

🤖 <b>বৈশিষ্ট্যসমূহ:</b>
• Free Fire Guild Glory প্যাকেজ অর্ডার
• UID TopUp Bd
• Weekly/Monthly প্যাকেজ
• পেমেন্ট প্রুফ স্ক্রিনশট সিস্টেম
• Owner review ও Approve/Reject

👇 শুরু করতে নিচের বাটন ব্যবহার করুন!"""

PACKAGE_TEXT = "🛒 <b>অনুগ্রহ করে আপনি কোন প্যাকেজটি নিতে চাচ্ছেন সেটি সিলেক্ট করুন</b>"
UID_TEXT = "💎 <b>UID TopUp Bd</b>\n\nনিচের লিস্ট থেকে একটি প্যাকেজ সিলেক্ট করুন:"
WEEKLY_MONTHLY_TEXT = "📅 <b>Weekly/Monthly</b>\n\nনিচের লিস্ট থেকে একটি প্যাকেজ সিলেক্ট করুন:"
THANKS_TEXT = (
    "📸 আপনার স্ক্রিনশটটি Owner-এর কাছে জমা দেওয়া হয়েছে।\n"
    "⏳ অনুগ্রহ করে Approve করা পর্যন্ত অপেক্ষা করুন।"
)

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
session = requests.Session()
users = {}
orders = {}
user_state = {}
owner_review_messages = {}
pending_user_messages = {}


def load_db():
    global users, orders
    if not DB_FILE.exists():
        return
    try:
        data = json.loads(DB_FILE.read_text(encoding="utf-8"))
        users = data.get("users", {})
        orders = data.get("orders", {})
    except Exception as exc:
        print(f"[DB LOAD ERROR] {exc}")
        users, orders = {}, {}


def save_db():
    DB_FILE.write_text(
        json.dumps({"users": users, "orders": orders}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def api(method, payload=None, files=None):
    url = f"{BASE_URL}/{method}"
    last_error = None
    for attempt in range(3):
        try:
            if files:
                response = session.post(url, data=payload or {}, files=files, timeout=90)
            elif payload is None:
                response = session.get(url, timeout=60)
            else:
                response = session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    print(f"[API ERROR] {method}: {last_error}")
    return {"ok": False, "description": str(last_error)}


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api("sendMessage", payload)


def send_photo(chat_id, photo_path, caption="", reply_markup=None):
    payload = {"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    try:
        with open(photo_path, "rb") as photo:
            return api("sendPhoto", payload, {"photo": photo})
    except Exception as exc:
        print(f"[PHOTO ERROR] {exc}")
        return {"ok": False, "description": str(exc)}


def delete_message(chat_id, message_id):
    if message_id:
        api("deleteMessage", {"chat_id": chat_id, "message_id": message_id})


def answer_callback(callback_id, text="", show_alert=False):
    api("answerCallbackQuery", {
        "callback_query_id": callback_id,
        "text": text,
        "show_alert": show_alert,
    })


def is_owner(uid):
    return int(uid) == ADMIN_ID


def remember_user(message):
    u = message.get("from", {})
    uid = int(u.get("id"))
    users[str(uid)] = {
        "id": uid,
        "username": u.get("username") or "",
        "name": u.get("first_name") or "User",
        "last_seen": int(time.time()),
    }
    save_db()
    return uid


def user_label(uid):
    u = users.get(str(uid), {})
    if u.get("username"):
        return "@" + u["username"].lstrip("@")
    return u.get("name") or str(uid)


def user_keyboard(uid=None):
    rows = [
        *([[{"text": "🎨 COLOR MENU", "web_app": {"url": WEB_APP_URL}}]] if WEB_APP_URL else []),
        [{"text": "🎮 FF GUILD GOLORY BOT"}, {"text": "💳 পেমেন্ট"}],
        [{"text": "💎 UID TopUp Bd"}, {"text": "📅 Weekly/Monthly"}],
        [{"text": "📦 আমার অর্ডার"}, {"text": "📢 আপডেট চ্যানেল"}],
        [{"text": "📞 মালিকের সাথে যোগাযোগ"}],
    ]
    if uid is not None and is_owner(uid):
        rows.append([{"text": "🔐 ADMIN"}])
    return {"keyboard": rows, "resize_keyboard": True, "is_persistent": True}


def inline_keyboard(rows):
    return {"inline_keyboard": rows}


def guild_package_keyboard():
    return inline_keyboard([
        [{"text": "4 BOT — 200 TK", "callback_data": "guild_4"},
         {"text": "8 BOT — 400 TK", "callback_data": "guild_8"}],
        [{"text": "12 BOT — 600 TK", "callback_data": "guild_12"},
         {"text": "16 BOT — 800 TK", "callback_data": "guild_16"}],
        [{"text": "20 BOT — 1000 TK", "callback_data": "guild_20"}],
    ])


def uid_package_keyboard():
    return inline_keyboard([
        [{"text": "1. 25 Diamond — 18 TK", "callback_data": "uid_25"},
         {"text": "2. 50 Diamond — 34 TK", "callback_data": "uid_50"}],
        [{"text": "3. 115 Diamond — 69 TK", "callback_data": "uid_115"},
         {"text": "4. 240 Diamond — 160 TK", "callback_data": "uid_240"}],
        [{"text": "5. 355 Diamond — 235 TK", "callback_data": "uid_355"},
         {"text": "6. 480 Diamond — 300 TK", "callback_data": "uid_480"}],
        [{"text": "7. 610 Diamond — 370 TK", "callback_data": "uid_610"},
         {"text": "8. 850 Diamond — 520 TK", "callback_data": "uid_850"}],
        [{"text": "9. 1090 Diamond — 630 TK", "callback_data": "uid_1090"},
         {"text": "10. 1240 Diamond — 700 TK", "callback_data": "uid_1240"}],
        [{"text": "11. 2530 Diamond — 1400 TK", "callback_data": "uid_2530"},
         {"text": "12. 5060 Diamond — 2720 TK", "callback_data": "uid_5060"}],
        [{"text": "13. Level Up Pass — 162 TK", "callback_data": "uid_level"},
         {"text": "14. Weekly — 159 TK", "callback_data": "uid_weekly"}],
        [{"text": "15. Monthly — 700 TK", "callback_data": "uid_monthly"}],
    ])


def weekly_monthly_keyboard():
    return inline_keyboard([
        [{"text": "Weekly — 158 TK", "callback_data": "wm_weekly"},
         {"text": "weekly lite — 45 TK", "callback_data": "wm_weekly_lite"}],
        [{"text": "Monthly — 790 TK", "callback_data": "wm_monthly"},
         {"text": "2X Weekly — 316 TK", "callback_data": "wm_2x_weekly"}],
        [{"text": "3X Weekly — 474 TK", "callback_data": "wm_3x_weekly"},
         {"text": "5X Weekly — 790 TK", "callback_data": "wm_5x_weekly"}],
        [{"text": "2X Monthly — 1580 TK", "callback_data": "wm_2x_monthly"},
         {"text": "1Weekly + 1Monthly — 948 TK", "callback_data": "wm_1weekly_1monthly"}],
        [{"text": "4Weekly + 1Monthly — 1422 TK", "callback_data": "wm_4weekly_1monthly"},
         {"text": "2x weekly lite — 90 TK", "callback_data": "wm_2x_weekly_lite"}],
        [{"text": "3x weekly lite — 135 TK", "callback_data": "wm_3x_weekly_lite"},
         {"text": "5x Weekly Lite — 225 TK", "callback_data": "wm_5x_weekly_lite"}],
    ])


def payment_keyboard(order_id):
    return inline_keyboard([
        [{"text": "📸 পেমেন্ট প্রুফ পাঠান", "callback_data": f"proof_{order_id}"}],
        [{"text": "❌ বাতিল", "callback_data": f"cancel_{order_id}"}],
    ])


def owner_review_keyboard(order_id):
    return inline_keyboard([
        [{"text": "✅ APPROVE", "callback_data": f"approve_{order_id}"},
         {"text": "❌ REJECT", "callback_data": f"reject_{order_id}"}],
    ])


def admin_keyboard():
    return inline_keyboard([
        [{"text": "📋 Pending Orders", "callback_data": "admin_pending"}],
        [{"text": "📦 All Orders", "callback_data": "admin_all"}],
        [{"text": "👥 Users", "callback_data": "admin_users"}],
        [{"text": "🔄 Refresh", "callback_data": "admin_menu"}],
    ])


def cleanup_user_messages(uid):
    for mid in pending_user_messages.pop(str(uid), []):
        delete_message(uid, mid)


def track_user_message(uid, result):
    if result and result.get("ok"):
        pending_user_messages.setdefault(str(uid), []).append(result["result"]["message_id"])


def create_order(uid, package_type, key, name, price, game_uid=None):
    oid = uuid.uuid4().hex[:8].upper()
    orders[oid] = {
        "id": oid,
        "user_id": uid,
        "username": user_label(uid),
        "name": users.get(str(uid), {}).get("name", "User"),
        "type": package_type,
        "package": name,
        "bots": key if package_type == "guild" else 0,
        "price": price,
        "game_uid": game_uid,
        "status": "awaiting_proof",
        "created_at": int(time.time()),
        "proof": None,
        "proof_message_id": None,
        "review_message_id": None,
        "decision_prompt_id": None,
        "delivery_code": None,
        "reject_reason": None,
    }
    save_db()
    return oid


def show_main(uid):
    u = users.get(str(uid), {})
    return send_message(uid, WELCOME.format(name=u.get("name", "User"), user_id=uid), user_keyboard(uid))


def show_guild_packages(uid):
    return send_message(uid, PACKAGE_TEXT, guild_package_keyboard())


def show_uid_packages(uid):
    return send_message(uid, UID_TEXT, uid_package_keyboard())


def show_weekly_monthly_packages(uid):
    return send_message(uid, WEEKLY_MONTHLY_TEXT, weekly_monthly_keyboard())


def show_payment(uid, oid):
    order = orders[oid]
    extra_uid = f"\n🎮 Game UID: <code>{order['game_uid']}</code>" if order.get("game_uid") else ""
    text = (
        f"💳 <b>পেমেন্ট করুন</b>\n\n"
        f"📦 প্যাকেজ: <b>{order['package']}</b>{extra_uid}\n"
        f"💰 মূল্য: <b>{order['price']} TK</b>\n\n"
        f"🟣 <b>bKash:</b> <code>{BKASH_NUMBER}</code>\n"
        "➡️ <b>Send Money</b> করুন\n\n"
        f"🟠 <b>Nagad:</b> <code>{NAGAD_NUMBER}</code>\n"
        "➡️ <b>Cash Out</b> করুন\n\n"
        "পেমেন্ট সম্পন্ন করার পর <b>স্ক্রিনশট</b> পাঠান।"
    )
    return send_message(uid, text, payment_keyboard(oid))


def send_owner_order(oid):
    order = orders.get(oid)
    if not order:
        return False
    uid = order["user_id"]
    uid_line = f"\n🎮 Game UID: <code>{order['game_uid']}</code>" if order.get("game_uid") else ""
    caption = (
        "📥 <b>নতুন Payment Proof</b>\n\n"
        f"🧾 Order: <code>#{oid}</code>\n"
        f"👤 Name: <b>{order['name']}</b>\n"
        f"🔗 Username: <b>{order['username']}</b>\n"
        f"🆔 User ID: <code>{uid}</code>\n"
        f"📦 Package: <b>{order.get('package') or (str(order.get('bots', 0)) + ' BOT')}</b>\n"
        f"💰 Amount: <b>{order['price']} TK</b>"
        f"{uid_line}\n\n"
        "Owner: Approve করলে কোড দিতে পারবেন, Reject করলে কারণ দিতে পারবেন।"
    )
    result = send_photo(ADMIN_ID, order["proof"], caption, owner_review_keyboard(oid))
    if result.get("ok"):
        mid = result["result"]["message_id"]
        order["review_message_id"] = mid
        owner_review_messages[oid] = mid
        save_db()
        return True
    return False


def pending_orders_text():
    rows = [o for o in orders.values() if o.get("status") == "pending"]
    if not rows:
        return "📋 <b>Pending Orders</b>\n\nকোনো pending order নেই।"
    lines = ["📋 <b>Pending Orders</b>\n"]
    for o in rows:
        uid_line = f" | UID: {o['game_uid']}" if o.get("game_uid") else ""
        lines.append(f"• <code>{o.get('id')}</code> — {o.get('package') or (str(o.get('bots', 0)) + ' BOT')} — {o.get('price', 0)} TK — {o.get('username', '(username নেই)')}{uid_line}")
    return "\n".join(lines)


def all_orders_text():
    if not orders:
        return "📦 <b>All Orders</b>\n\nকোনো order নেই।"
    lines = ["📦 <b>All Orders</b>\n"]
    for o in list(orders.values())[-50:]:
        lines.append(f"• <code>{o.get('id')}</code> | {o.get('package') or (str(o.get('bots', 0)) + ' BOT')} | {o.get('price', 0)} TK | {o.get('status')} | {o.get('username', '(username নেই)')}")
    return "\n".join(lines)


def admin_panel(uid):
    if not is_owner(uid):
        return send_message(uid, "⛔ এই Admin Panel শুধু Owner-এর জন্য।", user_keyboard(uid))
    return send_message(uid, "👑 <b>OWNER ADMIN PANEL</b>\n\nPending order-এর screenshot দেখে Approve/Reject করতে পারবেন।", admin_keyboard())


def handle_photo(message, uid):
    state = user_state.get(uid, "")
    if not state.startswith("proof:"):
        send_message(uid, "📸 আগে একটি প্যাকেজ নির্বাচন করুন এবং পেমেন্ট প্রুফ পাঠানোর অপশন চাপুন।", user_keyboard(uid))
        return
    oid = state.split(":", 1)[1]
    order = orders.get(oid)
    if not order or order.get("user_id") != uid or order.get("status") != "awaiting_proof":
        user_state.pop(uid, None)
        send_message(uid, "❌ এই Order আর valid নেই। আবার প্যাকেজ নির্বাচন করুন।", user_keyboard(uid))
        return

    photo = message["photo"][-1]
    gf = api("getFile", {"file_id": photo["file_id"]})
    if not gf.get("ok"):
        send_message(uid, "❌ স্ক্রিনশট নেওয়া যায়নি। আবার চেষ্টা করুন।", user_keyboard(uid))
        return
    tg_path = gf["result"]["file_path"]
    local_path = PROOF_DIR / f"{oid}.jpg"
    try:
        r = session.get(f"https://api.telegram.org/file/bot{TOKEN}/{tg_path}", timeout=60)
        r.raise_for_status()
        local_path.write_bytes(r.content)
    except Exception as exc:
        print(f"[PROOF DOWNLOAD ERROR] {exc}")
        send_message(uid, "❌ স্ক্রিনশট সংরক্ষণ করা যায়নি। আবার চেষ্টা করুন।", user_keyboard(uid))
        return

    order["proof"] = str(local_path)
    order["proof_message_id"] = message["message_id"]
    order["status"] = "pending"
    save_db()

    # Delete the buyer's payment/proof flow messages and the screenshot itself.
    cleanup_user_messages(uid)
    delete_message(uid, message["message_id"])
    user_state.pop(uid, None)

    notice = send_message(uid, THANKS_TEXT, user_keyboard(uid))
    pending_user_messages[str(uid)] = []
    track_user_message(uid, notice)

    if not send_owner_order(oid):
        send_message(uid, "⚠️ Order save হয়েছে, কিন্তু Owner notification পাঠানো যায়নি। Owner bot-এ /start দিয়ে রাখুন এবং আবার চেষ্টা করুন।", user_keyboard(uid))


def finish_owner_decision(uid, oid, action, value):
    order = orders.get(oid)
    if not order:
        user_state.pop(uid, None)
        send_message(uid, "❌ Order পাওয়া যায়নি।", user_keyboard(uid))
        return
    if order.get("status") != "pending":
        user_state.pop(uid, None)
        send_message(uid, "⚠️ এই Order ইতিমধ্যে review করা হয়েছে।", user_keyboard(uid))
        return

    value = value.strip()
    if not value:
        send_message(uid, "⚠️ খালি রাখা যাবে না। আবার লিখুন।")
        return

    if action == "approve":
        order["status"] = "approved"
        order["approved_at"] = int(time.time())
        if order.get("type") in ("uid", "weekly_monthly"):
            # UID TopUp / Weekly-Monthly: no delivery-code field is shown.
            order["delivery_code"] = None
            user_text = (
                "🎉 <b>আপনার অর্ডার APPROVE করা হয়েছে!</b>\n\n"
                f"📦 প্যাকেজ: <b>{order.get('package') or (str(order.get('bots', 0)) + ' BOT')}</b>\n"
                "✅ আপনার অর্ডারটি অনুমোদিত হয়েছে।\n\n"
                "ধন্যবাদ।"
            )
            admin_text = f"✅ Order <code>{oid}</code> approved এবং User-কে confirmation পাঠানো হয়েছে।"
        else:
            order["delivery_code"] = value
            user_text = (
                "🎉 <b>আপনার অর্ডার APPROVE করা হয়েছে!</b>\n\n"
                f"📦 প্যাকেজ: <b>{order.get('package') or (str(order.get('bots', 0)) + ' BOT')}</b>\n"
                f"🎁 আপনার কোড:\n<code>{value}</code>\n\n"
                "ধন্যবাদ।"
            )
            admin_text = f"✅ Order <code>{oid}</code> approved এবং কোড User-এর কাছে পাঠানো হয়েছে।"
    else:
        order["status"] = "rejected"
        order["reject_reason"] = value
        order["rejected_at"] = int(time.time())
        user_text = (
            "❌ <b>আপনার অর্ডারটি Reject করা হয়েছে।</b>\n\n"
            f"📝 কারণ: {value}"
        )
        admin_text = f"❌ Order <code>{oid}</code> rejected এবং কারণ User-এর কাছে পাঠানো হয়েছে।"

    # Remove the old buyer flow messages before sending the final result,
    # so the final APPROVE/REJECT notice remains visible to the buyer.
    cleanup_user_messages(order["user_id"])

    # Remove Owner's review screenshot and any decision-prompt message.
    review_mid = order.get("review_message_id") or owner_review_messages.get(oid)
    if review_mid:
        delete_message(ADMIN_ID, review_mid)
    decision_prompt_mid = order.get("decision_prompt_id")
    if decision_prompt_mid:
        delete_message(ADMIN_ID, decision_prompt_mid)
    owner_review_messages.pop(oid, None)

    save_db()
    send_message(order["user_id"], user_text, user_keyboard(order["user_id"]))
    send_message(ADMIN_ID, admin_text, admin_keyboard())
    user_state.pop(uid, None)


def handle_callback(call):
    uid = int(call.get("from", {}).get("id", 0))
    data = call.get("data", "")
    msg = call.get("message", {})
    msg_id = msg.get("message_id")
    if not uid:
        return

    # Guild Glory package selection
    if data.startswith("guild_"):
        key = data.split("_", 1)[1]
        if key not in GUILD_PACKAGES:
            answer_callback(call["id"], "Invalid package", True)
            return
        p = GUILD_PACKAGES[key]
        oid = create_order(uid, "guild", key, p["name"], p["price"])
        user_state[uid] = f"proof:{oid}"
        result = show_payment(uid, oid)
        track_user_message(uid, result)
        delete_message(uid, msg_id)
        answer_callback(call["id"], "Package selected")
        return

    # UID TopUp package selection -> ask for game UID
    if data in UID_PACKAGES:
        package_name, price = UID_PACKAGES[data]
        user_state[uid] = f"uid_input:{data}"
        result = send_message(
            uid,
            f"💎 <b>{package_name}</b>\n💰 মূল্য: <b>{price} TK</b>\n\n🎮 এখন আপনার <b>Game UID</b> লিখে পাঠান।",
            user_keyboard(uid),
        )
        track_user_message(uid, result)
        delete_message(uid, msg_id)
        answer_callback(call["id"], "UID লিখুন")
        return

    # Weekly/Monthly package selection -> ask for game UID
    if data in WEEKLY_MONTHLY_PACKAGES:
        package_name, price = WEEKLY_MONTHLY_PACKAGES[data]
        user_state[uid] = f"wm_uid_input:{data}"
        result = send_message(
            uid,
            f"📅 <b>{package_name}</b>\n💰 মূল্য: <b>{price} TK</b>\n\n🎮 এখন আপনার <b>Game UID</b> লিখে পাঠান।",
            user_keyboard(uid),
        )
        track_user_message(uid, result)
        delete_message(uid, msg_id)
        answer_callback(call["id"], "UID লিখুন")
        return

    # User pressed payment-proof button
    if data.startswith("proof_"):
        oid = data.split("_", 1)[1]
        order = orders.get(oid)
        if order and order.get("user_id") == uid and order.get("status") == "awaiting_proof":
            user_state[uid] = f"proof:{oid}"
            result = send_message(uid, "📸 এখন আপনার পেমেন্টের <b>স্ক্রিনশট</b> পাঠান।", user_keyboard(uid))
            track_user_message(uid, result)
            answer_callback(call["id"], "Screenshot পাঠান")
        else:
            answer_callback(call["id"], "Order পাওয়া যায়নি", True)
        return

    if data.startswith("cancel_"):
        oid = data.split("_", 1)[1]
        order = orders.get(oid)
        if order and order.get("user_id") == uid:
            order["status"] = "cancelled"
            save_db()
            user_state.pop(uid, None)
            cleanup_user_messages(uid)
            delete_message(uid, msg_id)
            show_main(uid)
            answer_callback(call["id"], "Cancelled")
        else:
            answer_callback(call["id"], "Order পাওয়া যায়নি", True)
        return

    # Everything below is Owner-only.
    if not is_owner(uid):
        answer_callback(call["id"], "⛔ Owner only", True)
        return

    if data == "admin_menu":
        admin_panel(uid)
        answer_callback(call["id"])
        return
    if data == "admin_pending":
        send_message(uid, pending_orders_text(), admin_keyboard())
        answer_callback(call["id"])
        return
    if data == "admin_all":
        send_message(uid, all_orders_text(), admin_keyboard())
        answer_callback(call["id"])
        return
    if data == "admin_users":
        send_message(uid, f"👥 <b>Total Users:</b> {len(users)}", admin_keyboard())
        answer_callback(call["id"])
        return

    if data.startswith("approve_") or data.startswith("reject_"):
        action, oid = data.split("_", 1)
        order = orders.get(oid)
        if not order or order.get("status") != "pending":
            answer_callback(call["id"], "এই order আর pending নেই।", True)
            return
        # UID TopUp / Weekly-Monthly approval does not need a code.
        if action == "approve" and order.get("type") in ("uid", "weekly_monthly"):
            finish_owner_decision(uid, oid, action, "APPROVED")
            answer_callback(call["id"], "Approved")
            return
        user_state[uid] = f"{action}:{oid}"
        if action == "approve":
            prompt = send_message(uid, f"✅ Order <code>{oid}</code> Approve করতে User-কে যে <b>কোড</b> দিতে চান সেটি লিখে পাঠান:")
        else:
            prompt = send_message(uid, f"❌ Order <code>{oid}</code> Reject করতে <b>কারণ</b> লিখে পাঠান:")
        if prompt and prompt.get("ok"):
            order["decision_prompt_id"] = prompt["result"]["message_id"]
            save_db()
        answer_callback(call["id"], "লিখে পাঠান")
        return

    answer_callback(call["id"])


def handle_text(message, uid):
    text = (message.get("text") or "").strip()

    if text.startswith("/start"):
        show_main(uid)
        return
    if text == "/admin" or text in ("🔐 ADMIN", "Admin", "admin"):
        admin_panel(uid)
        return

    # Owner's typed code/rejection reason
    state = user_state.get(uid, "")
    if is_owner(uid) and (state.startswith("approve:") or state.startswith("reject:")):
        action, oid = state.split(":", 1)
        finish_owner_decision(uid, oid, action, text)
        return

    # UID input after selecting a Weekly/Monthly package
    if state.startswith("wm_uid_input:"):
        key = state.split(":", 1)[1]
        if key not in WEEKLY_MONTHLY_PACKAGES:
            user_state.pop(uid, None)
            send_message(uid, "❌ Package session শেষ হয়েছে। আবার Weekly/Monthly নির্বাচন করুন।", user_keyboard(uid))
            return
        game_uid = text
        if not game_uid.isdigit() or not (5 <= len(game_uid) <= 15):
            send_message(uid, "⚠️ সঠিক Game UID লিখুন (শুধু সংখ্যা)।", user_keyboard(uid))
            return
        package_name, price = WEEKLY_MONTHLY_PACKAGES[key]
        oid = create_order(uid, "weekly_monthly", key, package_name, price, game_uid=game_uid)
        user_state[uid] = f"proof:{oid}"
        result = show_payment(uid, oid)
        track_user_message(uid, result)
        return

    # UID input after selecting a UID TopUp package
    if state.startswith("uid_input:"):
        key = state.split(":", 1)[1]
        if key not in UID_PACKAGES:
            user_state.pop(uid, None)
            send_message(uid, "❌ Package session শেষ হয়েছে। আবার UID TopUp Bd নির্বাচন করুন।", user_keyboard(uid))
            return
        game_uid = text
        if not game_uid.isdigit() or not (5 <= len(game_uid) <= 15):
            send_message(uid, "⚠️ সঠিক Game UID লিখুন (শুধু সংখ্যা)।", user_keyboard(uid))
            return
        package_name, price = UID_PACKAGES[key]
        oid = create_order(uid, "uid", key, package_name, price, game_uid=game_uid)
        user_state[uid] = f"proof:{oid}"
        result = show_payment(uid, oid)
        track_user_message(uid, result)
        return

    if text == "🎮 FF GUILD GOLORY BOT":
        show_guild_packages(uid)
        return
    if text == "💎 UID TopUp Bd":
        show_uid_packages(uid)
        return
    if text == "📅 Weekly/Monthly":
        show_weekly_monthly_packages(uid)
        return
    if text == "💳 পেমেন্ট":
        # Show the most recent unfinished order.
        for oid in reversed(list(orders.keys())):
            o = orders[oid]
            if o.get("user_id") == uid and o.get("status") == "awaiting_proof":
                result = show_payment(uid, oid)
                track_user_message(uid, result)
                return
        send_message(uid, "🎮 আগে একটি প্যাকেজ নির্বাচন করুন।", user_keyboard(uid))
        return
    if text == "📦 আমার অর্ডার":
        mine = [o for o in orders.values() if o.get("user_id") == uid]
        if not mine:
            send_message(uid, "📦 আপনার কোনো Order নেই।", user_keyboard(uid))
            return
        lines = ["📦 <b>আমার অর্ডার</b>\n"]
        for o in mine[-10:]:
            lines.append(f"• <code>{o['id']}</code> — {o['package']} — {o['price']} TK — {o['status']}")
        send_message(uid, "\n".join(lines), user_keyboard(uid))
        return
    if text == "📢 আপডেট চ্যানেল":
        send_message(uid, "📢 আপডেট চ্যানেলের লিংক এখানে সেট করুন।", user_keyboard(uid))
        return
    if text == "📞 মালিকের সাথে যোগাযোগ":
        send_message(uid, f"📞 মালিকের সাথে যোগাযোগ: {OWNER_USERNAME}", user_keyboard(uid))
        return

    send_message(uid, "👇 মেনু থেকে একটি অপশন নির্বাচন করুন।", user_keyboard(uid))


def handle_web_app_data(message, uid):
    raw = ((message.get("web_app_data") or {}).get("data") or "").strip()
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {"action": raw}
    action = str(payload.get("action", ""))

    # Main-menu actions from the Mini App
    if action == "guild_menu":
        show_guild_packages(uid); return
    if action == "uid_menu":
        show_uid_packages(uid); return
    if action == "wm_menu":
        show_weekly_monthly_packages(uid); return
    if action == "payment":
        handle_text({"text": "💳 পেমেন্ট"}, uid); return
    if action == "orders":
        handle_text({"text": "📦 আমার অর্ডার"}, uid); return
    if action == "owner":
        handle_text({"text": "📞 মালিকের সাথে যোগাযোগ"}, uid); return
    if action == "channel":
        handle_text({"text": "📢 আপডেট চ্যানেল"}, uid); return

    # Package selections reuse the bot's existing callback logic.
    if action.startswith(("guild_", "uid_", "wm_")):
        fake_call = {"id": "webapp", "from": message.get("from", {}), "data": action,
                     "message": {"message_id": message.get("message_id")}}
        handle_callback(fake_call)
        return

    send_message(uid, "👇 Mini App থেকে একটি অপশন নির্বাচন করুন।", user_keyboard(uid))


def handle_update(update):
    if "message" in update:
        message = update["message"]
        uid = remember_user(message)
        if message.get("web_app_data"):
            handle_web_app_data(message, uid)
        elif message.get("photo"):
            handle_photo(message, uid)
        else:
            handle_text(message, uid)
    elif "callback_query" in update:
        handle_callback(update["callback_query"])


def poll():
    offset = None
    print("Bot is running...")
    print("Owner ID:", ADMIN_ID)
    while True:
        try:
            payload = {"timeout": 50}
            if offset is not None:
                payload["offset"] = offset
            result = api("getUpdates", payload)
            if not result.get("ok"):
                print("[POLL ERROR]", result.get("description"))
                time.sleep(3)
                continue
            for update in result.get("result", []):
                offset = update["update_id"] + 1
                handle_update(update)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as exc:
            print(f"[LOOP ERROR] {exc}")
            time.sleep(3)


if __name__ == "__main__":
    load_db()
    if not TOKEN:
        raise SystemExit("BOT_TOKEN is empty")
    me = api("getMe")
    if not me.get("ok"):
        print("ERROR: Telegram API connection/token is invalid.")
        print(me.get("description", "Unknown error"))
        raise SystemExit(1)
    print("Connected as @" + me["result"].get("username", "unknown"))
    if WEB_APP_URL:
        api("setChatMenuButton", {"menu_button": {"type": "web_app", "text": "🎨 Color Menu", "web_app": {"url": WEB_APP_URL}}})
        print("Mini App:", WEB_APP_URL)
    poll()
