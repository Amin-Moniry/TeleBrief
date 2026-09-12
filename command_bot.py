import asyncio
import html
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    MessageHandler, filters,
)

from digest_core import (
    AI_CHANNELS, SECURITY_CHANNELS, BOT_TOKEN, HOURS_WINDOW,
    format_date_header, format_story, prepare_digest,
)

APP_NAME = "TeleBrief"
STATE_FILE = Path("bot_state.json")
logger = logging.getLogger(__name__)
user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
PAGE_SIZE = 10
SUPPORTED_LANGUAGES = {"fa": "فارسی", "en": "English"}


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


def user_prefs(user_id: int) -> dict:
    state = load_state()
    entry = state.setdefault("users", {}).setdefault(str(user_id), {})
    entry.setdefault("language", "fa")
    entry.setdefault("extra_channels", [])
    return entry


def update_user_prefs(user_id: int, **changes) -> dict:
    state = load_state()
    entry = state.setdefault("users", {}).setdefault(str(user_id), {})
    entry.update(changes)
    save_state(state)
    return entry


def safe_channel(value: str) -> str | None:
    value = value.strip().replace("https://t.me/", "").replace("http://t.me/", "")
    value = value.split("/", 1)[0].strip().lstrip("@").strip()
    if not value or len(value) > 64 or not value.replace("_", "").isalnum():
        return None
    return value


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang:fa"), InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")], [InlineKeyboardButton("🏠 منوی اصلی", callback_data="page:menu")]])


def channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("➕ افزودن کانال / Add channel", callback_data="channel:add")], [InlineKeyboardButton("🏠 منوی اصلی", callback_data="page:menu")]])


def main_menu_keyboard(lang: str = "fa") -> InlineKeyboardMarkup:
    if lang == "en":
        rows = [[InlineKeyboardButton("🤖 AI Intelligence", callback_data="digest:ai"), InlineKeyboardButton("🛡 Cyber Security", callback_data="digest:security")], [InlineKeyboardButton("📚 My Channels", callback_data="page:channels"), InlineKeyboardButton("🌐 Language", callback_data="page:language")], [InlineKeyboardButton("📖 Help", callback_data="page:help"), InlineKeyboardButton("ℹ️ About", callback_data="page:about")]]
    else:
        rows = [[InlineKeyboardButton("🤖 هوش مصنوعی", callback_data="digest:ai"), InlineKeyboardButton("🛡 امنیت سایبری", callback_data="digest:security")], [InlineKeyboardButton("📚 کانال‌های من", callback_data="page:channels"), InlineKeyboardButton("🌐 زبان / Language", callback_data="page:language")], [InlineKeyboardButton("📖 راهنما", callback_data="page:help"), InlineKeyboardButton("ℹ️ درباره ربات", callback_data="page:about")]]
    return InlineKeyboardMarkup(rows)



def hours_keyboard(category: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("۶ ساعت", callback_data=f"hours:{category}:6"),
            InlineKeyboardButton("۱۲ ساعت", callback_data=f"hours:{category}:12"),
        ],
        [
            InlineKeyboardButton("۲۴ ساعت", callback_data=f"hours:{category}:24"),
            InlineKeyboardButton("۴۸ ساعت", callback_data=f"hours:{category}:48"),
        ],
        [InlineKeyboardButton("✍️ واردکردن ساعت دلخواه", callback_data=f"custom:{category}")],
        [InlineKeyboardButton("🏠 بازگشت", callback_data="page:menu")],
    ])


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="page:menu")]
    ])


