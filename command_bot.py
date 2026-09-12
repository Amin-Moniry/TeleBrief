import asyncio
import html
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from digest_core import BOT_TOKEN, HOURS_WINDOW, run_digest

APP_NAME = "TeleBrief"
STATE_FILE = Path("bot_state.json")
logger = logging.getLogger(__name__)
user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"users": {}}
    try:
        import json
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.exception("خواندن فایل وضعیت ناموفق بود")
        return {"users": {}}


def save_state(state: dict) -> None:
    """ذخیره اتمیک برای جلوگیری از خراب‌شدن فایل وضعیت."""
    import json
    temp_file = STATE_FILE.with_suffix(".tmp")
    try:
        temp_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temp_file.replace(STATE_FILE)
    except OSError:
        logger.exception("ذخیره فایل وضعیت ناموفق بود")


def touch_user(user_id: int) -> bool:
    state = load_state()
    users = state.setdefault("users", {})
    key = str(user_id)
    is_new = key not in users
    now = datetime.now().isoformat(timespec="seconds")
    users.setdefault(key, {"first_seen": now})["last_interaction"] = now
    save_state(state)
    return is_new


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 هوش مصنوعی", callback_data="digest:ai"),
            InlineKeyboardButton("🛡 امنیت سایبری", callback_data="digest:security"),
        ],
        [
            InlineKeyboardButton("📖 راهنما", callback_data="page:help"),
            InlineKeyboardButton("ℹ️ درباره ربات", callback_data="page:about"),
        ],
    ])


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="page:menu")]
    ])


def welcome_text(first_name: str, is_new: bool) -> str:
    name = html.escape(first_name or "دوست عزیز")
    greeting = "خوش اومدی" if is_new else "خوش برگشتی"
    return (
        f"👋 <b>سلام {name}، {greeting}!</b>\n\n"
        f"من <b>{APP_NAME}</b> هستم: پیام‌های کانال‌های معتبر را عمیق بررسی می‌کنم، "
        "خبرهای تکراری و تبلیغاتی را کنار می‌گذارم و فقط مهم‌ترین موارد را با منبع مستقیم تحویلت می‌دهم.\n\n"
        f"<blockquote>بازه فعلی گزارش: {HOURS_WINDOW} ساعت اخیر\n"
        "خروجی: خلاصه فارسی، دلیل اهمیت، نکات کلیدی و لینک منبع</blockquote>\n\n"
        "یکی از دسته‌ها را انتخاب کن 👇"
    )


HELP_TEXT = (
    "📖 <b>راهنمای TeleBrief</b>\n\n"
    "یک دسته را انتخاب کن. ربات همه پیام‌های بازه زمانی را می‌خواند، موارد کم‌ارزش را حذف می‌کند، "
    "خبرهای مشابه را ادغام می‌کند و مهم‌ترین نتیجه‌ها را به ترتیب اهمیت می‌فرستد.\n\n"
    "<b>دستورها</b>\n"
    "/start - شروع و نمایش منوی اصلی\n"
    "/menu - بازکردن منو\n"
    "/help - راهنمای استفاده\n"
    "/about - معرفی ربات\n\n"
    "<blockquote>برای هر خبر، روی «مشاهده پیام اصلی» بزن تا مستقیماً به منبع تلگرام بروی.</blockquote>"
)

ABOUT_TEXT = (
    "ℹ️ <b>درباره TeleBrief</b>\n\n"
    "یک خبرخوان تحلیلی فارسی برای حوزه‌های <b>هوش مصنوعی</b> و <b>امنیت سایبری</b>. "
    "هدفش زیادکردن تعداد پیام‌ها نیست؛ هدفش پیدا کردن چیزهایی است که واقعاً ارزش خواندن دارند.\n\n"
    "<blockquote>کمتر اسکرول کن، بهتر باخبر شو.</blockquote>"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    is_new = touch_user(user.id)
    await update.effective_message.reply_text(
        welcome_text(user.first_name, is_new),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
        disable_web_page_preview=True,
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_user(update.effective_user.id)
    await update.effective_message.reply_text(
        "🗞 <b>چه گزارشی می‌خوای؟</b>\n\nدسته موردنظرت را انتخاب کن:",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        ABOUT_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""
    user = query.from_user
    touch_user(user.id)

    if data in {"digest:ai", "digest:security"} and user_locks[user.id].locked():
        await query.answer("گزارش قبلی هنوز در حال آماده‌شدن است.", show_alert=True)
        return
    await query.answer()

    if data == "page:menu":
        await query.edit_message_text(
            "🗞 <b>چه گزارشی می‌خوای؟</b>\n\nدسته موردنظرت را انتخاب کن:",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(),
        )
        return
    if data == "page:help":
        await query.edit_message_text(
            HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
        )
        return
    if data == "page:about":
        await query.edit_message_text(
            ABOUT_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
        )
        return
    if data not in {"digest:ai", "digest:security"}:
        return

    category = data.split(":", 1)[1]
    category_name = "هوش مصنوعی" if category == "ai" else "امنیت سایبری"
    lock = user_locks[user.id]
    async with lock:
        progress_message = await query.edit_message_text(
            f"🔎 <b>جست‌وجوی عمیق {category_name}</b>\n\n"
            "در حال خواندن پیام‌ها، حذف تبلیغات، تشخیص خبرهای تکراری و رتبه‌بندی موارد مهم...\n\n"
            "<blockquote expandable>این مرحله ممکنه کمی طول بکشه؛ چون خروجی سریع ولی سطحی نمی‌خوایم.</blockquote>",
            parse_mode=ParseMode.HTML,
        )
        try:
            count = await run_digest(
                chat_id=query.message.chat_id,
                hours=HOURS_WINDOW,
                include_date_header=True,
                category=category,
            )
            await progress_message.edit_text(
                f"✅ <b>گزارش آماده شد</b>\n\n{count} خبر مهم از حوزه {category_name} پیدا و ارسال شد.",
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard(),
            )
        except Exception:
            logger.exception("ساخت گزارش برای کاربر %s ناموفق بود", user.id)
            await progress_message.edit_text(
                "⚠️ <b>ساخت گزارش کامل نشد</b>\n\n"
                "ارتباط با یکی از سرویس‌ها مشکل داشت. چند دقیقه دیگه دوباره امتحان کن.",
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard(),
            )


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("start", "شروع و نمایش منوی اصلی"),
        BotCommand("menu", "انتخاب دسته خبری"),
        BotCommand("help", "راهنمای استفاده"),
        BotCommand("about", "معرفی TeleBrief"),
    ])


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("خطای کنترل‌نشده در ربات", exc_info=context.error)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    if not BOT_TOKEN:
        raise RuntimeError("متغیر محیطی BOT_TOKEN تنظیم نشده است.")

    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)
    logger.info("%s آماده است", APP_NAME)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
