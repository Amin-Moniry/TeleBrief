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

def get_env_str(key, default=""):
    val = os.environ.get(key, default)
    if val:
        return str(val).strip().strip("\"'")
    return default


def get_env_int(key, default=0):
    val = os.environ.get(key, "")
    if val:
        cleaned = str(val).strip().strip("\"'")
        if cleaned.isdigit():
            return int(cleaned)
    return default


# این موارد مستقیماً از متغیرهای محیطی خوانده می‌شوند
API_ID = get_env_int("API_ID", 0)
API_HASH = get_env_str("API_HASH", "")
SESSION_STRING = get_env_str("SESSION_STRING", "")
BOT_TOKEN = get_env_str("BOT_TOKEN", "")
MY_CHAT_ID = get_env_str("MY_CHAT_ID", "")
XKIRO_API_KEY = get_env_str("XKIRO_API_KEY", "")
API_BASE_URL = get_env_str("API_BASE_URL", "")

# این دو مورد با مقدار پیش‌فرض در کد باقی می‌مانند
XKIRO_MODEL = get_env_str("DEFAULT_MODEL", "deepseek/deepseek-v4-pro")
HOURS_WINDOW = get_env_int("HOURS_WINDOW", 12)

SECURITY_CHANNELS = [
    "cybersecurityexperts",
    "thehackernews",
    "cibsecurity",
    "Cyber_Security_Channel",
    "androidMalware",
    "cloudandcybersecurity",
]

AI_CHANNELS = [
    "digiai",
    "RoidBest",
    "Farda_Ai",
    "Lumosel",
    "asrnovin_ir",
    "perplexity",
    "cryptoquant_official",
    "hiaimediaen",
    "Hugging_face_news",
    "samiotech",
]

# برای سازگاری با کد قدیمی
CHANNELS = SECURITY_CHANNELS

FOOTER = "\n\n[𝐉𝐎𝐈𝐍](https://t.me/telebriefdata_bot) ➣ telebriefdata_bot"


# ============================================================


async def fetch_channel_messages(hours=HOURS_WINDOW, channels=None):
    """پیام‌های N ساعت اخیر را به تفکیک هر کانال و به ترتیب زمانی جمع‌آوری می‌کند."""
    if channels is None:
        channels = CHANNELS

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    channel_messages = {}

    for channel in channels:
        channel_msgs = []
        try:
            async for msg in client.iter_messages(channel, limit=300):
                if msg.date < since:
                    break
                if msg.text and msg.text.strip():
                    channel_msgs.append({
                        "id": msg.id,
                        "date": msg.date.isoformat() if msg.date else None,
                        "reply_to": getattr(msg, "reply_to_msg_id", None),
                        "text": msg.text.strip(),
                    })
            if channel_msgs:
                # مرتب‌سازی به ترتیب زمانی (قدیمی به جدید) برای حفظ جریان مکالمه و سیر رخدادها
                channel_msgs.reverse()
                channel_messages[channel] = channel_msgs
        except Exception as e:
            print(f"خطا در خواندن کانال {channel}: {e}")

    await client.disconnect()
    return channel_messages


async def fetch_recent_messages(hours=HOURS_WINDOW, channels=None):
    """سازگاری با نسخه‌های پیشین: برگرداندن همه پیام‌ها به شکل یک لیست مسطح."""
    channel_msgs = await fetch_channel_messages(hours=hours, channels=channels)
    all_msgs = []
    for channel, msgs in channel_msgs.items():
        for m in msgs:
            all_msgs.append({"id": m["id"], "channel": channel, "text": m["text"]})
    return all_msgs


