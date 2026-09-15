import asyncio
import html
import logging
import os
import secrets
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from telegram import (
    BotCommand, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup, Update,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest
from localized_bot import LocalizedBot, language_for, localize
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    MessageHandler, filters,
)

from digest_core import (
    ADMIN_ID, BOT_TOKEN,
    CURRENCY_HOURS_WINDOW, fetch_queue_busy, format_currency_digest, format_date_header,
    format_market_highlight, format_market_overview, format_story,
    prepare_currency_digest, prepare_digest, prepare_market_digest,
)

APP_NAME = "TeleBrief"
# DATA_DIR باید به مسیر یک Volume دائمی روی Railway اشاره کند (مثلاً /data)
# در غیر این صورت هر دیپلوی/ری‌استارت باعث پاک‌شدن bot_state.json می‌شود.
DATA_DIR = Path(os.getenv("DATA_DIR", "."))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / "bot_state.json"
logger = logging.getLogger(__name__)
user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
user_report_tasks: dict[int, tuple[str, asyncio.Task]] = {}
PAGE_SIZE = 10


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang:fa"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
    ]])


def user_language(user_id: int) -> str:
    return user_prefs(user_id).get("language", "fa")


def localized(user_id: int, text: str) -> str:
    return localize(text, user_language(user_id))


def commands_for(lang: str, admin: bool = False) -> list[BotCommand]:
    if lang == "en":
        commands = [
            BotCommand("start", "Choose language and open the main menu"),
            BotCommand("menu", "Choose a news category"),
            BotCommand("ai", "Artificial intelligence report"),
            BotCommand("security", "Cybersecurity report"),
            BotCommand("crypto", "Crypto and geopolitical risk report"),
            BotCommand("addchannel", "Add a personal channel"),
            BotCommand("price", "Latest USD and gold rates"),
            BotCommand("help", "Usage guide"),
            BotCommand("about", "About TeleBrief"),
            BotCommand("language", "Change language"),
        ]
        if admin:
            commands.append(BotCommand("stats", "Bot analytics (admin only)"))
        return commands
    commands = [
        BotCommand("start", "انتخاب زبان و نمایش منوی اصلی"),
        BotCommand("menu", "انتخاب دسته خبری"),
        BotCommand("ai", "گزارش هوش مصنوعی"),
        BotCommand("security", "گزارش امنیت شبکه"),
        BotCommand("crypto", "گزارش کریپتو و جنگ"),
        BotCommand("addchannel", "افزودن کانال شخصی"),
        BotCommand("price", "نرخ لحظه‌ای دلار و طلا"),
        BotCommand("help", "راهنمای استفاده"),
        BotCommand("about", "معرفی TeleBrief"),
        BotCommand("language", "تغییر زبان"),
    ]
    if admin:
        commands.append(BotCommand("stats", "آمار ربات (فقط ادمین)"))
    return commands


def report_token() -> str:
    return secrets.token_urlsafe(6)


def report_active(user_id: int) -> bool:
    current = user_report_tasks.get(user_id)
    return bool(current and not current[1].done())


def cancel_keyboard(user_id: int, token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ لغو گزارش", callback_data=f"cancel:{user_id}:{token}")],
    ])


def start_report_task(coro, user_id: int, token: str) -> bool:
    """تسک گزارش را در پس‌زمینه اجرا می‌کند و بلافاصله برمی‌گردد.

    نکته مهم: اگر اینجا await می‌کردیم، خودِ handler که این تابع را صدا زده
    تا پایان گزارش تمام نمی‌شد. چون python-telegram-bot به‌صورت پیش‌فرض
    آپدیت‌ها را یکی‌یکی پردازش می‌کند (concurrent_updates=False)، یعنی کلیک
    روی دکمه «لغو گزارش» اصلاً به هیچ handler‌ای نمی‌رسید تا گزارش قبلی کامل
    تمام شود — همان دلیلی که دکمه لغو کار نمی‌کرد. با اجرای تسک در پس‌زمینه
    و برگشت فوری، آپدیت بعدی (از جمله کلیک لغو) بلافاصله پردازش می‌شود."""
    # رزرو قبل از اولین await انجام می‌شود؛ در نتیجه دابل‌کلیک دو گزارش نمی‌سازد.
    if report_active(user_id):
        coro.close()
        return False
    task = asyncio.create_task(coro)
    user_report_tasks[user_id] = (token, task)

    def _cleanup(done_task: asyncio.Task) -> None:
        current = user_report_tasks.get(user_id)
        if current and current[1] is done_task:
            user_report_tasks.pop(user_id, None)
        if not done_task.cancelled():
            try:
                error = done_task.exception()
            except asyncio.CancelledError:
                return
            if error is not None:
                logger.error(
                    "تسک پس‌زمینه گزارش برای کاربر %s شکست خورد", user_id,
                    exc_info=(type(error), error, error.__traceback__),
                )

    task.add_done_callback(_cleanup)
    return True

# ---------------------------------------------------------------------------
# عضویت اجباری در کانال
# نکته مهم: ربات باید در کانال زیر ادمین باشد تا بتواند وضعیت عضویت کاربرها را
# با getChatMember بررسی کند؛ در غیر این صورت این بررسی به‌صورت خودکار عبور
# داده می‌شود (fail-open) تا کل ربات به‌خاطر یک تنظیم فراموش‌شده از کار نیفتد.
# ---------------------------------------------------------------------------
REQUIRED_CHANNEL_USERNAME = "atishbekakestar"
REQUIRED_CHANNEL_LINK = "https://t.me/atishbekakestar"
REQUIRED_CHANNEL_DISPLAY = "آتیش بی خاکستر"
JOIN_CHECK_CALLBACK = "join:check"


