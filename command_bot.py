import asyncio
import html
import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from telegram import (
    BotCommand, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup, Update,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    MessageHandler, filters,
)

from digest_core import (
    ADMIN_ID, AI_CHANNELS, SECURITY_CHANNELS, BOT_TOKEN, HOURS_WINDOW,
    CURRENCY_HOURS_WINDOW, format_currency_digest, format_date_header,
    format_story, prepare_currency_digest, prepare_digest,
)

APP_NAME = "TeleBrief"
# DATA_DIR باید به مسیر یک Volume دائمی روی Railway اشاره کند (مثلاً /data)
# در غیر این صورت هر دیپلوی/ری‌استارت باعث پاک‌شدن bot_state.json می‌شود.
DATA_DIR = Path(os.getenv("DATA_DIR", "."))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / "bot_state.json"
logger = logging.getLogger(__name__)
user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
PAGE_SIZE = 10


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


CATEGORY_NAMES = {"ai": "هوش مصنوعی", "security": "امنیت سایبری", "currency": "دلار و طلا"}


def touch_user(user_id: int, user=None) -> bool:
    state = load_state()
    users = state.setdefault("users", {})
    key = str(user_id)
    is_new = key not in users
    now = datetime.now().isoformat(timespec="seconds")
    entry = users.setdefault(key, {"first_seen": now, "total_requests": 0, "requests_by_category": {}})
    entry["last_interaction"] = now
    if user is not None:
        # فقط برای شناسایی راحت‌تر کاربر در آمار ادمین؛ در جای دیگری استفاده نمی‌شود
        entry["first_name"] = user.first_name or entry.get("first_name", "")
        entry["username"] = user.username or entry.get("username", "")
    save_state(state)
    return is_new


def record_request(user_id: int, category: str) -> None:
    """هر بار که کاربر یک گزارش واقعی درخواست می‌کند (AI/امنیت/دلار) صدا زده می‌شود."""
    state = load_state()
    key = str(user_id)
    now = datetime.now().isoformat(timespec="seconds")
    entry = state.setdefault("users", {}).setdefault(
        key, {"first_seen": now, "total_requests": 0, "requests_by_category": {}}
    )
    entry["total_requests"] = entry.get("total_requests", 0) + 1
    by_category = entry.setdefault("requests_by_category", {})
    by_category[category] = by_category.get(category, 0) + 1
    entry["last_interaction"] = now
    save_state(state)


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



def channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("➕ افزودن کانال", callback_data="channel:add")], [InlineKeyboardButton("🏠 منوی اصلی", callback_data="page:menu")]])


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 هوش مصنوعی", callback_data="digest:ai"),
         InlineKeyboardButton("🛡 امنیت سایبری", callback_data="digest:security")],
        [InlineKeyboardButton("💵 دلار و طلا", callback_data="digest:currency")],
        [InlineKeyboardButton("📚 کانال‌های من", callback_data="page:channels"),
         InlineKeyboardButton("📖 راهنما", callback_data="page:help")],
        [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="page:about")],
    ])



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
        [
            InlineKeyboardButton("۷ روز", callback_data=f"hours:{category}:168"),
            InlineKeyboardButton("۱۵ روز / ۳۶۰ ساعت", callback_data=f"hours:{category}:360"),
        ],
        [InlineKeyboardButton("✍️ بازه دلخواه", callback_data=f"custom:{category}")],
        [InlineKeyboardButton("🏠 بازگشت", callback_data="page:menu")],
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
        f"من <b>{APP_NAME}</b> هستم: همه کانال‌های تنظیم‌شده را بررسی می‌کنم، "
        "نویز و خبرهای تکراری را حذف می‌کنم و مهم‌ترین یافته‌ها را با لینک مستقیم می‌فرستم.\n\n"
        f"<blockquote>بازه پیش‌فرض: {HOURS_WINDOW} ساعت\n"
        "خروجی: خلاصه رتبه‌بندی‌شده، نکات کلیدی و منبع مستقیم</blockquote>\n\n"
        "یک گزارش را انتخاب کن:")