def build_channel_summary_prompt(channel, messages, category="security"):
    """ایجاد پرامپت عمیق، چندبخشی و تحلیلی برای کل مکالمات یک کانال."""
    blocks = []
    for m in messages:
        reply_info = f" [در پاسخ به پیام #{m['reply_to']}]" if m.get("reply_to") else ""
        text = m["text"]
        # اگر پیامی خیلی بلند بود، برای جلوگیری از سرریز توکن محدود می‌شود
        if len(text) > 2500:
            text = text[:2500] + " ... [ادامه متن طولانی کوتاه شد]"
        blocks.append(f"[پیام #{m['id']}]{reply_info}\n{text}")

    joined = "\n\n---\n\n".join(blocks)
    category_label = "هوش مصنوعی و یادگیری ماشین" if category == "ai" else "امنیت سایبری و تحلیل تهدیدات"

    return (
        f"شما یک تحلیل‌گر ارشد و پژوهشگر متخصص در حوزه {category_label} هستید.\n"
        f"در ادامه، تمامی پیام‌ها و بحث‌های منتشرشده در کانال تلگرام «{channel}» در ساعات اخیر به ترتیب زمانی آورده شده است.\n\n"
        "دستورالعمل‌های تحلیل:\n"
        "۱. تمام پیام‌ها و رشته‌مکالمات را با دقت، پیوستگی و یکپارچگی کامل بخوانید و تحلیل کنید (به هیچ عنوان به قضاوت یک‌خطی یا تمرکز روی تک‌پست‌ها بسنده نکنید).\n"
        "۲. هدف اصلی، ارائه یک خلاصه جامع، عمیق و کاربردی از کل رخدادها و مباحث این کانال است.\n"
        "۳. تبلیغات محض، اسپم، کلیک‌بیت‌های توخالی یا پیام‌های تبریک/احوال‌پرسی را کاملاً فیلتر کنید.\n"
        "۴. نکات کلیدی، یافته‌ها، تصمیمات، ابزارها یا اقدامات عملی و سوالات بی‌پاسخ را مشخص کنید.\n\n"
        "خروجی را **فقط و فقط** به صورت یک شیء JSON استاندارد بدون هیچ توضیح اضافی و بدون تگ مارک‌داون (```json) به این فرمت تولید کنید:\n"
        "{\n"
        f'  "channel": "{channel}",\n'
        '  "has_substantive_content": true,\n'
        '  "headline": "یک تیتر تحلیلی، رسا و محوری از رویدادها یا تم اصلی کانال (حداکثر ۱۰ کلمه)",\n'
        '  "overview": "یک یا دو پاراگراف تحلیلی و پیوسته (۳ الی ۵ خط) از جریان کلی مطالب، تحولات و رخدادهای کانال",\n'
        '  "key_topics": ["موضوع و محور بحث ۱", "موضوع و محور بحث ۲"],\n'
        '  "takeaways": ["یافته فنی، تصمیم یا نکته کلیدی ۱", "نتیجه‌گیری یا دستاورد مهم ۲"],\n'
        '  "action_items": ["اقدام عملی، توصیه کاربردی، یا ابزار/منبع معرفی‌شده"],\n'
        '  "open_questions": ["ابهامات، چالش‌ها، یا پرسش‌های باز مطرح‌شده در مباحث"]\n'
        "}\n\n"
        "قوانین مهم:\n"
        "- اگر تمامی پیام‌های کانال صرفاً تبلیغاتی، اسپم یا فاقد محتوای معنادار بودند، مقدار \"has_substantive_content\" را false قرار دهید.\n"
        "- همه متون باید به فارسی روان، شیوا و استاندارد نگارش شوند.\n"
        "- اگر برای فیلدی (مثل open_questions یا action_items) موردی در متن وجود نداشت، آن را به صورت لیست خالی [] بگذارید.\n\n"
        f"پیام‌های کانال {channel}:\n{joined}"
    )


def analyze_channel(channel, messages, category="security"):
    """ارسال متن کامل پیام‌های یک کانال به هوش مصنوعی و دریافت خلاصه ساختاریافته."""
    if not messages:
        return None

    prompt = build_channel_summary_prompt(channel, messages, category)

    response = None
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
            break
        except requests.exceptions.HTTPError as http_err:
            print(f"خطای HTTP در تحلیل کانال {channel} (تلاش {attempt + 1}): {http_err}")
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception as e:
            print(f"خطا در ارتباط با مدل برای کانال {channel} (تلاش {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return None

    if not response:
        return None

    try:
        raw = response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"خطا در استخراج متن پاسخ برای کانال {channel}: {e}")
        return None

    # حذف تگ‌های احتمالی مارک‌داون
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception as e:
        print(f"خطا در پردازش JSON خروجی کانال {channel}: {e}")
        print("خروجی خام:", raw[:300])

    return None


