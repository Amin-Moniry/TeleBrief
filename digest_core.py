import os
import json
import time
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    TEHRAN_TZ = ZoneInfo("Asia/Tehran")
except Exception:
    TEHRAN_TZ = None

import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

# ============ تنظیمات ============

def get_env_int(key, default=0):
    val = os.environ.get(key, "")
    if val and str(val).strip().isdigit():
        return int(str(val).strip())
    return default

# این موارد مستقیماً از سکرت‌های گیت‌هاب خوانده می‌شوند
API_ID = get_env_int("API_ID", 0)
API_HASH = os.environ.get("API_HASH", "").strip()
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
MY_CHAT_ID = os.environ.get("MY_CHAT_ID", "").strip()
XKIRO_API_KEY = os.environ.get("XKIRO_API_KEY", "").strip()
API_BASE_URL = os.environ.get("API_BASE_URL", "").strip()

# این دو مورد با مقدار پیش‌فرض در کد باقی می‌مانند
XKIRO_MODEL = os.environ.get("DEFAULT_MODEL", "deepseek/deepseek-v4-pro").strip()
HOURS_WINDOW = get_env_int("HOURS_WINDOW", 12)

CHANNELS = [
    "cybersecurityexperts",
    "thehackernews",
    "cibsecurity",
    "Cyber_Security_Channel",
    "androidMalware",
    "cloudandcybersecurity",
]

FOOTER = "\n\n[𝐉𝐎𝐈𝐍](https://t.me/telebriefdata_bot) ➣ telebriefdata_bot"


# ============================================================


async def fetch_recent_messages(hours=HOURS_WINDOW):
    """پیام‌های N ساعت اخیر همهٔ کانال‌ها رو با آیدی‌شون جمع می‌کنه."""
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    all_messages = []

    for channel in CHANNELS:
        try:
            async for msg in client.iter_messages(channel, limit=300):
                if msg.date < since:
                    break
                if msg.text:
                    all_messages.append(
                        {"id": msg.id, "channel": channel, "text": msg.text}
                    )
        except Exception as e:
            print(f"خطا در خوندن کانال {channel}: {e}")

    await client.disconnect()
    return all_messages


def build_prompt(messages):
    blocks = []
    for m in messages:
        blocks.append(f"[id:{m['id']}] [channel:{m['channel']}]\n{m['text']}")
    joined = "\n\n---\n\n".join(blocks)

    return (
        "زیر پیام‌های چند ساعت اخیر چند کانال تلگرام هست.\n\n"
        "وظیفهٔ تو اینه که خودت تشخیص بدی کدوم پیام‌ها واقعاً ارزشمندن. "
        "هیچ محدودیتی تو تعداد نداری - اگه فقط ۲ تا مهم بود همون ۲ تا، اگه ۳۰ تا مهم بود همون ۳۰ تا رو برگردون.\n\n"
        "این‌ها رو ارزشمند حساب کن:\n"
        "- خبر واقعی و مهم (رویداد، تغییر قیمت بزرگ، اتفاق مهم اقتصادی/سیاسی/تکنولوژی/امنیتی)\n"
        "- دیتا یا آمار قابل استناد\n"
        "- معرفی یه ابزار، سرویس، یا منبع واقعاً کاربردی\n"
        "- تحلیل یا نکتهٔ آموزشی که واقعاً چیزی یاد می‌ده\n"
        "- برای کانال‌های امنیتی: آسیب‌پذیری تازه (CVE)، حمله یا نشت اطلاعات واقعی، ابزار امنیتی جدید، هشدار فوری\n\n"
        "این‌ها رو کاملاً کنار بذار:\n"
        "- تبلیغات (مستقیم یا پنهون، مثل 'همین الان عضو شو'، تخفیف، پروموشن کانال دیگه)\n"
        "- کلیک‌بیت بدون اطلاعات واقعی\n"
        "- پیام‌های تکراری یا حاشیه‌ای\n\n"
        "خروجی رو **فقط و فقط** به‌صورت یک آرایهٔ JSON خام بده، بدون هیچ متن اضافه، بدون ```، بدون توضیح.\n"
        "هر آیتم باید این شکل باشه:\n"
        "{\n"
        '  "id": (همون id عددی پیام از ورودی),\n'
        '  "channel": (همون channel پیام از ورودی، دقیقاً یکسان),\n'
        '  "title": (یک عنوان کوتاه فارسی، حداکثر ۸ کلمه),\n'
        '  "summary": (خلاصهٔ ۱ تا ۲ خطی به فارسی),\n'
        '  "reason": (چرا این مهمه، به فارسی),\n'
        '  "type": (یکی از: خبر / دیتا / ابزار / آموزش / هشدار امنیتی)\n'
        "}\n\n"
        "اگه هیچ پیام مهمی نبود، آرایهٔ خالی [] برگردون.\n"
        "همهٔ متن‌های title و summary و reason باید فارسی و اول جمله حتماً یک حرف فارسی باشه (نه لینک، نه عدد، نه انگلیسی).\n\n"
        f"پیام‌ها:\n{joined}"
    )


