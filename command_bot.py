import asyncio
import json
import os

import requests

from digest_core import BOT_TOKEN, MY_CHAT_ID, HOURS_WINDOW, run_digest, send_message

STATE_FILE = "bot_state.json"
COMMAND_DIGEST = "/todaynews"
COMMAND_START = "/start"
COMMAND_HELP = "/help"


def load_offset():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("offset", 0)
        except Exception:
            return 0
    return 0


def save_offset(offset):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"offset": offset}, f)
    except Exception as e:
        print(f"خطا در ذخیره آفست: {e}")


def get_updates(offset):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    resp = requests.get(url, params={"offset": offset, "timeout": 0}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("result", [])


async def process_commands():
    offset = load_offset()
    try:
        updates = get_updates(offset)
    except Exception as e:
        print(f"خطا در دریافت آپدیت‌ها: {e}")
        return

    if not updates:
        print("پیام جدیدی نبود.")
        return

    max_update_id = offset
    digest_requested = False

    for update in updates:
        update_id = update.get("update_id", 0)
        max_update_id = max(max_update_id, update_id + 1)

        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        chat_id = str(message.get("chat", {}).get("id", ""))

        if not text or not chat_id:
            continue

        cmd = text.split("@")[0].lower()

        # چک کردن دسترسی چت مجاز
        if chat_id != str(MY_CHAT_ID):
            print(f"پیام از کاربر ناشناس دریافت شد: {chat_id}")
            send_message(chat_id, "⛔️ دسترسی شما به این ربات مجاز نیست.")
            continue

        if cmd in (COMMAND_START, COMMAND_HELP):
            print(f"کامند {cmd} دریافت شد.")
            welcome_msg = (
                "👋 **سلام! به TeleBrief خوش آمدید.**\n\n"
                "برای دریافت خلاصه و تحلیل اخبار امنیت سایبری ۱۲ ساعت گذشته، دستور زیر را ارسال کنید:\n"
                "👉 `/todaynews`"
            )
            send_message(chat_id, welcome_msg)

        elif cmd == COMMAND_DIGEST:
            print("درخواست /todaynews دریافت شد.")
            digest_requested = True

    # آفست رو ذخیره کن
    save_offset(max_update_id)

    if digest_requested:
        print("در حال آماده‌سازی و ارسال گزارش...")
        count = await run_digest(MY_CHAT_ID, hours=HOURS_WINDOW, include_date_header=True)
        print(f"گزارش ارسال شد. تعداد پیام: {count}")


if __name__ == "__main__":
    asyncio.run(process_commands())