def format_channel_summary(summary, category="security"):
    """فرمت‌بندی زیبای خلاصه تحلیلی یک کانال برای ارسال در تلگرام."""
    channel = summary.get("channel", "")
    headline = summary.get("headline", "").strip()
    overview = summary.get("overview", "").strip()
    key_topics = summary.get("key_topics", [])
    takeaways = summary.get("takeaways", [])
    action_items = summary.get("action_items", [])
    open_questions = summary.get("open_questions", [])

    cat_emoji = "🤖" if category == "ai" else "🔒"
    lines = [f"{cat_emoji} **تحلیل جامع کانال @{channel}**"]

    if headline:
        lines.append(f"\n🎯 **{headline}**")

    if overview:
        lines.append(f"\n📝 {overview}")

    if key_topics:
        lines.append("\n📌 **موضوعات کلیدی:**")
        for item in key_topics:
            lines.append(f"• {item}")

    if takeaways:
        lines.append("\n💡 **یافته‌ها و نکات کلیدی:**")
        for item in takeaways:
            lines.append(f"• {item}")

    if action_items:
        lines.append("\n🛠️ **اقدامات و منابع:**")
        for item in action_items:
            lines.append(f"• {item}")

    if open_questions:
        lines.append("\n❓ **پرسش‌ها و چالش‌های باز:**")
        for item in open_questions:
            lines.append(f"• {item}")

    lines.append(f"\n🔗 [مشاهده کانال](https://t.me/{channel})")
    lines.append(FOOTER)

    return "\n".join(lines)


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


def send_digest(chat_id, summaries, include_date_header=False, hours=HOURS_WINDOW, total_messages=0, active_channels_count=0, category="security"):
    """ارسال خلاصه‌های تحلیلی کانال‌ها به همراه آمار به کاربر."""
    if include_date_header:
        send_message(chat_id, format_date_header(hours))
        time.sleep(1)

    category_name = "🤖 هوش مصنوعی" if category == "ai" else "🔒 امنیت سایبری"

    if total_messages > 0:
        stats_message = (
            f"📊 در بازه گذشته، {total_messages} پیام در {active_channels_count} کانال فعال "
            f"از دسته {category_name} بررسی و تحلیل شد."
        )
        send_message(chat_id, stats_message)
        time.sleep(1)

    if not summaries:
        no_news_msg = f"🟣 در پیام‌های اخیر کانال‌های {category_name}، موضوع تحلیلی برجسته‌ای یافت نشد." + FOOTER
        send_message(chat_id, no_news_msg)
        return

    for s in summaries:
        formatted = format_channel_summary(s, category=category)
        send_message(chat_id, formatted)
        time.sleep(1.5)  # جلوگیری از محدودیت نرخ ارسال تلگرام


async def run_digest(chat_id, hours=HOURS_WINDOW, include_date_header=False, category="security"):
    """جمع‌آوری کامل پیام‌ها، تحلیل عمیق رشته‌پیام‌ها به تفکیک کانال، و ارسال گزارش تحلیلی."""
    channels = AI_CHANNELS if category == "ai" else SECURITY_CHANNELS
    category_name = "🤖 هوش مصنوعی" if category == "ai" else "🔒 امنیت سایبری"

    channel_messages = await fetch_channel_messages(hours, channels=channels)
    total_messages = sum(len(msgs) for msgs in channel_messages.values())
    active_channels_count = len(channel_messages)

    if total_messages == 0:
        if include_date_header:
            send_message(chat_id, format_date_header(hours))
            time.sleep(1)
        send_message(chat_id, f"🟣 در {hours} ساعت گذشته هیچ پیامی در کانال‌های {category_name} منتشر نشده است." + FOOTER)
        return 0

    summaries = []
    for channel, msgs in channel_messages.items():
        print(f"در حال تحلیل کانال {channel} ({len(msgs)} پیام)...")
        try:
            summary = analyze_channel(channel, msgs, category=category)
            if summary and summary.get("has_substantive_content", True):
                summaries.append(summary)
        except Exception as e:
            print(f"خطا در فرآیند تحلیل کانال {channel}: {e}")

    send_digest(
        chat_id,
        summaries,
        include_date_header=include_date_header,
        hours=hours,
        total_messages=total_messages,
        active_channels_count=active_channels_count,
        category=category,
    )
    return len(summaries)