def get_ai_picks(messages):
    if not messages:
        return []

    prompt = build_prompt(messages)
    # حداکثر 3 بار تلاش می‌کنیم تا API به مشکل‌ساز نشود
    for attempt in range(3):
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {XKIRO_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": XKIRO_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=180,
            )
            response.raise_for_status()
            break  # موفقیت‌آمیز
        except requests.exceptions.HTTPError as http_err:
            # 5xx یعنی مشکل سرور، یکبار صبر می‌کنیم و دوباره سعی می‌کنیم
            print(f"خطای HTTP در درخواست XKIRO (تلاش {attempt + 1}): {http_err}")
            if attempt < 2:
                import time
                time.sleep(2 ** attempt)  # back‑off کوتاه
                continue
            else:
                print("به‌نظر می‌رسد سرویس XKIRO در دسترس نیست. خروجی خالی بازگردانده می‌شود.")
                return []
        except Exception as e:
            print(f"خطا در ارتباط با XKIRO (تلاش {attempt + 1}): {e}")
            if attempt < 2:
                import time
                time.sleep(2 ** attempt)
                continue
            else:
                return []

    raw = response.json()["choices"][0]["message"]["content"].strip()

    # اگر مدل خروجی با ``` احاطه شده بود، آن را پاک می‌کنیم
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        picks = json.loads(raw)
        if not isinstance(picks, list):
            picks = []
    except Exception as e:
        print("خطا در پردازش خروجی مدل:", e)
        print("خروجی خام مدل:", raw)
        picks = []
    return picks


def format_message(pick):
    channel = pick.get("channel", "")
    msg_id = pick.get("id", "")
    title = pick.get("title", "بدون عنوان")
    summary = pick.get("summary", "")
    reason = pick.get("reason", "")
    msg_type = pick.get("type", "")

    link = f"https://t.me/{channel}/{msg_id}" if channel and msg_id else None

    text = f"🟣 {title}\n\n{summary}"
    if reason:
        text += f"\n\nچرا مهمه: {reason}"
    if msg_type:
        text += f"\nنوع: {msg_type}"
    if link:
        text += f"\n\n🔗 [مشاهده در کانال]({link})"
    text += FOOTER

    return text


def format_date_header(hours=HOURS_WINDOW):
    now = datetime.now(TEHRAN_TZ) if TEHRAN_TZ else datetime.now()
    since = now - timedelta(hours=hours)
    fmt = "%Y/%m/%d - %H:%M"
    return (
        f"📅 این گزارش مربوط به {hours} ساعت گذشته است\n"
        f"از {since.strftime(fmt)} تا {now.strftime(fmt)}"
    )


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code != 200:
            print(f"هشدار: ارسال با Markdown ناموفق بود ({resp.status_code}): {resp.text}")
            # تلاش مجدد بدون Markdown اگر خطای فرمت بود
            payload.pop("parse_mode")
            retry_resp = requests.post(url, json=payload, timeout=30)
            if retry_resp.status_code == 200:
                print("پیام به صورت متن ساده با موفقیت ارسال شد.")
            else:
                print(f"خطا در ارسال پیام ساده ({retry_resp.status_code}): {retry_resp.text}")
        else:
            print("پیام با موفقیت ارسال شد.")
    except Exception as e:
        print(f"خطا در ارتباط با سرور تلگرام: {e}")


def send_digest(chat_id, picks, include_date_header=False, hours=HOURS_WINDOW):
    if include_date_header:
        send_message(chat_id, format_date_header(hours))
        time.sleep(1)

    if not picks:
        send_message(chat_id, "🟣 تو این بازه پیام مهمی پیدا نشد." + FOOTER)
        return

    for pick in picks:
        send_message(chat_id, format_message(pick))
        time.sleep(1)  # جلوگیری از محدودیت نرخ ارسال تلگرام


async def run_digest(chat_id, hours=HOURS_WINDOW, include_date_header=False):
    """جمع‌آوری پیام‌ها، انتخاب با AI، و ارسال. برای هر دو حالت زمان‌بندی و کامندی استفاده می‌شه."""
    messages = await fetch_recent_messages(hours)
    picks = get_ai_picks(messages)
    send_digest(chat_id, picks, include_date_header=include_date_header, hours=hours)
    return len(picks)