def join_required_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("☑️ عضویت در کانال", url=REQUIRED_CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم، بررسی کن", callback_data=JOIN_CHECK_CALLBACK)],
    ])


def join_required_text(first_name: str = "") -> str:
    name = html.escape(first_name or "دوست عزیز")
    return (
        f"\u200fسلام {name} عزیز 🌹\n\n"
        "\u200fخوشحالیم که به TeleBrief سر زدید. برای استفاده از امکانات ربات، "
        "لازم است ابتدا عضو کانال زیر شوید:\n\n"
        f"<blockquote>\u200f🌀 <a href=\"{REQUIRED_CHANNEL_LINK}\">{REQUIRED_CHANNEL_DISPLAY}</a></blockquote>\n\n"
        "\u200fپس از عضویت، کافی‌ست روی دکمه زیر بزنید تا بلافاصله دسترسی کامل برایتان فعال شود."
    )


async def is_channel_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """بررسی می‌کند کاربر عضو کانال اجباری هست یا نه. ادمین همیشه معاف است."""
    if ADMIN_ID and user_id == ADMIN_ID:
        return True
    try:
        member = await context.bot.get_chat_member(
            chat_id=f"@{REQUIRED_CHANNEL_USERNAME}", user_id=user_id
        )
        return member.status not in ("left", "kicked")
    except BadRequest:
        logger.warning(
            "بررسی عضویت کاربر %s ناموفق بود؛ دسترسی تا رفع تنظیم کانال بسته می‌ماند.",
            user_id,
        )
        return False
    except Exception:
        logger.exception("خطای غیرمنتظره هنگام بررسی عضویت کاربر %s", user_id)
        return False


async def send_join_wall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is not None:
        await message.reply_text(
            join_required_text(user.first_name if user else ""),
            parse_mode=ParseMode.HTML,
            reply_markup=join_required_keyboard(),
            disable_web_page_preview=True,
        )


async def require_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """اگر کاربر عضو کانال نباشد، دیوار عضویت را نشان می‌دهد و False برمی‌گرداند."""
    user = update.effective_user
    if user is None or await is_channel_member(context, user.id):
        return True
    await send_join_wall(update, context)
    return False


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
    """ذخیره اتمیک؛ نام موقت یکتا مانع برخورد چند پردازش می‌شود."""
    import json
    temp_file = STATE_FILE.with_name(
        f".{STATE_FILE.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    )
    try:
        temp_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temp_file, STATE_FILE)
    except OSError:
        logger.exception("ذخیره فایل وضعیت ناموفق بود")
        try:
            temp_file.unlink(missing_ok=True)
        except OSError:
            pass


CATEGORY_NAMES = {"ai": "هوش مصنوعی", "security": "امنیت شبکه", "currency": "دلار و طلا", "crypto": "کریپتو و جنگ"}


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
    """هر بار که کاربر یک گزارش واقعی درخواست می‌کند (AI/امنیت/دلار/کریپتو) صدا زده می‌شود."""
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


MAX_EXTRA_CHANNELS = 30


def channels_keyboard(has_channels: bool = False) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton("🌀 افزودن کانال", callback_data="channel:add")]]
    if has_channels:
        rows.append([
            InlineKeyboardButton("🌀 حذف یک کانال", callback_data="channel:remove"),
            InlineKeyboardButton("🌀 پاک‌کردن همه", callback_data="channel:clear"),
        ])
    rows.append([InlineKeyboardButton("🌀 منوی اصلی", callback_data="page:menu")])
    return InlineKeyboardMarkup(rows)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌀 هوش مصنوعی", callback_data="digest:ai"),
         InlineKeyboardButton("🌀 امنیت شبکه", callback_data="digest:security")],
        [InlineKeyboardButton("🌀 دلار و طلا", callback_data="digest:currency"),
         InlineKeyboardButton("🌀 کریپتو و جنگ", callback_data="digest:crypto")],
        [InlineKeyboardButton("🌀 کانال‌های من", callback_data="page:channels"),
         InlineKeyboardButton("🌀 راهنما", callback_data="page:help")],
        [InlineKeyboardButton("🌀 درباره ربات", callback_data="page:about")],
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
        [InlineKeyboardButton("🌀 بازه دلخواه", callback_data=f"custom:{category}")],
        [InlineKeyboardButton("🌀 بازگشت", callback_data="page:menu")],
    ])


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌀 بازگشت به منوی اصلی", callback_data="page:menu")]
    ])


def welcome_text(first_name: str, is_new: bool) -> str:
    name = html.escape(first_name or "دوست عزیز")
    return (
        f"👋 <b>سلام {name} عزیز، خوش اومدی!</b>\n\n"
        f"من <b>{APP_NAME}</b> هستم؛ دستیاری برای رصد و تحلیل اخبار در حوزه‌های "
        "هوش مصنوعی، امنیت شبکه، بازار دلار و طلا و همچنین وضعیت بازار کریپتو و جنگ.\n\n"
        "<blockquote>پیام‌های مهم را شناسایی می‌کنم، موارد کم‌ارزش و تکراری را کنار می‌گذارم "
        "و نتیجه را به‌صورت خلاصه و رتبه‌بندی‌شده، همراه با منبع مستقیم هر خبر، "
        "در اختیارتان قرار می‌دهم.</blockquote>\n\n"
        "در خدمت شما هستم ، از طریق دکمه‌های زیر می‌توانید از امکانات ربات استفاده کنید :")


MENU_PROMPT_TEXT = (
    "🗞 <b>چه گزارشی می‌خوای؟</b>\n\n"
    "یکی از حوزه‌های خبری زیر را انتخاب کن تا مهم‌ترین و تازه‌ترین یافته‌های همان حوزه برایت آماده شود.\n\n"
    "<blockquote>دسته موردنظرت را از دکمه‌های زیر انتخاب کن</blockquote>"
)

