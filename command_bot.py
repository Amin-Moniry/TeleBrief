import os
import json
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from digest_core import (
    run_digest,
    BOT_TOKEN,
    HOURS_WINDOW,
)

print("DEBUG len(BOT_TOKEN):", len(BOT_TOKEN))

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
            return {"users": {}}
    return {"users": {}}


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


# ============ ساخت دکمه‌های منو ============


def get_main_menu_keyboard():
    """دکمه‌های منوی اصلی"""
    keyboard = [
        [
            InlineKeyboardButton("🤖 اخبار هوش مصنوعی", callback_data="news_ai"),
            InlineKeyboardButton("🔒 اخبار امنیت سایبری", callback_data="news_security"),
        ],
        [
            InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard():
    """دکمه بازگشت به منو"""
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)


# ============ هندلرهای دستورات ============


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /start"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    print(f"📩 دستور /start از کاربر {user_id} ({user_name})")

    if is_first_time_user(user_id):
        # کاربر جدید - پیام خوش‌آمدگویی کامل
        welcome_message = (
            f"🔷 سلام {user_name}! به **TeleBrief** خوش آمدید!\n\n"
            "TeleBrief یک دستیار هوشمند برای دریافت خلاصه و تحلیل اخبار است.\n\n"
            "🤖 من به‌صورت خودکار کانال‌های معتبر را بررسی می‌کنم و مهم‌ترین اخبار را برای شما انتخاب و خلاصه می‌کنم.\n\n"
            "**📚 دو دسته خبری:**\n"
            "• 🤖 هوش مصنوعی - 10 کانال تخصصی\n"
            "• 🔒 امنیت سایبری - 6 کانال معتبر\n\n"
            "📊 همراه با تعداد پیام‌های بررسی شده، خلاصه هوشمند، و لینک مستقیم\n\n"
            "👇 دسته مورد نظر خود را انتخاب کنید:"
        )
        mark_user_as_seen(user_id)
    else:
        # کاربر قبلی - پیام کوتاه
        welcome_message = (
            f"👋 سلام {user_name}! خوش برگشتید!\n\n"
            "👇 دسته مورد نظر خود را انتخاب کنید:"
        )

    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown",
    )

    update_user_interaction(user_id)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /menu - نمایش منوی اصلی"""
    user_name = update.effective_user.first_name

    await update.message.reply_text(
        f"📰 سلام {user_name}!\n\n👇 دسته مورد نظر خود را انتخاب کنید:",
        reply_markup=get_main_menu_keyboard(),
    )


# ============ هندلر دکمه‌ها (Callback Query) ============


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر کلیک روی دکمه‌ها"""
    query = update.callback_query
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    data = query.data

    await query.answer()  # تایید دریافت callback

    print(f"🔘 دکمه '{data}' توسط کاربر {user_id} ({user_name}) کلیک شد")

    # بازگشت به منوی اصلی
    if data == "main_menu":
        await query.edit_message_text(
            f"📰 سلام {user_name}!\n\n👇 دسته مورد نظر خود را انتخاب کنید:",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # نمایش راهنما
    if data == "help":
        help_text = (
            "📖 **راهنمای استفاده از TeleBrief**\n\n"
            "**نحوه کار:**\n"
            "1️⃣ دسته مورد نظر (AI یا Security) را انتخاب کنید\n"
            "2️⃣ ربات کانال‌های معتبر را بررسی می‌کند\n"
            "3️⃣ پیام‌های 12 ساعت گذشته را جمع‌آوری می‌کند\n"
            "4️⃣ با هوش مصنوعی، مهم‌ترین اخبار را انتخاب می‌کند\n"
            "5️⃣ خلاصه هر خبر به همراه لینک مستقیم ارسال می‌شود\n"
            "6️⃣ اگر خبر خاصی نبود، خلاصه کلی محتوای روز ارائه می‌شود\n\n"
            "**کانال‌های بررسی شده:**\n"
            "🤖 AI: 10 کانال (digiai, RoidBest, Farda_Ai و...)\n"
            "🔒 Security: 6 کانال (thehackernews, cibsecurity و...)\n\n"
            "**دستورات:**\n"
            "• /start - نمایش منوی اصلی\n"
            "• /menu - نمایش منوی اصلی\n"
            "• /help - نمایش این راهنما"
        )

        await query.edit_message_text(
            help_text,
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="Markdown",
        )
        return

    # دریافت اخبار AI
    if data == "news_ai":
        category = "ai"
        category_name = "🤖 هوش مصنوعی"
        emoji = "🤖"

    # دریافت اخبار Security
    elif data == "news_security":
        category = "security"
        category_name = "🔒 امنیت سایبری"
        emoji = "🔒"

    else:
        return

    # ویرایش پیام به حالت "در حال پردازش"
    processing_msg = await query.edit_message_text(
        f"⏳ در حال بررسی کانال‌های {category_name}...\n\n"
        f"🔍 در حال جستجو در صدها پیام...\n"
        f"🤖 تحلیل هوشمند اخبار...\n\n"
        f"⏱️ لطفاً چند لحظه صبر کنید..."
    )

    try:
        # اجرای digest
        chat_id = query.message.chat_id
        picks_count = await run_digest(
            chat_id, hours=HOURS_WINDOW, include_date_header=True, category=category
        )

        # ارسال پیام موفقیت با دکمه بازگشت
        await context.bot.send_message(
            chat_id,
            f"✅ {picks_count} خبر {category_name} با موفقیت ارسال شد!\n\n"
            f"👇 برای دریافت اخبار دسته دیگر، به منو برگردید:",
            reply_markup=get_back_to_menu_keyboard(),
        )

        # حذف پیام "در حال پردازش"
        await processing_msg.delete()

        print(f"✅ {picks_count} خبر {category} برای کاربر {user_id} ارسال شد.")
        update_user_interaction(user_id)

    except Exception as e:
        print(f"❌ خطا در اجرای digest برای {category}: {e}")

        # ویرایش پیام به حالت خطا
        await processing_msg.edit_text(
            f"⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد.\n\n"
            f"لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.\n\n"
            f"خطا: {str(e)[:100]}",
            reply_markup=get_back_to_menu_keyboard(),
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /help"""
    help_text = (
        "📖 **راهنمای استفاده از TeleBrief**\n\n"
        "**نحوه کار:**\n"
        "1️⃣ دسته مورد نظر (AI یا Security) را انتخاب کنید\n"
        "2️⃣ ربات کانال‌های معتبر را بررسی می‌کند\n"
        "3️⃣ پیام‌های 12 ساعت گذشته را جمع‌آوری می‌کند\n"
        "4️⃣ با هوش مصنوعی، مهم‌ترین اخبار را انتخاب می‌کند\n"
        "5️⃣ خلاصه هر خبر به همراه لینک مستقیم ارسال می‌شود\n"
        "6️⃣ اگر خبر خاصی نبود، خلاصه کلی محتوای روز ارائه می‌شود\n\n"
        "**کانال‌های بررسی شده:**\n"
        "🤖 AI: 10 کانال تخصصی\n"
        "🔒 Security: 6 کانال معتبر\n\n"
        "**دستورات:**\n"
        "• /start - نمایش منوی اصلی\n"
        "• /menu - نمایش منوی اصلی\n"
        "• /help - نمایش این راهنما"
    )

    await update.message.reply_text(
        help_text, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown"
    )


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
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))

    # افزودن هندلر دکمه‌ها
    application.add_handler(CallbackQueryHandler(button_callback))

    print("✅ ربات آماده است و منتظر دستورات...")

    # شروع polling (24/7)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