def welcome_text(first_name: str, is_new: bool, lang: str = "fa") -> str:
    name = html.escape(first_name or ("friend" if lang == "en" else "دوست عزیز"))
    if lang == "en":
        return f"👋 <b>Hello {name}!</b>\n\nI am <b>{APP_NAME}</b>, your AI news intelligence bot. I scan configured channels, remove noise and send ranked stories with direct sources.\n\n<blockquote>Default window: {HOURS_WINDOW} hours</blockquote>\n\nChoose a briefing:"

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
    "یک دسته و بازه زمانی را انتخاب کن. ربات همه پیام‌های بازه را می‌خواند، موارد کم‌ارزش را حذف می‌کند، "
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
    lang = user_prefs(user.id).get("language", "fa")
    await update.effective_message.reply_text(
        welcome_text(user.first_name, is_new, lang),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(lang),
        disable_web_page_preview=True,
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_user(update.effective_user.id)
    lang = user_prefs(update.effective_user.id).get("language", "fa")
    text = "🗞 <b>Choose your briefing</b>" if lang == "en" else "🗞 <b>چه گزارشی می‌خوای؟</b>\n\nدسته موردنظرت را انتخاب کن:"
    await update.effective_message.reply_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(lang),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        ABOUT_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
    )



def more_keyboard(remaining: int) -> InlineKeyboardMarkup:
    rows = []
    if remaining > 0:
        rows.append([
            InlineKeyboardButton(
                f"مشاهده ۱۰ خبر بعدی ({remaining} باقی‌مانده) ⬇️",
                callback_data="digest:more",
            )
        ])
    rows.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="page:menu")])
    return InlineKeyboardMarkup(rows)