HELP_TEXT = (
    "📖 <b>راهنمای TeleBrief</b>\n\n"
    "حوزه و بازه زمانی موردنظر خود را انتخاب کنید. ربات تمام پیام‌های آن بازه را بررسی می‌کند، "
    "موارد کم‌اهمیت را حذف می‌کند، خبرهای مشابه را با یکدیگر ادغام می‌کند و مهم‌ترین نتایج را "
    "به ترتیب اهمیت برایتان ارسال می‌کند.\n\n"
    "<blockquote>بخش «دلار و طلا» به‌صورت مجزا عمل می‌کند: به‌جای رتبه‌بندی خبر، صرفاً "
    "تازه‌ترین نرخ دلار و طلای ۱۸ عیار را از کانال‌های مرجع استخراج می‌کند و همواره "
    "جدیدترین به‌روزرسانی موجود میان چند کانال را نمایش می‌دهد.</blockquote>\n\n"
    "<blockquote>بخش «کریپتو و جنگ» هم مکانیزم جداگانه‌ای دارد: به‌جای فهرست خبر، یک "
    "گزارش وضعیت کامل بازار رمزارز و ریسک‌های جنگ/ژئوپلیتیک مؤثر بر آن می‌سازد؛ یک پیام "
    "روایت کلی وضعیت بازار و پیام‌های بعدی، نکات مهم منبع‌دار هستند که در صورت زیاد بودن "
    "با دکمه «مشاهده نکته‌های بعدی» به‌صورت ده‌تایی نمایش داده می‌شوند.</blockquote>\n\n"
    "<b>دستورها</b>\n"
    "/start - شروع و نمایش منوی اصلی\n"
    "/menu - بازکردن منو\n"
    "/ai - گزارش هوش مصنوعی\n"
    "/security - گزارش امنیت شبکه\n"
    "/crypto - گزارش کریپتو و جنگ\n"
    "/addchannel - افزودن کانال شخصی\n"
    "/price - نرخ لحظه‌ای دلار و طلا\n"
    "/help - راهنمای استفاده\n"
    "/about - معرفی ربات\n\n"
    "<blockquote>برای هر خبر، روی «مشاهده پیام اصلی» بزن تا مستقیماً به منبع تلگرام بروی.</blockquote>"
)

