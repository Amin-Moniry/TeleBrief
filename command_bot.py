import asyncio
import json
import os

import requests

from digest_core import BOT_TOKEN, MY_CHAT_ID, HOURS_WINDOW, run_digest

STATE_FILE = "bot_state.json"
COMMAND = "/todaynews"


def load_offset():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("offset", 0)
        except Exception:
            return 0
    return 0


def save_offset(offset):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"offset": offset}, f)


def get_updates(offset):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    resp = requests.get(url, params={"offset": offset, "timeout": 0}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("result", [])


async def process_commands():
    offset = load_offset()
    updates = get_updates(offset)

    if not updates:
        print("پیام جدیدی نبود.")
        return

    max_update_id = offset
    triggered = False

    for update in updates:
        update_id = update.get("update_id", 0)
        # آفست بعدی باید یکی بیشتر از بزرگترین update_id باشه
        max_update_id = max(max_update_id, update_id + 1)

        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        chat_id = str(message.get("chat", {}).get("id", ""))

        # فقط به کامندی که از چت خودمون اومده واکنش نشون بده
        if chat_id != str(MY_CHAT_ID):
            continue

        # پشتیبانی از هر دو حالت /todaynews و /todaynews@BotUsername
        if text.split("@")[0] == COMMAND:
            triggered = True

    # آفست رو همیشه ذخیره کن، حتی اگه کامندی پیدا نشد، تا پیام‌های قدیمی دوباره چک نشن
    save_offset(max_update_id)

    if triggered:
        print("درخواست /todaynews دریافت شد، در حال آماده‌سازی گزارش...")
        count = await run_digest(MY_CHAT_ID, hours=HOURS_WINDOW, include_date_header=True)
        print(f"گزارش ارسال شد. {count} پیام.")
    else:
        print("کامند مرتبطی پیدا نشد.")


if __name__ == "__main__":
    asyncio.run(process_commands())