HELP_TEXT = (
    "📖 <b>راهنمای TeleBrief</b>\n\n"
    "یک دسته و بازه زمانی را انتخاب کن. ربات همه پیام‌های بازه را می‌خواند، موارد کم‌ارزش را حذف می‌کند، "
    "خبرهای مشابه را ادغام می‌کند و مهم‌ترین نتیجه‌ها را به ترتیب اهمیت می‌فرستد.\n\n"
    "بخش «💵 دلار و طلا» جداست: به‌جای رتبه‌بندی خبر، فقط تازه‌ترین قیمت دلار و طلای ۱۸ عیار را از کانال‌های ارز پیدا می‌کند "
    "و همیشه جدیدترین بروزرسانی بین چند کانال را نشان می‌دهد.\n\n"
    "<b>دستورها</b>\n"
    "/start - شروع و نمایش منوی اصلی\n"
    "/menu - بازکردن منو\n"
    "/price - نرخ لحظه‌ای دلار و طلا\n"
    "/help - راهنمای استفاده\n"
    "/about - معرفی ربات\n\n"
    "<blockquote>برای هر خبر، روی «مشاهده پیام اصلی» بزن تا مستقیماً به منبع تلگرام بروی.</blockquote>"
)

ABOUT_TEXT = (
    "\u200fℹ️ <b>درباره</b> \u200e<b>TeleBrief</b>\u200f\n\n"
    "\u200fیک خبرخوان تحلیلی فارسی برای حوزه‌های <b>هوش مصنوعی</b> و <b>امنیت سایبری</b>. "
    "هدفش زیادکردن تعداد پیام‌ها نیست؛ هدفش پیدا کردن چیزهایی است که واقعاً ارزش خواندن دارند.\n\n"
    "<blockquote>کمتر اسکرول کن، بهتر باخبر شو.</blockquote>"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    is_new = touch_user(user.id, user)
    await update.effective_message.reply_text(
        welcome_text(user.first_name, is_new),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
        disable_web_page_preview=True,
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_user(update.effective_user.id, update.effective_user)
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



def more_keyboard(remaining: int) -> InlineKeyboardMarkup:
    rows = []
    if remaining > 0:
        rows.append([
            InlineKeyboardButton(
                f"مشاهده خبرهای بعدی (۱۰ تا از {remaining} خبر باقی‌مانده) ⬇️",
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


LOADING_STAGES = (
    "اتصال به منابع معتبر",
    "استخراج پیام‌های مهم",
    "حذف تبلیغات و موارد تکراری",
    "رتبه‌بندی نهایی خبرها",
)


async def animate_loading(
    status_message, category_name: str, hours: int, stages: tuple[str, ...] = LOADING_STAGES
) -> None:
    """لودینگ داشبوردی: قاب ثابت، مرحله متغیر، بدون اسپینر."""
    tick = 0
    stage_index = 0
    try:
        while True:
            stage = stages[stage_index % len(stages)]
            completed = "●" * stage_index + "○" * (len(stages) - stage_index)
            try:
                await status_message.edit_text(
                    "🔍 <b>گزارش هوشمند | TeleBrief</b>\n"
                    f"\n<i>بخش: {category_name}</i>\n\n"
                    f"<blockquote>بازه زمانی: {hours} ساعت اخیر\n"
                    f"مرحله فعلی: {stage}\n"
                    f"پیشرفت: {completed}</blockquote>\n\n"
                    "🧠 در حال بررسی دقیق پیام‌ها هستم؛ موارد ارزشمند جدا می‌شوند.",
                    parse_mode=ParseMode.HTML,
                )
            except BadRequest as exc:
                # وقتی متن جدید دقیقاً با متن فعلی یکسان است (بین دو تغییر مرحله)،
                # تلگرام همین خطای بی‌ضرر را می‌دهد؛ نادیده می‌گیریم و لودینگ ادامه پیدا می‌کند.
                if "not modified" not in str(exc).lower():
                    raise
            tick += 1
            if tick % 4 == 0:
                stage_index = (stage_index + 1) % len(stages)
            await asyncio.sleep(0.8)
    except asyncio.CancelledError:
        return
    except Exception:
        logger.debug("spinner stopped", exc_info=True)


async def build_and_send_report(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
    category: str,
    hours: int,
    status_message,
) -> None:
    category_name = "هوش مصنوعی" if category == "ai" else "امنیت سایبری"
    record_request(user_id, category)
    lock = user_locks[user_id]
    async with lock:
        loading_task = asyncio.create_task(
            animate_loading(status_message, category_name, hours)
        )
        try:
            await asyncio.sleep(0.05)
            await status_message.edit_text(
                f"🔎 <b>جست‌وجوی عمیق {category_name}</b>\n\n"
                f"در حال خواندن تمام کانال‌ها و تحلیل پیام‌های {hours} ساعت اخیر...\n"
                f"<blockquote>بازه انتخاب‌شده: {hours} ساعت</blockquote>\n"
                "<blockquote expandable>تبلیغات حذف، خبرهای مشابه ادغام و همه موارد مهم رتبه‌بندی می‌شوند.</blockquote>",
                parse_mode=ParseMode.HTML,
            )
            extra_channels = user_prefs(user_id).get("extra_channels", [])
            result = await prepare_digest(hours=hours, category=category, extra_channels=extra_channels)
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            stories = result["stories"]
            cache = {"stories": stories, "category": category, "offset": 0}
            context.user_data["digest_cache"] = cache
            await status_message.edit_text(
                format_date_header(hours, result["total_messages"], result["active_channels"])
                + f"\n\n<b>وضعیت کانال‌ها:</b> هر {result['configured_channels']} کانال پیمایش شد؛ {result['active_channels']} کانال در این بازه پیام داشت.",
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
                text=(
                    f"✅ <b>{sent} خبر اول از مجموع {sent + remaining} خبر ارسال شد</b>\n\n"
                    + (f"هنوز {remaining} خبر مهم باقی مانده." if remaining else "همه خبرهای مهم ارسال شدند.")
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=more_keyboard(remaining),
            )
            if not remaining:
                context.user_data.pop("digest_cache", None)
        except Exception as exc:
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            logger.exception("ساخت گزارش برای کاربر %s ناموفق بود", user_id)
            is_model_outage = (
                "سرویس مدل" in str(exc)
                or "مدل در دسترس نیست" in str(exc)
                or "هیچ دسته‌ای" in str(exc)
                or "503" in str(exc)
            )
            message = (
                "⚠️ <b>سرویس تحلیل هوش مصنوعی پاسخ نمی‌دهد</b>\n\n"
                "پیام‌ها دریافت شدند، اما سرویس مدل بعد از چند تلاش خطای موقت داد؛ "
                "برای جلوگیری از گزارش خام یا ساختگی، چیزی منتشر نشد."
                if is_model_outage else
                "⚠️ <b>ساخت گزارش کامل نشد</b>\n\nچند دقیقه دیگر دوباره امتحان کن."
            )
            await status_message.edit_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard(),
            )


CURRENCY_LOADING_STAGES = (
    "اتصال به کانال‌های ارز و طلا",
    "خواندن آخرین پیام‌ها",
    "استخراج نرخ دلار و طلا",
    "انتخاب تازه‌ترین به‌روزرسانی",
)


async def build_and_send_currency_report(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
    status_message,
) -> None:
    record_request(user_id, "currency")
    lock = user_locks[user_id]
    async with lock:
        loading_task = asyncio.create_task(
            animate_loading(status_message, "دلار و طلا", CURRENCY_HOURS_WINDOW, CURRENCY_LOADING_STAGES)
        )
        try:
            result = await prepare_currency_digest()
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            text = format_currency_digest(
                result["readings"], result["total_messages"], result["active_channels"],
                result.get("contributors"),
            )
            await status_message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=back_keyboard(),
            )
        except Exception as exc:
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            logger.exception("ساخت گزارش دلار و طلا برای کاربر %s ناموفق بود", user_id)
            is_model_outage = "سرویس مدل" in str(exc) or "503" in str(exc)
            message = (
                "⚠️ <b>سرویس تحلیل هوش مصنوعی پاسخ نمی‌دهد</b>\n\n"
                "پیام‌ها دریافت شدند، اما سرویس مدل بعد از چند تلاش خطای موقت داد."
                if is_model_outage else
                "⚠️ <b>دریافت نرخ دلار و طلا کامل نشد</b>\n\nچند دقیقه دیگر دوباره امتحان کن."
            )
            await status_message.edit_text(
                message, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
            )


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    touch_user(user_id, update.effective_user)
    if user_locks[user_id].locked():
        await update.effective_message.reply_text("گزارش قبلی هنوز آماده نشده.")
        return
    status = await update.effective_message.reply_text(
        "⏳ <b>در حال دریافت آخرین نرخ...</b>", parse_mode=ParseMode.HTML
    )
    await build_and_send_currency_report(context, update.effective_chat.id, user_id, status)


async def custom_hours_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    category = context.user_data.get("awaiting_hours")
    if not category:
        return
    raw = (update.effective_message.text or "").strip()
    try:
        hours = int(raw.translate(str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"
        )))
    except ValueError:
        await update.effective_message.reply_text(
            "فقط یک عدد بفرست؛ مثلاً <b>۲۴</b>.", parse_mode=ParseMode.HTML
        )
        return
    if not 1 <= hours <= 720:
        await update.effective_message.reply_text(
            "بازه باید بین <b>۱ تا ۷۲۰ ساعت</b> باشد.\nمثلاً برای ۱۵ روز: <b>۳۶۰</b>.",
            parse_mode=ParseMode.HTML,
        )
        return
    if user_locks[update.effective_user.id].locked():
        await update.effective_message.reply_text("گزارش قبلی هنوز آماده نشده.")
        return
    context.user_data.pop("awaiting_hours", None)
    status = await update.effective_message.reply_text(
        "⏳ <b>در حال شروع بررسی...</b>", parse_mode=ParseMode.HTML
    )
    await build_and_send_report(
        context, update.effective_chat.id, update.effective_user.id,
        category, hours, status,
    )


async def add_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("awaiting_channel"):
        return
    channel = safe_channel(update.effective_message.text or "")
    if not channel:
        await update.effective_message.reply_text(
            "فرمت درست نیست. @channel یا لینک عمومی t.me/channel را بفرست."
        )
        return
    prefs = user_prefs(update.effective_user.id)
    channels = list(dict.fromkeys(prefs.get("extra_channels", []) + [channel]))[:30]
    update_user_prefs(update.effective_user.id, extra_channels=channels)
    context.user_data.pop("awaiting_channel", None)
    await update.effective_message.reply_text(
        f"✅ کانال @{html.escape(channel)} اضافه شد.",
        parse_mode=ParseMode.HTML,
        reply_markup=channels_keyboard(),
    )


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """یک router واحد؛ اجازه نمی‌دهد ورودی ساعت توسط handler کانال بلعیده شود."""
    if context.user_data.get("awaiting_channel"):
        await add_channel_message(update, context)
    elif context.user_data.get("awaiting_hours"):
        await custom_hours_message(update, context)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""
    user = query.from_user
    touch_user(user.id, user)

    if data.startswith("hours:") and user_locks[user.id].locked():
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
    if data == "page:channels":
        prefs = user_prefs(user.id)
        channels = prefs.get("extra_channels", [])
        heading = "📚 <b>کانال‌های من</b>"
        listed = "\n".join(f"• @{html.escape(c)}" for c in channels) if channels else "هنوز کانالی اضافه نشده."
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
            (f"📚 <b>{sent} خبر دیگر ارسال شد</b>\n\n"
             + (f"هنوز {remaining} خبر مهم باقی مانده." if remaining else "همه خبرهای مهم این بازه ارسال شدند.")),
            parse_mode=ParseMode.HTML, reply_markup=more_keyboard(remaining),
        )
        if not remaining:
            context.user_data.pop("digest_cache", None)
        return
    if data == "digest:currency":
        if user_locks[user.id].locked():
            await query.answer("گزارش قبلی هنوز در حال آماده‌شدن است.", show_alert=True)
            return
        await query.edit_message_text(
            "⏳ <b>در حال دریافت آخرین نرخ...</b>", parse_mode=ParseMode.HTML
        )
        await build_and_send_currency_report(context, query.message.chat_id, user.id, query.message)
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
            "یک عدد بین ۱ تا ۷۲۰ بنویس؛ مثلاً <b>۳۶۰</b>.\n"
            "برای ۱۵ روز، عدد <b>۳۶۰</b> را ارسال کن.",
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


_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_num(value) -> str:
    """نمایش عدد با ارقام فارسی، هم‌راستا با بقیه متن راست‌به‌چپ."""
    return str(value).translate(_FA_DIGITS)


def format_last_seen(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
    except (ValueError, TypeError):
        return "نامشخص"
    return fa_num(dt.strftime("%Y/%m/%d %H:%M"))


def build_stats_report() -> tuple[str, list[str]]:
    """خلاصه آمار کلی + صفحه‌های لیست کامل کاربران (برای رعایت محدودیت طول پیام تلگرام)."""
    state = load_state()
    users = state.get("users", {})
    total_users = len(users)
    today = datetime.now().date().isoformat()
    new_today = sum(1 for u in users.values() if str(u.get("first_seen", "")).startswith(today))
    total_requests = sum(u.get("total_requests", 0) for u in users.values())

    category_totals: dict[str, int] = defaultdict(int)
    for u in users.values():
        for cat, count in u.get("requests_by_category", {}).items():
            category_totals[cat] += count
    top_category = max(category_totals.items(), key=lambda kv: kv[1], default=(None, 0))

    lines = [
        "📊 <b>آمار ربات TeleBrief</b>",
        "▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️",
        "",
        f"👥 کاربران: <b>{fa_num(total_users)}</b>",
        f"✨ جدید امروز: <b>{fa_num(new_today)}</b>",
        f"📨 درخواست‌ها: <b>{fa_num(total_requests)}</b>",
    ]
    if category_totals:
        lines.append("")
        lines.append("🗂 <b>به تفکیک موضوع</b>")
        icons = {"ai": "🤖", "security": "🛡", "currency": "💵"}
        for cat, count in sorted(category_totals.items(), key=lambda kv: -kv[1]):
            icon = icons.get(cat, "•")
            lines.append(f"{icon} {CATEGORY_NAMES.get(cat, cat)}: {fa_num(count)}")
        if top_category[0]:
            lines.append("")
            lines.append(
                f"🏆 پرطرفدار: <b>{CATEGORY_NAMES.get(top_category[0], top_category[0])}</b>"
                f" ({fa_num(top_category[1])} درخواست)"
            )
    summary = "\n".join(lines)

    ranked = sorted(users.items(), key=lambda kv: kv[1].get("total_requests", 0), reverse=True)
    rows = []
    for rank, (uid, u) in enumerate(ranked, start=1):
        name = html.escape(u.get("first_name") or "—")
        username = f" @{html.escape(u['username'])}" if u.get("username") else ""
        reqs = u.get("total_requests", 0)
        by_cat = u.get("requests_by_category", {})
        fav = max(by_cat.items(), key=lambda kv: kv[1], default=(None, 0))
        fav_text = f" — محبوب: {CATEGORY_NAMES.get(fav[0], fav[0])}" if fav[0] else ""
        last_seen = format_last_seen(u.get("last_interaction", ""))
        rows.append(
            f"☆ <b>کاربر {fa_num(rank)}:</b> {name}{username}\n"
            f"♡ {fa_num(reqs)} درخواست{fav_text} — آخرین فعالیت: {last_seen}\n"
            f"<i>شناسه: {uid}</i>"
        )

    pages, chunk, chunk_len = [], [], 0
    for row in rows:
        if chunk_len + len(row) + 1 > 3500:
            pages.append("\n\n".join(chunk))
            chunk, chunk_len = [], 0
        chunk.append(row)
        chunk_len += len(row) + 1
    if chunk:
        pages.append("\n\n".join(chunk))

    return summary, pages


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """فقط برای ادمین؛ برای هر کس دیگری کاملاً سکوت می‌کند تا وجود دستور فاش نشود."""
    if not ADMIN_ID or update.effective_user.id != ADMIN_ID:
        return
    summary, pages = build_stats_report()
    await update.effective_message.reply_text(summary, parse_mode=ParseMode.HTML)
    if not pages:
        return
    for i, page in enumerate(pages, start=1):
        header = f"👤 <b>لیست کاربران</b> — صفحه {fa_num(i)}/{fa_num(len(pages))}\n\n"
        await update.effective_message.reply_text(header + page, parse_mode=ParseMode.HTML)


async def post_init(application: Application) -> None:
    default_commands = [
        BotCommand("start", "شروع و نمایش منوی اصلی"),
        BotCommand("menu", "انتخاب دسته خبری"),
        BotCommand("price", "نرخ لحظه‌ای دلار و طلا"),
        BotCommand("help", "راهنمای استفاده"),
        BotCommand("about", "معرفی TeleBrief"),
    ]
    await application.bot.set_my_commands(default_commands)
    if ADMIN_ID:
        try:
            await application.bot.set_my_commands(
                default_commands + [BotCommand("stats", "آمار ربات (فقط ادمین)")],
                scope=BotCommandScopeChat(chat_id=ADMIN_ID),
            )
        except Exception:
            logger.warning("تنظیم منوی دستورهای اختصاصی ادمین ناموفق بود؛ /stats همچنان کار می‌کند.")


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
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    application.add_error_handler(error_handler)
    logger.info("%s آماده است", APP_NAME)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()