ABOUT_TEXT = (
    "\u200fℹ️ <b>درباره</b> \u200e<b>TeleBrief</b>\u200f\n\n"
    "\u200fیک خبرخوان تحلیلی فارسی برای حوزه‌های <b>هوش مصنوعی</b>، <b>امنیت شبکه</b>، "
    "<b>دلار و طلا</b> و <b>کریپتو و جنگ</b>. "
    "هدفش زیادکردن تعداد پیام‌ها نیست؛ هدفش پیدا کردن چیزهایی است که واقعاً ارزش خواندن دارند.\n\n"
    "<blockquote>کمتر اسکرول کن، بهتر باخبر شو.</blockquote>"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    touch_user(user.id, user)
    await update.effective_message.reply_text(
        "🌐 <b>زبان خود را انتخاب کنید | Choose your language</b>\n\n"
        "برای ادامه زبان را انتخاب کنید. | Select a language to continue.",
        parse_mode=ParseMode.HTML, reply_markup=language_keyboard(),
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_join(update, context):
        return
    touch_user(update.effective_user.id, update.effective_user)
    await update.effective_message.reply_text(
        MENU_PROMPT_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_join(update, context):
        return
    touch_user(update.effective_user.id, update.effective_user)
    await update.effective_message.reply_text(
        HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_join(update, context):
        return
    touch_user(update.effective_user.id, update.effective_user)
    await update.effective_message.reply_text(
        ABOUT_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
    )



def more_keyboard(remaining: int, user_id: int, token: str) -> InlineKeyboardMarkup:
    rows = []
    if remaining > 0:
        rows.append([
            InlineKeyboardButton(
                f"مشاهده خبرهای بعدی ({min(PAGE_SIZE, remaining)} تا از {remaining} خبر باقی‌مانده) 🌀",
                callback_data=f"digest:more:{user_id}:{token}",
            )
        ])
    rows.append([InlineKeyboardButton("🌀 منوی اصلی", callback_data="page:menu")])
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
            text=format_story(story, rank, cache["category"], lang=cache.get("lang", "fa")),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        await asyncio.sleep(0.35)
    cache["offset"] = end
    return end - start, len(stories) - end


def more_market_keyboard(remaining: int, user_id: int, token: str) -> InlineKeyboardMarkup:
    rows = []
    if remaining > 0:
        rows.append([
            InlineKeyboardButton(
                f"مشاهده نکته‌های بعدی ({min(PAGE_SIZE, remaining)} تا از {remaining} نکته باقی‌مانده) 🌀",
                callback_data=f"market:more:{user_id}:{token}",
            )
        ])
    rows.append([InlineKeyboardButton("🌀 منوی اصلی", callback_data="page:menu")])
    return InlineKeyboardMarkup(rows)


async def send_market_page(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    cache: dict,
) -> tuple[int, int]:
    highlights = cache["highlights"]
    start = cache.get("offset", 0)
    end = min(start + PAGE_SIZE, len(highlights))
    for rank, item in enumerate(highlights[start:end], start=start + 1):
        await context.bot.send_message(
            chat_id=chat_id,
            text=format_market_highlight(item, rank, lang=cache.get("lang", "fa")),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        await asyncio.sleep(0.35)
    cache["offset"] = end
    return end - start, len(highlights) - end


LOADING_STAGES = (
    "اتصال به منابع معتبر",
    "استخراج پیام‌های مهم",
    "حذف تبلیغات و موارد تکراری",
    "رتبه‌بندی نهایی خبرها",
)


async def animate_loading(
    status_message, category_name: str, hours: int, user_id: int, token: str,
    stages: tuple[str, ...] = LOADING_STAGES,
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
                    reply_markup=cancel_keyboard(user_id, token),
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
    token: str,
) -> None:
    category_name = "هوش مصنوعی" if category == "ai" else "امنیت شبکه"
    lock = user_locks[user_id]
    async with lock:
        loading_task = asyncio.create_task(
            animate_loading(status_message, category_name, hours, user_id, token)
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
            result = await prepare_digest(hours=hours, category=category, extra_channels=extra_channels, lang=user_language(user_id))
            record_request(user_id, category)
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            stories = result["stories"]
            cache = {"stories": stories, "category": category, "offset": 0, "lang": user_language(user_id)}
            context.user_data.setdefault("digest_caches", {})[token] = cache
            await status_message.edit_text(
                format_date_header(hours, result["total_messages"], result["active_channels"], lang=user_language(user_id))
                + f"\n\n<b>وضعیت کانال‌ها:</b> هر {result['configured_channels']} کانال پیمایش شد؛ {result['active_channels']} کانال در این بازه پیام داشت.",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            if not stories:
                context.user_data.get("digest_caches", {}).pop(token, None)
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
                reply_markup=more_keyboard(remaining, user_id, token),
            )
            if not remaining:
                context.user_data.get("digest_caches", {}).pop(token, None)
        except asyncio.CancelledError:
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            logger.info("ساخت گزارش برای کاربر %s توسط خودش لغو شد", user_id)
            context.user_data.get("digest_caches", {}).pop(token, None)
            try:
                await status_message.edit_text(
                    "❌ <b>گزارش لغو شد</b>\n\nهر وقت خواستی از منو دوباره درخواست بده.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=back_keyboard(),
                )
            except Exception:
                logger.debug("ویرایش پیام لغو ناموفق بود", exc_info=True)
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
    token: str,
) -> None:
    lock = user_locks[user_id]
    async with lock:
        loading_task = asyncio.create_task(
            animate_loading(status_message, "دلار و طلا", CURRENCY_HOURS_WINDOW, user_id, token, CURRENCY_LOADING_STAGES)
        )
        try:
            result = await prepare_currency_digest()
            record_request(user_id, "currency")
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            text = format_currency_digest(
                result["readings"], result["total_messages"], result["active_channels"],
                result.get("contributors"), lang=user_language(user_id),
            )
            await status_message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=back_keyboard(),
            )
        except asyncio.CancelledError:
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            logger.info("ساخت گزارش دلار و طلا برای کاربر %s توسط خودش لغو شد", user_id)
            try:
                await status_message.edit_text(
                    "❌ <b>گزارش لغو شد</b>\n\nهر وقت خواستی از منو دوباره درخواست بده.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=back_keyboard(),
                )
            except Exception:
                logger.debug("ویرایش پیام لغو ناموفق بود", exc_info=True)
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


CRYPTO_LOADING_STAGES = (
    "اتصال به کانال‌های بازار",
    "جمع‌آوری اخبار رمزارز و جنگ",
    "تفکیک نکات مهم از حاشیه",
    "نوشتن گزارش نهایی",
)


async def build_and_send_market_report(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
    hours: int,
    status_message,
    token: str,
) -> None:
    """مکانیزمش با build_and_send_report فرق دارد: به‌جای فهرست خبر
    رتبه‌بندی‌شده و صفحه‌بندی «بیشتر»، یک گزارش کامل در چند پیام می‌فرستد —
    پیام اول روایت کلی وضعیت بازار، پیام‌های بعدی نکات مهمِ منبع‌دار."""
    lock = user_locks[user_id]
    async with lock:
        loading_task = asyncio.create_task(
            animate_loading(status_message, "کریپتو و جنگ", hours, user_id, token, CRYPTO_LOADING_STAGES)
        )
        try:
            await asyncio.sleep(0.05)
            await status_message.edit_text(
                "🔎 <b>بررسی عمیق بازار کریپتو و جنگ</b>\n\n"
                f"در حال خواندن کانال‌های بازار و تحلیل پیام‌های {hours} ساعت اخیر...\n"
                f"<blockquote>بازه انتخاب‌شده: {hours} ساعت</blockquote>\n"
                "<blockquote expandable>وضعیت کلی بازار و ریسک‌های جنگ/ژئوپلیتیک مؤثر بر آن جمع‌بندی می‌شود.</blockquote>",
                parse_mode=ParseMode.HTML,
            )
            result = await prepare_market_digest(hours=hours, lang=user_language(user_id))
            record_request(user_id, "crypto")
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            highlights = result["highlights"]
            await status_message.edit_text(
                format_market_overview(
                    hours, result["total_messages"], result["active_channels"], result["overview"], lang=user_language(user_id)
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            if not highlights:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "📌 <b>نکته منبع‌دار مجزایی پیدا نشد</b>\n\n"
                        "وضعیت کلی بازار در پیام بالا آمد."
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=back_keyboard(),
                )
                return
            cache = {"highlights": highlights, "offset": 0, "lang": user_language(user_id)}
            context.user_data.setdefault("market_caches", {})[token] = cache
            sent, remaining = await send_market_page(context, chat_id, cache)
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"✅ <b>{fa_num(sent)} نکته اول از مجموع {fa_num(sent + remaining)} نکته ارسال شد</b>\n\n"
                    + (f"هنوز {fa_num(remaining)} نکته مهم باقی مانده." if remaining else "همهٔ نکته‌های مهم بازار رمز ارز ارسال شدند.")
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=more_market_keyboard(remaining, user_id, token),
            )
            if not remaining:
                context.user_data.get("market_caches", {}).pop(token, None)
        except asyncio.CancelledError:
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            logger.info("گزارش بازار کریپتو برای کاربر %s توسط خودش لغو شد", user_id)
            context.user_data.get("market_caches", {}).pop(token, None)
            try:
                await status_message.edit_text(
                    "❌ <b>گزارش لغو شد</b>\n\nهر وقت خواستی از منو دوباره درخواست بده.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=back_keyboard(),
                )
            except Exception:
                logger.debug("ویرایش پیام لغو ناموفق بود", exc_info=True)
        except Exception as exc:
            loading_task.cancel()
            await asyncio.gather(loading_task, return_exceptions=True)
            logger.exception("گزارش بازار کریپتو برای کاربر %s ناموفق بود", user_id)
            is_model_outage = (
                "سرویس مدل" in str(exc)
                or "مدل در دسترس نیست" in str(exc)
                or "503" in str(exc)
            )
            message = (
                "⚠️ <b>سرویس تحلیل هوش مصنوعی پاسخ نمی‌دهد</b>\n\n"
                "پیام‌ها دریافت شدند، اما سرویس مدل بعد از چند تلاش خطای موقت داد."
                if is_model_outage else
                "⚠️ <b>ساخت گزارش کامل نشد</b>\n\nچند دقیقه دیگر دوباره امتحان کن."
            )
            await status_message.edit_text(
                message, parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
            )


async def category_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_join(update, context):
        return
    user = update.effective_user
    touch_user(user.id, user)
    category = (update.effective_message.text or "").split("@", 1)[0].lstrip("/").lower()
    if category not in {"ai", "security", "crypto"}:
        return
    await update.effective_message.reply_text(
        "⏱ <b>چند ساعت اخیر بررسی شود؟</b>\n\n"
        "بازه آماده را انتخاب کن یا عدد دلخواهت را بنویس.",
        parse_mode=ParseMode.HTML, reply_markup=hours_keyboard(category),
    )


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not await require_join(update, context):
        return
    touch_user(user_id, update.effective_user)
    if report_active(user_id):
        await update.effective_message.reply_text("گزارش قبلی هنوز آماده نشده.")
        return
    queue_notice = (
        "\n\n<i>چند نفر دیگر هم هم‌زمان درخواست دارند؛ ربات خراب نیست، فقط کمی صف دارد.</i>"
        if fetch_queue_busy() else ""
    )
    status = await update.effective_message.reply_text(
        "⏳ <b>در حال دریافت آخرین نرخ...</b>" + queue_notice, parse_mode=ParseMode.HTML
    )
    token = report_token()
    start_report_task(
        build_and_send_currency_report(context, update.effective_chat.id, user_id, status, token),
        user_id, token,
    )


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
    if report_active(update.effective_user.id):
        await update.effective_message.reply_text("گزارش قبلی هنوز آماده نشده.")
        return
    context.user_data.pop("awaiting_hours", None)
    queue_notice = (
        "\n\n<i>چند نفر دیگر هم هم‌زمان درخواست دارند؛ ربات خراب نیست، فقط کمی صف دارد.</i>"
        if fetch_queue_busy() else ""
    )
    status = await update.effective_message.reply_text(
        "⏳ <b>در حال شروع بررسی...</b>" + queue_notice, parse_mode=ParseMode.HTML
    )
    token = report_token()
    if category == "crypto":
        start_report_task(
            build_and_send_market_report(
                context, update.effective_chat.id, update.effective_user.id, hours, status, token,
            ),
            update.effective_user.id, token,
        )
    else:
        start_report_task(
            build_and_send_report(
                context, update.effective_chat.id, update.effective_user.id,
                category, hours, status, token,
            ),
            update.effective_user.id, token,
        )


def channels_page_text(channels: list[str]) -> str:
    heading = "📚 <b>کانال‌های شخصی من</b>"
    intro = (
        "<blockquote>این کانال‌ها علاوه بر منابع پیش‌فرض ربات بررسی می‌شوند و در گزارش‌های "
        "«هوش مصنوعی» و «امنیت شبکه» لحاظ خواهند شد.</blockquote>"
    )
    count_line = f"ظرفیت استفاده‌شده: <b>{fa_num(len(channels))}</b> از <b>{fa_num(MAX_EXTRA_CHANNELS)}</b> کانال"
    if channels:
        listed = "\n".join(f"• @{html.escape(c)}" for c in channels)
    else:
        listed = "هنوز کانالی اضافه نشده است."
    return f"{heading}\n\n{intro}\n\n{count_line}\n\n{listed}"


def channel_removal_prompt_text(channels: list[str]) -> str:
    listed = "\n".join(f"• @{html.escape(c)}" for c in channels)
    return (
        "🌀 <b>حذف کانال</b>\n\n"
        "نام یکی از کانال‌های زیر را بفرست (با یا بدون @) تا از لیست حذف شود:\n\n"
        f"{listed}"
    )


def channel_clear_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌀 بله، پاک کن", callback_data="channel:clear:yes"),
         InlineKeyboardButton("🌀 انصراف", callback_data="channel:clear:no")],
    ])


async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_join(update, context):
        return
    user = update.effective_user
    touch_user(user.id, user)
    prefs = user_prefs(user.id)
    remaining = MAX_EXTRA_CHANNELS - len(prefs.get("extra_channels", []))
    context.user_data["awaiting_channel"] = True
    await update.effective_message.reply_text(
        "🌀 <b>افزودن کانال</b>\n\n"
        "آی‌دی عمومی کانال یا لینک آن را بفرست؛ مثال: <b>@thehackernews</b>\n\n"
        f"<blockquote>ظرفیت باقی‌مانده: {fa_num(remaining)} کانال</blockquote>",
        parse_mode=ParseMode.HTML, reply_markup=back_keyboard(),
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
    try:
        chat = await context.bot.get_chat(f"@{channel}")
        if getattr(chat, "type", None) != "channel" or not getattr(chat, "username", None):
            raise ValueError("not a public channel")
        channel = chat.username
    except Exception:
        await update.effective_message.reply_text(
            "این کانال عمومی پیدا نشد یا ربات به آن دسترسی ندارد؛ نام را دوباره بررسی کن."
        )
        return
    prefs = user_prefs(update.effective_user.id)
    existing = prefs.get("extra_channels", [])
    if channel.casefold() in {c.casefold() for c in existing}:
        context.user_data.pop("awaiting_channel", None)
        await update.effective_message.reply_text(
            f"این کانال (@{html.escape(channel)}) از قبل در لیست شماست.",
            parse_mode=ParseMode.HTML,
            reply_markup=channels_keyboard(has_channels=True),
        )
        return
    if len(existing) >= MAX_EXTRA_CHANNELS:
        context.user_data.pop("awaiting_channel", None)
        await update.effective_message.reply_text(
            f"ظرفیت شما تکمیل شده است (حداکثر {fa_num(MAX_EXTRA_CHANNELS)} کانال). "
            "برای افزودن کانال جدید، ابتدا یکی را حذف کنید.",
            parse_mode=ParseMode.HTML,
            reply_markup=channels_keyboard(has_channels=True),
        )
        return
    channels = existing + [channel]
    update_user_prefs(update.effective_user.id, extra_channels=channels)
    context.user_data.pop("awaiting_channel", None)
    await update.effective_message.reply_text(
        f"✅ کانال @{html.escape(channel)} اضافه شد.\n\n"
        f"ظرفیت استفاده‌شده: {fa_num(len(channels))} از {fa_num(MAX_EXTRA_CHANNELS)} کانال",
        parse_mode=ParseMode.HTML,
        reply_markup=channels_keyboard(has_channels=True),
    )


async def remove_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("awaiting_channel_removal"):
        return
    channel = safe_channel(update.effective_message.text or "")
    prefs = user_prefs(update.effective_user.id)
    existing = prefs.get("extra_channels", [])
    matches = [c for c in existing if channel and c.casefold() == channel.casefold()]
    if not matches:
        await update.effective_message.reply_text(
            "این کانال در لیست شما پیدا نشد. نام دقیق‌تری بفرست یا از منو انصراف بده.",
            reply_markup=back_keyboard(),
        )
        return
    channel = matches[0]
    channels = [c for c in existing if c.casefold() != channel.casefold()]
    update_user_prefs(update.effective_user.id, extra_channels=channels)
    context.user_data.pop("awaiting_channel_removal", None)
    await update.effective_message.reply_text(
        f"🗑 کانال @{html.escape(channel)} حذف شد.\n\n"
        f"ظرفیت استفاده‌شده: {fa_num(len(channels))} از {fa_num(MAX_EXTRA_CHANNELS)} کانال",
        parse_mode=ParseMode.HTML,
        reply_markup=channels_keyboard(has_channels=bool(channels)),
    )


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """یک router واحد؛ اجازه نمی‌دهد ورودی ساعت توسط handler کانال بلعیده شود."""
    if not await require_join(update, context):
        return
    if context.user_data.get("awaiting_channel"):
        await add_channel_message(update, context)
    elif context.user_data.get("awaiting_channel_removal"):
        await remove_channel_message(update, context)
    elif context.user_data.get("awaiting_hours"):
        await custom_hours_message(update, context)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""
    user = query.from_user

    if data in {"lang:fa", "lang:en"}:
        lang = data.split(":", 1)[1]
        touch_user(user.id, user)
        update_user_prefs(user.id, language=lang)
        try:
            await context.bot.set_my_commands(
                commands_for(lang, admin=bool(ADMIN_ID and user.id == ADMIN_ID)),
                scope=BotCommandScopeChat(chat_id=user.id),
            )
        except Exception:
            logger.warning("Could not update command menu for user %s", user.id)
        await query.answer("زبان فارسی انتخاب شد." if lang == "fa" else "English selected.")
        if not await is_channel_member(context, user.id):
            await query.edit_message_text(
                join_required_text(user.first_name), parse_mode=ParseMode.HTML,
                reply_markup=join_required_keyboard(), disable_web_page_preview=True,
            )
            return
        await query.edit_message_text(
            welcome_text(user.first_name, False), parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(), disable_web_page_preview=True,
        )
        return

    if data == JOIN_CHECK_CALLBACK:
        if await is_channel_member(context, user.id):
            is_new = touch_user(user.id, user)
            await query.answer(localized(user.id, "✅ عضویت تایید شد!"))
            await query.edit_message_text(
                welcome_text(user.first_name, is_new),
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard(),
                disable_web_page_preview=True,
            )
        else:
            await query.answer(localized(user.id, "هنوز عضو کانال نشدی 🙁"), show_alert=True)
        return

    if data.startswith("cancel:"):
        try:
            _, owner_raw, token = data.split(":", 2)
            owner_id = int(owner_raw)
        except (ValueError, TypeError):
            await query.answer(localized(user.id, "دکمه نامعتبر است."), show_alert=True)
            return
        current = user_report_tasks.get(owner_id)
        if user.id != owner_id:
            await query.answer(localized(user.id, "این گزارش متعلق به شما نیست."), show_alert=True)
        elif current and current[0] == token and not current[1].done():
            current[1].cancel()
            await query.answer(localized(user.id, "در حال لغو گزارش..."))
        else:
            await query.answer(localized(user.id, "این گزارش دیگر در جریان نیست."), show_alert=True)
        return

    if not await is_channel_member(context, user.id):
        await query.answer()
        await query.edit_message_text(
            join_required_text(user.first_name),
            parse_mode=ParseMode.HTML,
            reply_markup=join_required_keyboard(),
            disable_web_page_preview=True,
        )
        return

    touch_user(user.id, user)
    if data.startswith("hours:") and report_active(user.id):
        await query.answer(localized(user.id, "گزارش قبلی هنوز در حال آماده‌شدن است."), show_alert=True)
        return
    await query.answer()

    if data == "page:menu":
        context.user_data.pop("awaiting_channel", None)
        context.user_data.pop("awaiting_channel_removal", None)
        context.user_data.pop("awaiting_hours", None)
        await query.edit_message_text(
            MENU_PROMPT_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(),
        )
        return
    if data == "page:channels":
        prefs = user_prefs(user.id)
        channels = prefs.get("extra_channels", [])
        await query.edit_message_text(
            channels_page_text(channels),
            parse_mode=ParseMode.HTML,
            reply_markup=channels_keyboard(has_channels=bool(channels)),
        )
        return
    if data == "channel:add":
        prefs = user_prefs(user.id)
        remaining = MAX_EXTRA_CHANNELS - len(prefs.get("extra_channels", []))
        context.user_data["awaiting_channel"] = True
        await query.edit_message_text(
            "🌀 <b>افزودن کانال</b>\n\n"
            "آی‌دی عمومی کانال یا لینک آن را بفرست؛ مثال: <b>@thehackernews</b>\n\n"
            f"<blockquote>ظرفیت باقی‌مانده: {fa_num(remaining)} کانال</blockquote>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard(),
        )
        return
    if data == "channel:remove":
        prefs = user_prefs(user.id)
        channels = prefs.get("extra_channels", [])
        if not channels:
            await query.answer(localized(user.id, "لیست شما خالی است."), show_alert=True)
            return
        context.user_data["awaiting_channel_removal"] = True
        await query.edit_message_text(
            channel_removal_prompt_text(channels),
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard(),
        )
        return
    if data == "channel:clear":
        prefs = user_prefs(user.id)
        if not prefs.get("extra_channels", []):
            await query.answer(localized(user.id, "لیست شما خالی است."), show_alert=True)
            return
        await query.edit_message_text(
            "🌀 <b>پاک‌کردن همه کانال‌ها</b>\n\n"
            "این کار همه کانال‌های شخصی شما را حذف می‌کند و قابل بازگشت نیست. مطمئن هستید؟",
            parse_mode=ParseMode.HTML,
            reply_markup=channel_clear_confirm_keyboard(),
        )
        return
    if data == "channel:clear:yes":
        update_user_prefs(user.id, extra_channels=[])
        await query.edit_message_text(
            "🗑 همه کانال‌های شخصی شما حذف شدند.",
            parse_mode=ParseMode.HTML,
            reply_markup=channels_keyboard(has_channels=False),
        )
        return
    if data == "channel:clear:no":
        prefs = user_prefs(user.id)
        channels = prefs.get("extra_channels", [])
        await query.edit_message_text(
            channels_page_text(channels),
            parse_mode=ParseMode.HTML,
            reply_markup=channels_keyboard(has_channels=bool(channels)),
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
    if data.startswith("digest:more:"):
        try:
            _, _, owner_raw, token = data.split(":", 3)
            owner_id = int(owner_raw)
        except (ValueError, TypeError):
            await query.answer(localized(user.id, "دکمه نامعتبر است."), show_alert=True)
            return
        if user.id != owner_id:
            await query.answer(localized(user.id, "این گزارش متعلق به شما نیست."), show_alert=True)
            return
        cache = context.user_data.get("digest_caches", {}).get(token)
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
            parse_mode=ParseMode.HTML, reply_markup=more_keyboard(remaining, user.id, token),
        )
        if not remaining:
            context.user_data.get("digest_caches", {}).pop(token, None)
        return
    if data.startswith("market:more:"):
        try:
            _, _, owner_raw, token = data.split(":", 3)
            owner_id = int(owner_raw)
        except (ValueError, TypeError):
            await query.answer(localized(user.id, "دکمه نامعتبر است."), show_alert=True)
            return
        if user.id != owner_id:
            await query.answer(localized(user.id, "این گزارش متعلق به شما نیست."), show_alert=True)
            return
        cache = context.user_data.get("market_caches", {}).get(token)
        if not cache:
            await query.edit_message_text(
                "⌛️ <b>این گزارش منقضی شده</b>\n\nاز منو گزارش تازه بگیر.",
                parse_mode=ParseMode.HTML, reply_markup=back_keyboard(),
            )
            return
        await query.edit_message_text("⏳ <b>در حال ارسال ۱۰ نکته بعدی...</b>", parse_mode=ParseMode.HTML)
        sent, remaining = await send_market_page(context, query.message.chat_id, cache)
        await query.edit_message_text(
            (f"📚 <b>{fa_num(sent)} نکته دیگر ارسال شد</b>\n\n"
             + (f"هنوز {fa_num(remaining)} نکته مهم باقی مانده." if remaining else "همهٔ نکته‌های مهم بازار رمز ارز ارسال شدند.")),
            parse_mode=ParseMode.HTML, reply_markup=more_market_keyboard(remaining, user.id, token),
        )
        if not remaining:
            context.user_data.get("market_caches", {}).pop(token, None)
        return
    if data == "digest:currency":
        if report_active(user.id):
            await query.answer(localized(user.id, "گزارش قبلی هنوز در حال آماده‌شدن است."), show_alert=True)
            return
        queue_notice = (
            "\n\n<i>چند نفر دیگر هم هم‌زمان درخواست دارند؛ ربات خراب نیست، فقط کمی صف دارد.</i>"
            if fetch_queue_busy() else ""
        )
        await query.edit_message_text(
            "⏳ <b>در حال دریافت آخرین نرخ...</b>" + queue_notice, parse_mode=ParseMode.HTML
        )
        token = report_token()
        start_report_task(
            build_and_send_currency_report(context, query.message.chat_id, user.id, query.message, token),
            user.id, token,
        )
        return
    if data in {"digest:ai", "digest:security", "digest:crypto"}:
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
        if report_active(user.id):
            await query.answer(localized(user.id, "گزارش قبلی هنوز در حال آماده‌شدن است."), show_alert=True)
            return
        context.user_data.pop("awaiting_hours", None)
        token = report_token()
        if category == "crypto":
            start_report_task(
                build_and_send_market_report(
                    context, query.message.chat_id, user.id, int(raw_hours), query.message, token,
                ),
                user.id, token,
            )
        else:
            start_report_task(
                build_and_send_report(
                    context, query.message.chat_id, user.id,
                    category, int(raw_hours), query.message, token,
                ),
                user.id, token,
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
    return fa_num(dt.strftime("%Y/%m/%d  -  %H:%M"))


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
        "<blockquote> آمار ربات TeleBrief</blockquote>",
        "",
        f"👥 کاربران: <b>{fa_num(total_users)}</b>",
        f"✨ جدید امروز: <b>{fa_num(new_today)}</b>",
        f"📨 درخواست‌ها: <b>{fa_num(total_requests)}</b>",
    ]
    if category_totals:
        lines.append("")
        lines.append("🗂 <b>به تفکیک موضوع</b>")
        icons = {"ai": "🤖", "security": "🛡", "currency": "💵", "crypto": "🪙"}
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
            f"<blockquote>☆ کاربر {fa_num(rank)}: {name}{username}</blockquote>\n"
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


def build_stats_report_en() -> tuple[str, list[str]]:
    state = load_state()
    users = state.get("users", {})
    today = datetime.now().date().isoformat()
    totals: dict[str, int] = defaultdict(int)
    for item in users.values():
        for category, count in item.get("requests_by_category", {}).items():
            totals[category] += count
    total_requests = sum(item.get("total_requests", 0) for item in users.values())
    new_today = sum(1 for item in users.values() if str(item.get("first_seen", "")).startswith(today))
    names = {"ai": "Artificial Intelligence", "security": "Cybersecurity", "currency": "USD & Gold", "crypto": "Crypto & Geopolitics"}
    lines = ["<blockquote>TeleBrief Analytics</blockquote>", "", f"👥 Users: <b>{len(users)}</b>", f"✨ New today: <b>{new_today}</b>", f"📨 Requests: <b>{total_requests}</b>"]
    if totals:
        lines += ["", "🗂 <b>By category</b>"] + [f"• {names.get(k, k)}: {v}" for k, v in sorted(totals.items(), key=lambda x: -x[1])]
    rows = []
    ranked = sorted(users.items(), key=lambda x: x[1].get("total_requests", 0), reverse=True)
    for rank, (uid, item) in enumerate(ranked, 1):
        name = html.escape(item.get("first_name") or "Unknown")
        username = f" @{html.escape(item['username'])}" if item.get("username") else ""
        last = item.get("last_interaction", "Unknown")
        rows.append(f"<blockquote>☆ User {rank}: {name}{username}</blockquote>\n♡ {item.get('total_requests', 0)} requests, last active: {html.escape(last)}\n<i>ID: {uid}</i>")
    pages, chunk, size = [], [], 0
    for row in rows:
        if size + len(row) > 3500:
            pages.append("\n\n".join(chunk)); chunk, size = [], 0
        chunk.append(row); size += len(row) + 2
    if chunk: pages.append("\n\n".join(chunk))
    return "\n".join(lines), pages


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """فقط برای ادمین؛ برای هر کس دیگری کاملاً سکوت می‌کند تا وجود دستور فاش نشود."""
    if not ADMIN_ID or update.effective_user.id != ADMIN_ID:
        return
    lang = user_language(update.effective_user.id)
    summary, pages = build_stats_report_en() if lang == "en" else build_stats_report()
    await update.effective_message.reply_text(summary, parse_mode=ParseMode.HTML)
    if not pages:
        return
    for i, page in enumerate(pages, start=1):
        header = (f"👤 <b>User List</b> | Page {i}/{len(pages)}\n\n" if lang == "en" else f"👤 <b>لیست کاربران</b> — صفحه {fa_num(i)}/{fa_num(len(pages))}\n\n")
        await update.effective_message.reply_text(header + page, parse_mode=ParseMode.HTML)


async def post_init(application: Application) -> None:
    # Telegram requires one global command language; Persian remains the default.
    # A per-chat English command menu is installed immediately after language selection.
    await application.bot.set_my_commands(commands_for("fa"))
    if ADMIN_ID:
        try:
            lang = language_for(ADMIN_ID)
            await application.bot.set_my_commands(
                commands_for(lang, admin=True), scope=BotCommandScopeChat(chat_id=ADMIN_ID),
            )
        except Exception:
            logger.warning("Could not configure the admin command menu")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("خطای کنترل‌نشده در ربات", exc_info=context.error)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    if not BOT_TOKEN:
        raise RuntimeError("متغیر محیطی BOT_TOKEN تنظیم نشده است.")

    application = Application.builder().bot(LocalizedBot(token=BOT_TOKEN)).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("language", start_command))
    application.add_handler(CommandHandler(["ai", "security", "crypto"], category_command))
    application.add_handler(CommandHandler("addchannel", add_channel_command))
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