async def send_story_page(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    cache: dict,
) -> tuple[int, int]:
    stories = cache["stories"]
    start = cache.get("offset", 0)
    end = min(start + PAGE_SIZE, len(stories))
    for rank, story in enumerate(stories[start:end], start=start + 1):
        await context.bot.send_message(
            chat_id=chat_id,
            text=format_story(story, rank, cache["category"]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        await asyncio.sleep(0.35)
    cache["offset"] = end
    return end - start, len(stories) - end


LOADING_FRAMES = ("⣾", "⣽", "⣻", "⢿")
LOADING_STAGES = (
    "در حال اتصال به کانال‌های منتخب",
    "در حال جمع‌آوری پیام‌های بازه زمانی",
    "در حال حذف تبلیغات و پیام‌های تکراری",
    "در حال خواندن عمیق محتوای پیام‌ها",
    "در حال مقایسه و ادغام خبرهای مشابه",
    "در حال رتبه‌بندی مهم‌ترین خبرها",
)


async def animate_loading(status_message, category_name: str, hours: int) -> None:
    """پیام وضعیت را بدون شلوغ‌کردن چت، زنده و متحرک نگه می‌دارد."""
    frame_index = 0
    stage_index = 0
    try:
        while True:
            frame = LOADING_FRAMES[frame_index % len(LOADING_FRAMES)]
            stage = LOADING_STAGES[stage_index % len(LOADING_STAGES)]
            await status_message.edit_text(
                f"{frame} <b>هوش مصنوعی در حال بررسی {category_name} است...</b>\n\n"
                f"{stage}\n"
                f"<blockquote expandable>بازه انتخاب‌شده: {hours} ساعت اخیر\n"
                "هنوز در حال جست‌وجو بین منابع هستم؛ خروجی که ارزش خواندن داشته باشد می‌فرستم.</blockquote>",
                parse_mode=ParseMode.HTML,
            )
            frame_index += 1
            if frame_index % 3 == 0:
                stage_index += 1
            await asyncio.sleep(2.2)
    except asyncio.CancelledError:
        return
    except Exception:
        logger.debug("به‌روزرسانی انیمیشن وضعیت متوقف شد", exc_info=True)


async def build_and_send_report(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
    category: str,
    hours: int,
    status_message,
) -> None:
    category_name = "هوش مصنوعی" if category == "ai" else "امنیت سایبری"
    lock = user_locks[user_id]
    async with lock:
        loading_task = asyncio.create_task(
            animate_loading(status_message, category_name, hours)
        )
        await asyncio.sleep(0.05)
        await status_message.edit_text(
            f"🔎 <b>جست‌وجوی عمیق {category_name}</b>\n\n"
            f"در حال خواندن تمام کانال‌ها و تحلیل پیام‌های {hours} ساعت اخیر...\n\n"
            "<blockquote expandable>تبلیغات حذف، خبرهای مشابه ادغام و همه موارد مهم رتبه‌بندی می‌شوند.</blockquote>",
            parse_mode=ParseMode.HTML,
        )
        try:
            extra_channels = user_prefs(user_id).get("extra_channels", [])
            result = await prepare_digest(hours=hours, category=category, extra_channels=extra_channels)
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            stories = result["stories"]
            cache = {"stories": stories, "category": category, "offset": 0}
            context.user_data["digest_cache"] = cache
            await status_message.edit_text(
                format_date_header(hours, result["total_messages"], result["active_channels"])
                + f"\n\n<b>وضعیت کانال‌ها:</b> هر {result['configured_channels']} کانال پیمایش شد؛ "
                + f"{result['active_channels']} کانال در این بازه پیام داشت.",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            if not stories:
                context.user_data.pop("digest_cache", None)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🔍 <b>خبر مهمی پیدا نشد</b>\n\nتمام پیام‌های این بازه بررسی شدند.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=back_keyboard(),
                )
                return
            sent, remaining = await send_story_page(context, chat_id, cache)
            await context.bot.send_message(
                chat_id=chat_id,
                text=(f"✅ <b>{sent} خبر اول، جداگانه ارسال شد</b>\n\n"
                      + (f"هنوز {remaining} خبر مهم باقی مانده." if remaining else "همه خبرهای مهم ارسال شدند.")),
                parse_mode=ParseMode.HTML,
                reply_markup=more_keyboard(remaining),
            )
            if not remaining:
                context.user_data.pop("digest_cache", None)
        except Exception:
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            logger.exception("ساخت گزارش برای کاربر %s ناموفق بود", user_id)
            await status_message.edit_text(
                "⚠️ <b>ساخت گزارش کامل نشد</b>\n\nچند دقیقه دیگر دوباره امتحان کن.",
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard(),
            )


async def custom_hours_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    category = context.user_data.get("awaiting_hours")
    if not category:
        return
    raw = (update.effective_message.text or "").strip()
    try:
        hours = int(raw.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")))
    except ValueError:
        await update.effective_message.reply_text("فقط یک عدد بفرست؛ مثلاً <b>۲۴</b>.", parse_mode=ParseMode.HTML)
        return
    if not 1 <= hours <= 168:
        await update.effective_message.reply_text("بازه باید بین <b>۱ تا ۱۶۸ ساعت</b> باشد.", parse_mode=ParseMode.HTML)
        return
    if user_locks[update.effective_user.id].locked():
        await update.effective_message.reply_text("گزارش قبلی هنوز آماده نشده.")
        return
    context.user_data.pop("awaiting_hours", None)
    status = await update.effective_message.reply_text("⏳ <b>در حال شروع بررسی...</b>", parse_mode=ParseMode.HTML)
    await build_and_send_report(
        context, update.effective_chat.id, update.effective_user.id,
        category, hours, status,
    )


async def add_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("awaiting_channel"):
        return
    channel = safe_channel(update.effective_message.text or "")
    if not channel:
        await update.effective_message.reply_text("فرمت درست نیست. @channel یا لینک عمومی t.me/channel را بفرست.")
        return
    prefs = user_prefs(update.effective_user.id)
    channels = list(dict.fromkeys(prefs.get("extra_channels", []) + [channel]))[:30]
    update_user_prefs(update.effective_user.id, extra_channels=channels)
    context.user_data.pop("awaiting_channel", None)
    await update.effective_message.reply_text(f"✅ کانال @{html.escape(channel)} اضافه شد.", parse_mode=ParseMode.HTML, reply_markup=channels_keyboard())


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""
    user = query.from_user
    touch_user(user.id)

    if data.startswith("hours:") and user_locks[user.id].locked():
        await query.answer("گزارش قبلی هنوز در حال آماده‌شدن است.", show_alert=True)
        return
    await query.answer()

    if data == "page:menu":
        lang = user_prefs(user.id).get("language", "fa")
        text = "🗞 <b>Choose your briefing</b>" if lang == "en" else "🗞 <b>چه گزارشی می‌خوای؟</b>\n\nدسته موردنظرت را انتخاب کن:"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=main_menu_keyboard(lang))
        return
    if data == "page:language":
        await query.edit_message_text("🌐 <b>زبان ربات را انتخاب کن</b> / <b>Choose bot language</b>", parse_mode=ParseMode.HTML, reply_markup=language_keyboard())
        return
    if data.startswith("lang:"):
        lang = data.split(":", 1)[1]
        update_user_prefs(user.id, language=lang)
        await query.edit_message_text("✅ <b>زبان روی فارسی تنظیم شد.</b>" if lang == "fa" else "✅ <b>Language set to English.</b>", parse_mode=ParseMode.HTML, reply_markup=main_menu_keyboard(lang))
        return
    if data == "page:channels":
        prefs = user_prefs(user.id)
        channels = prefs.get("extra_channels", [])
        lang = prefs.get("language", "fa")
        heading = "📚 <b>My channels</b>" if lang == "en" else "📚 <b>کانال‌های من</b>"
        listed = "\n".join(f"• @{html.escape(c)}" for c in channels) if channels else ("No personal channels yet." if lang == "en" else "هنوز کانالی اضافه نشده.")
        await query.edit_message_text(heading + "\n\n" + listed, parse_mode=ParseMode.HTML, reply_markup=channels_keyboard())
        return
    if data == "channel:add":
        context.user_data["awaiting_channel"] = True
        await query.edit_message_text("✍️ <b>کانال عمومی را بفرست</b>\n\nمثال: @thehackernews", parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
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
    if data == "digest:more":
        cache = context.user_data.get("digest_cache")
        if not cache:
            await query.edit_message_text(
                "⌛️ <b>این گزارش منقضی شده</b>\n\nاز منو گزارش تازه بگیر.",
                parse_mode=ParseMode.HTML, reply_markup=back_keyboard(),
            )
            return
        await query.edit_message_text("⏳ <b>در حال ارسال ۱۰ خبر بعدی...</b>", parse_mode=ParseMode.HTML)
        sent, remaining = await send_story_page(context, query.message.chat_id, cache)
        await query.edit_message_text(
            (f"📚 <b>{sent} خبر دیگر، جداگانه ارسال شد</b>\n\n"
             + (f"هنوز {remaining} خبر مهم باقی مانده." if remaining else "همه خبرهای مهم این بازه ارسال شدند.")),
            parse_mode=ParseMode.HTML, reply_markup=more_keyboard(remaining),
        )
        if not remaining:
            context.user_data.pop("digest_cache", None)
        return
    if data in {"digest:ai", "digest:security"}:
        category = data.split(":", 1)[1]
        context.user_data.pop("awaiting_hours", None)
        await query.edit_message_text(
            "⏱ <b>چند ساعت اخیر بررسی شود؟</b>\n\n"
            "بازه آماده را انتخاب کن یا عدد دلخواهت را بنویس.",
            parse_mode=ParseMode.HTML,
            reply_markup=hours_keyboard(category),
        )
        return
    if data.startswith("custom:"):
        category = data.split(":", 1)[1]
        context.user_data["awaiting_hours"] = category
        await query.edit_message_text(
            "✍️ <b>ساعت دلخواه را بفرست</b>\n\n"
            "یک عدد بین ۱ تا ۱۶۸ بنویس؛ مثلاً <b>۲۴</b>.",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard(),
        )
        return
    if data.startswith("hours:"):
        _, category, raw_hours = data.split(":", 2)
        if user_locks[user.id].locked():
            await query.answer("گزارش قبلی هنوز در حال آماده‌شدن است.", show_alert=True)
            return
        context.user_data.pop("awaiting_hours", None)
        await build_and_send_report(
            context, query.message.chat_id, user.id,
            category, int(raw_hours), query.message,
        )
        return


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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_message), group=0)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_hours_message), group=1)
    application.add_error_handler(error_handler)
    logger.info("%s آماده است", APP_NAME)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
