import os
import json
import asyncio
from datetime import datetime

from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

from digest_core import (
    run_digest,
    API_ID,
    API_HASH,
    SESSION_STRING,
    BOT_TOKEN,
    MY_CHAT_ID,
    HOURS_WINDOW,
)


# ============ مدیریت وضعیت کاربران ============

STATE_FILE = "bot_state.json"


def load_state():
    """بارگذاری وضعیت از فایل"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"خطا در خواندن state file: {e}")
            return {"users": {}, "last_update_id": 0}
    return {"users": {}, "last_update_id": 0}


def save_state(state):
    """ذخیره وضعیت در فایل"""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"خطا در ذخیره state file: {e}")


def is_first_time_user(user_id):
    """بررسی اینکه آیا کاربر برای اولین بار است"""
    state = load_state()
    user_id_str = str(user_id)
    return user_id_str not in state.get("users", {})


def mark_user_as_seen(user_id):
    """علامت‌گذاری کاربر به عنوان دیده شده"""
    state = load_state()
    if "users" not in state:
        state["users"] = {}

    user_id_str = str(user_id)
    state["users"][user_id_str] = {
        "first_seen": datetime.now().isoformat(),
        "last_interaction": datetime.now().isoformat(),
    }
    save_state(state)


def update_user_interaction(user_id):
    """به‌روزرسانی زمان آخرین تعامل کاربر"""
    state = load_state()
    user_id_str = str(user_id)

    if "users" not in state:
        state["users"] = {}

    if user_id_str in state["users"]:
        state["users"][user_id_str]["last_interaction"] = datetime.now().isoformat()
    else:
        state["users"][user_id_str] = {
            "first_seen": datetime.now().isoformat(),
            "last_interaction": datetime.now().isoformat(),
        }

    save_state(state)


# ============ تابع ارسال منوی انتخاب دسته ============


async def send_category_menu(bot, chat_id):
    """ارسال منوی انتخاب دسته با دکمه‌ها"""
    buttons = [
        [Button.inline("🤖 اخبار هوش مصنوعی", b"news_ai")],
        [Button.inline("🔒 اخبار امنیت سایبری", b"news_security")],
    ]

    await bot.send_message(
        chat_id,
        "📰 لطفاً دسته مورد نظر خود را انتخاب کنید:",
        buttons=buttons,
    )


# ============ تابع اصلی برای چک کردن پیام‌های جدید ============


async def check_new_commands():
    """
    هر بار که این تابع اجرا میشه، پیام‌های جدید از چت شخصی رو چک می‌کنه
    و به دستورات /start و /todaynews پاسخ میده.
    """
    # ساخت client با session string
    bot = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)

    print("🔍 در حال چک کردن پیام‌های جدید...")

    state = load_state()
    last_update_id = state.get("last_update_id", 0)

    # ============ هندلر برای کلیک روی دکمه‌ها ============
    @bot.on(events.CallbackQuery)
    async def handle_callback(event):
        data = event.data.decode("utf-8")
        user_id = event.sender_id

        if data == "news_ai":
            category = "ai"
            category_name = "🤖 هوش مصنوعی"
        elif data == "news_security":
            category = "security"
            category_name = "🔒 امنیت سایبری"
        else:
            return

        await event.answer()  # پاسخ به callback

        # ارسال پیام "در حال پردازش"
        processing_msg = await bot.send_message(
            MY_CHAT_ID,
            f"⏳ در حال بررسی کانال‌های {category_name}...\nلطفاً چند لحظه صبر کنید.",
        )

        try:
            # اجرای digest
            picks_count = await run_digest(
                MY_CHAT_ID,
                hours=HOURS_WINDOW,
                include_date_header=True,
                category=category,
            )

            # حذف پیام "در حال پردازش"
            await bot.delete_messages(MY_CHAT_ID, processing_msg.id)

            print(f"✅ {picks_count} خبر {category_name} برای کاربر {user_id} ارسال شد.")

            update_user_interaction(user_id)

        except Exception as e:
            print(f"❌ خطا در اجرای digest: {e}")
            await bot.edit_message(
                MY_CHAT_ID,
                processing_msg.id,
                "⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد.\n"
                "لطفاً دوباره تلاش کنید.",
            )

    try:
        # دریافت آخرین پیام‌ها
        messages = await bot.get_messages(MY_CHAT_ID, limit=10)

        # مرتب‌سازی از قدیمی به جدید
        messages = list(reversed(messages))

        new_last_id = last_update_id

        for msg in messages:
            # اگر پیام قبلاً پردازش شده، رد کن
            if msg.id <= last_update_id:
                continue

            # آپدیت آخرین ID
            if msg.id > new_last_id:
                new_last_id = msg.id

            # فقط پیام‌های متنی که از کاربر هستن
            if not msg.text or not msg.out:
                continue

            text = msg.text.strip()
            user_id = msg.sender_id or (msg.from_id.user_id if msg.from_id else None)

            if not user_id:
                continue

            # پردازش دستور /start
            if text == "/start":
                print(f"📩 دستور /start از کاربر {user_id}")

                if is_first_time_user(user_id):
                    # کاربر جدید - پیام خوش‌آمدگویی کامل
                    welcome_message = (
                        "🔷 به **TeleBrief** خوش آمدید!\n\n"
                        "TeleBrief یک دستیار هوشمند برای دریافت خلاصه و تحلیل اخبار است.\n\n"
                        "**دستورات موجود:**\n"
                        "• `/todaynews` - دریافت اخبار ۱۲ ساعت گذشته\n\n"
                        "🤖 من به‌صورت خودکار کانال‌های معتبر را بررسی می‌کنم و مهم‌ترین اخبار را برای شما انتخاب و خلاصه می‌کنم.\n\n"
                        "**دسته‌بندی اخبار:**\n"
                        "• 🤖 هوش مصنوعی\n"
                        "• 🔒 امنیت سایبری\n\n"
                        "[𝐉𝐎𝐈𝐍](https://t.me/telebriefdata_bot) ➣ telebriefdata_bot"
                    )
                    await bot.send_message(
                        MY_CHAT_ID, welcome_message, parse_mode="md", link_preview=False
                    )
                    mark_user_as_seen(user_id)
                else:
                    # کاربر قبلی - پیام کوتاه
                    await bot.send_message(
                        MY_CHAT_ID,
                        "👋 خوش برگشتید!\n\n"
                        "برای دریافت آخرین اخبار دستور `/todaynews` را ارسال کنید.",
                        parse_mode="md",
                    )

                update_user_interaction(user_id)

            # پردازش دستور /todaynews
            elif text == "/todaynews":
                print(f"📰 دستور /todaynews از کاربر {user_id}")

                # ارسال منوی انتخاب دسته
                await send_category_menu(bot, MY_CHAT_ID)

                update_user_interaction(user_id)

            # پردازش دستور /help
            elif text == "/help":
                print(f"❓ دستور /help از کاربر {user_id}")

                help_text = (
                    "📖 **راهنمای استفاده از TeleBrief**\n\n"
                    "**دستورات:**\n"
                    "• `/start` - شروع به کار با ربات\n"
                    "• `/todaynews` - دریافت اخبار ۱۲ ساعت گذشته\n"
                    "• `/help` - نمایش این راهنما\n\n"
                    "**نحوه کار:**\n"
                    "هنگامی که دستور `/todaynews` را می‌فرستید:\n"
                    "1️⃣ دسته مورد نظر (AI یا Security) را انتخاب می‌کنید\n"
                    "2️⃣ ربات کانال‌های معتبر را بررسی می‌کند\n"
                    "3️⃣ پیام‌های ۱۲ ساعت گذشته را جمع‌آوری می‌کند\n"
                    "4️⃣ با هوش مصنوعی، مهم‌ترین اخبار را انتخاب می‌کند\n"
                    "5️⃣ خلاصه هر خبر به همراه لینک مستقیم برای شما ارسال می‌شود\n"
                    "6️⃣ اگر خبر خاصی نبود، خلاصه کلی از محتوای روز را ارائه می‌دهد\n\n"
                    "[𝐉𝐎𝐈𝐍](https://t.me/telebriefdata_bot) ➣ telebriefdata_bot"
                )

                await bot.send_message(
                    MY_CHAT_ID, help_text, parse_mode="md", link_preview=False
                )
                update_user_interaction(user_id)

        # صبر کوتاه برای پردازش callback‌ها
        await asyncio.sleep(3)

        # ذخیره آخرین ID پردازش شده
        if new_last_id > last_update_id:
            state["last_update_id"] = new_last_id
            save_state(state)
            print(f"💾 وضعیت ذخیره شد. آخرین ID: {new_last_id}")

    except Exception as e:
        print(f"❌ خطا در چک کردن پیام‌ها: {e}")

    finally:
        await bot.disconnect()


# ============ نقطه ورود ============


async def main():
    """
    این تابع یکبار اجرا میشه و پیام‌های جدید رو چک می‌کنه.
    GitHub Actions هر 5 دقیقه این رو اجرا می‌کنه.
    """
    await check_new_commands()


if __name__ == "__main__":
    asyncio.run(main())
