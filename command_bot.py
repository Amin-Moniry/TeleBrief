import os
import json
import asyncio
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from digest_core import run_digest, BOT_TOKEN, HOURS_WINDOW


# ============ مدیریت وضعیت کاربران ============

STATE_FILE = "bot_state.json"


def load_state():
    """بارگذاری وضعیت کاربران از فایل"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"خطا در خواندن state file: {e}")
            return {"users": {}}
    return {"users": {}}


def save_state(state):
    """ذخیره وضعیت کاربران در فایل"""
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
        "last_interaction": datetime.now().isoformat()
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
            "last_interaction": datetime.now().isoformat()
        }

    save_state(state)


# ============ هندلرهای دستورات ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /start - فقط برای کاربران جدید پیام خوش‌آمدگویی می‌فرستد"""
    user_id = update.effective_user.id

    # فقط اگر کاربر برای اولین بار است، پیام خوش‌آمدگویی بفرست
    if is_first_time_user(user_id):
        welcome_message = (
            "🔷 به **TeleBrief** خوش آمدید!\n\n"
            "TeleBrief یک دستیار هوشمند برای دریافت خلاصه و تحلیل اخبار امنیت سایبری است.\n\n"
            "**دستورات موجود:**\n"
            "• `/todaynews` - دریافت خلاصه اخبار ۱۲ ساعت گذشته\n\n"
            "🤖 من به‌صورت خودکار کانال‌های معتبر امنیت سایبری را بررسی می‌کنم و مهم‌ترین اخبار را برای شما انتخاب و خلاصه می‌کنم.\n\n"
            "[𝐉𝐎𝐈𝐍](https://t.me/telebriefdata_bot) ➣ telebriefdata_bot"
        )
        await update.message.reply_text(welcome_message, parse_mode="Markdown", disable_web_page_preview=True)
        mark_user_as_seen(user_id)
    else:
        # کاربر قبلاً دیده شده، پیام ساده‌تر
        await update.message.reply_text(
            "👋 خوش برگشتید!\n\n"
            "برای دریافت آخرین اخبار دستور `/todaynews` را ارسال کنید.",
            parse_mode="Markdown"
        )

    update_user_interaction(user_id)


async def todaynews_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /todaynews - دریافت و ارسال خلاصه اخبار"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # اطلاع‌رسانی به کاربر که در حال پردازش است
    processing_msg = await update.message.reply_text(
        "⏳ در حال بررسی کانال‌ها و جمع‌آوری اخبار مهم...\nلطفاً چند لحظه صبر کنید."
    )

    try:
        # به‌روزرسانی تعامل کاربر
        update_user_interaction(user_id)

        # اجرای digest و دریافت تعداد پیام‌های یافت شده
        picks_count = await run_digest(chat_id, hours=HOURS_WINDOW, include_date_header=True)

        # حذف پیام "در حال پردازش"
        await processing_msg.delete()

        print(f"✅ دستور /todaynews برای کاربر {user_id} انجام شد. {picks_count} خبر ارسال شد.")

    except Exception as e:
        print(f"❌ خطا در اجرای /todaynews برای کاربر {user_id}: {e}")
        await processing_msg.edit_text(
            "⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد.\n"
            "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /help - راهنمای استفاده"""
    user_id = update.effective_user.id

    help_text = (
        "📖 **راهنمای استفاده از TeleBrief**\n\n"
        "**دستورات:**\n"
        "• `/start` - شروع به کار با ربات\n"
        "• `/todaynews` - دریافت خلاصه اخبار ۱۲ ساعت گذشته\n"
        "• `/help` - نمایش این راهنما\n\n"
        "**نحوه کار:**\n"
        "هنگامی که دستور `/todaynews` را می‌فرستید، ربات:\n"
        "1️⃣ کانال‌های معتبر امنیت سایبری را بررسی می‌کند\n"
        "2️⃣ پیام‌های ۱۲ ساعت گذشته را جمع‌آوری می‌کند\n"
        "3️⃣ با استفاده از هوش مصنوعی، مهم‌ترین اخبار را انتخاب می‌کند\n"
        "4️⃣ خلاصه‌ای از هر خبر به همراه لینک مستقیم برای شما ارسال می‌کند\n\n"
        "[𝐉𝐎𝐈𝐍](https://t.me/telebriefdata_bot) ➣ telebriefdata_bot"
    )

    await update.message.reply_text(help_text, parse_mode="Markdown", disable_web_page_preview=True)
    update_user_interaction(user_id)


# ============ راه‌اندازی ربات ============

def main():
    """راه‌اندازی و اجرای ربات"""
    if not BOT_TOKEN:
        print("❌ خطا: BOT_TOKEN تنظیم نشده است!")
        return

    print("🚀 در حال راه‌اندازی ربات TeleBrief...")

    # ایجاد Application
    application = Application.builder().token(BOT_TOKEN).build()

    # افزودن هندلرهای دستورات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("todaynews", todaynews_command))
    application.add_handler(CommandHandler("help", help_command))

    print("✅ ربات آماده است و منتظر دستورات...")

    # شروع polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
