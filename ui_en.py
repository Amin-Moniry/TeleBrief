"""English UI translation layer for TeleBrief.

The bot's original Persian copy stays untouched in command_bot.py.  This module
translates every finalized UI message and keyboard label for English users,
including dynamic counters and progress messages.
"""
import re

EXACT = {
    "🇮🇷 فارسی": "🇮🇷 فارسی",
    "6 ساعت": "6 hours", "12 ساعت": "12 hours", "24 ساعت": "24 hours",
    "48 ساعت": "48 hours", "7 روز": "7 days", "15 روز / 360 ساعت": "15 days / 360 hours",
    "❌ لغو گزارش": "❌ Cancel report",
    "☑️ عضویت در کانال": "☑️ Join the channel",
    "✅ عضو شدم، بررسی کن": "✅ I joined, check now",
    "🌀 افزودن کانال": "🌀 Add Channel",
    "🌀 حذف یک کانال": "🌀 Remove a Channel",
    "🌀 پاک‌کردن همه": "🌀 Clear All",
    "🌀 منوی اصلی": "🌀 Main Menu",
    "🌀 هوش مصنوعی": "🌀 Artificial Intelligence",
    "🌀 امنیت شبکه": "🌀 Cybersecurity",
    "🌀 دلار و طلا": "🌀 USD & Gold",
    "🌀 کریپتو و جنگ": "🌀 Crypto & Geopolitics",
    "🌀 کانال‌های من": "🌀 My Channels",
    "🌀 راهنما": "🌀 Help",
    "🌀 درباره ربات": "🌀 About",
    "۶ ساعت": "6 hours", "۱۲ ساعت": "12 hours", "24 ساعت": "24 hours",
    "۴۸ ساعت": "48 hours", "۷ روز": "7 days", "15 روز / 360 ساعت": "15 days / 360 hours",
    "🌀 بازه دلخواه": "🌀 Custom Range", "🌀 بازگشت": "🌀 Back",
    "🌀 بازگشت به منوی اصلی": "🌀 Back to Main Menu",
    "🌀 بله، پاک کن": "🌀 Yes, clear all", "🌀 انصراف": "🌀 Cancel",
    "گزارش قبلی هنوز آماده نشده.": "Your previous report is still being prepared.",
    "گزارش قبلی هنوز در حال آماده‌شدن است.": "Your previous report is still being prepared.",
    "لیست شما خالی است.": "Your channel list is empty.",
    "دکمه نامعتبر است.": "This button is invalid.",
    "این گزارش متعلق به شما نیست.": "This report belongs to another user.",
    "در حال لغو گزارش...": "Canceling the report...",
    "این گزارش دیگر در جریان نیست.": "This report is no longer running.",
    "✅ عضویت تایید شد!": "✅ Membership confirmed!",
    "هنوز عضو کانال نشدی 🙁": "You have not joined the channel yet 🙁",
    "فرمت درست نیست. @channel یا لینک عمومی t.me/channel را بفرست.": "Invalid format. Send @channel or a public t.me/channel link.",
    "این کانال عمومی پیدا نشد یا ربات به آن دسترسی ندارد؛ نام را دوباره بررسی کن.": "I could not find or access that public channel. Check the username and try again.",
    "این کانال در لیست شما پیدا نشد. نام دقیق‌تری بفرست یا از منو انصراف بده.": "That channel is not in your list. Send the exact username or cancel from the menu.",
    "🗑 همه کانال‌های شخصی شما حذف شدند.": "🗑 All personal channels were removed.",
}

REPLACEMENTS = [
    (r"آتیش بی خاکستر", "Atish Bi Khakestar"),
    (r"سلام (.+?) عزیز، خوش اومدی!", r"Hi \1, welcome!"),
    (r"سلام (.+?) عزیز 🌹", r"Hi \1 🌹"),
    (r"دوست عزیز", "there"),
    (r"خوشحالیم که به TeleBrief سر زدید\. برای استفاده از امکانات ربات، لازم است ابتدا عضو کانال زیر شوید:", "Welcome to TeleBrief. To use the bot, please join the channel below first:"),
    (r"پس از عضویت، کافی‌ست روی دکمه زیر بزنید تا بلافاصله دسترسی کامل برایتان فعال شود\.", "After joining, tap the button below to unlock full access."),
    (r"من <b>TeleBrief</b> هستم؛.*?در اختیارتان قرار می‌دهم\.</blockquote>", "I’m <b>TeleBrief</b>, an intelligence assistant for AI, cybersecurity, USD and gold, crypto, and geopolitics.\n\n<blockquote>I remove noise and duplicates, then deliver concise ranked reports with direct source links.</blockquote>"),
    (r"در خدمت شما هستم ، از طریق دکمه‌های زیر می‌توانید از امکانات ربات استفاده کنید :", "Choose an option below to get started:"),
    (r"چه گزارشی می‌خوای؟", "What report do you want?"),
    (r"یکی از حوزه‌های خبری زیر را انتخاب کن تا مهم‌ترین و تازه‌ترین یافته‌های همان حوزه برایت آماده شود\.", "Choose a category and I’ll prepare its most important recent findings."),
    (r"دسته موردنظرت را از دکمه‌های زیر انتخاب کن", "Select a category below"),
    (r"چند ساعت اخیر بررسی شود؟", "How far back should I scan?"),
    (r"بازه آماده را انتخاب کن یا عدد دلخواهت را بنویس\.", "Choose a preset or enter a custom number of hours."),
    (r"در حال دریافت آخرین نرخ", "Fetching the latest rates"),
    (r"در حال شروع بررسی", "Starting the scan"),
    (r"چند نفر دیگر هم‌زمان درخواست دارند؛ ربات خراب نیست، فقط کمی صف دارد\.", "Other reports are queued. The bot is working, it may just take a little longer."),
    (r"فقط یک عدد بفرست؛ مثلاً <b>24</b>\.", "Send a number only, for example <b>24</b>."),
    (r"بازه باید بین <b>1 تا 720 ساعت</b> باشد\.\nمثلاً برای 15 روز: <b>360</b>\.", "The range must be between <b>1 and 720 hours</b>.\nFor 15 days, send <b>360</b>."),
    (r"ساعت دلخواه را بفرست", "Send a custom number of hours"),
    (r"یک عدد بین 1 تا 720 بنویس؛ مثلاً <b>360</b>\.\nبرای 15 روز، عدد <b>360</b> را ارسال کن\.", "Enter a number from 1 to 720, for example <b>360</b>.\nFor 15 days, send <b>360</b>."),
    (r"کانال‌های شخصی من", "My Personal Channels"),
    (r"این کانال‌ها علاوه بر منابع پیش‌فرض ربات بررسی می‌شوند و در گزارش‌های «هوش مصنوعی» و «امنیت شبکه» لحاظ خواهند شد\.", "These channels are scanned alongside the default sources in AI and cybersecurity reports."),
    (r"ظرفیت استفاده‌شده: <b>(\d+)</b> از <b>(\d+)</b> کانال", r"Capacity used: <b>\1</b> of <b>\2</b> channels"),
    (r"ظرفیت استفاده‌شده: (\d+) از (\d+) کانال", r"Capacity used: \1 of \2 channels"),
    (r"هنوز کانالی اضافه نشده است\.", "You have not added any channels yet."),
    (r"حذف کانال", "Remove a Channel"),
    (r"نام یکی از کانال‌های زیر را بفرست \(با یا بدون @\) تا از لیست حذف شود:", "Send one channel username from the list below, with or without @:"),
    (r"افزودن کانال", "Add a Channel"),
    (r"آی‌دی عمومی کانال یا لینک آن را بفرست؛ مثال: <b>@thehackernews</b>", "Send a public channel username or link, for example <b>@thehackernews</b>."),
    (r"ظرفیت باقی‌مانده: (\d+) کانال", r"Remaining capacity: \1 channels"),
    (r"این کانال \(@(.+?)\) از قبل در لیست شماست\.", r"@\1 is already in your channel list."),
    (r"ظرفیت شما تکمیل شده است \(حداکثر (\d+) کانال\)\. برای افزودن کانال جدید، ابتدا یکی را حذف کنید\.", r"Your list is full (maximum \1 channels). Remove one before adding another."),
    (r"✅ کانال @(.+?) اضافه شد\.", r"✅ Added @\1."),
    (r"🗑 کانال @(.+?) حذف شد\.", r"🗑 Removed @\1."),
    (r"پاک‌کردن همه کانال‌ها", "Clear All Channels"),
    (r"این کار همه کانال‌های شخصی شما را حذف می‌کند و قابل بازگشت نیست\. مطمئن هستید؟", "This permanently removes every personal channel from your list. Continue?"),
    (r"گزارش هوشمند", "Intelligence Report"),
    (r"بخش: هوش مصنوعی", "Category: Artificial Intelligence"),
    (r"بخش: امنیت شبکه", "Category: Cybersecurity"),
    (r"بخش: دلار و طلا", "Category: USD & Gold"),
    (r"بخش: کریپتو و جنگ", "Category: Crypto & Geopolitics"),
    (r"بازه زمانی: (\d+) ساعت اخیر", r"Time range: last \1 hours"),
    (r"مرحله فعلی:", "Current stage:"), (r"پیشرفت:", "Progress:"),
    (r"اتصال به منابع معتبر", "Connecting to trusted sources"),
    (r"استخراج پیام‌های مهم", "Extracting important messages"),
    (r"حذف تبلیغات و موارد تکراری", "Removing ads and duplicates"),
    (r"رتبه‌بندی نهایی خبرها", "Ranking the final stories"),
    (r"اتصال به کانال‌های ارز و طلا", "Connecting to currency and gold channels"),
    (r"خواندن آخرین پیام‌ها", "Reading the latest messages"),
    (r"استخراج نرخ دلار و طلا", "Extracting USD and gold rates"),
    (r"انتخاب تازه‌ترین به‌روزرسانی", "Selecting the freshest update"),
    (r"اتصال به کانال‌های بازار", "Connecting to market channels"),
    (r"جمع‌آوری اخبار رمزارز و جنگ", "Collecting crypto and geopolitical news"),
    (r"تفکیک نکات مهم از حاشیه", "Separating signal from noise"),
    (r"نوشتن گزارش نهایی", "Writing the final report"),
    (r"در حال بررسی دقیق پیام‌ها هستم؛ موارد ارزشمند جدا می‌شوند\.", "I’m reviewing every message and separating signal from noise."),
    (r"جست‌وجوی عمیق هوش مصنوعی", "Deep AI Scan"),
    (r"جست‌وجوی عمیق امنیت شبکه", "Deep Cybersecurity Scan"),
    (r"در حال خواندن تمام کانال‌ها و تحلیل پیام‌های (\d+) ساعت اخیر", r"Reading every channel and analyzing the last \1 hours"),
    (r"بازه انتخاب‌شده: (\d+) ساعت", r"Selected range: \1 hours"),
    (r"تبلیغات حذف، خبرهای مشابه ادغام و همه موارد مهم رتبه‌بندی می‌شوند\.", "Ads are removed, related stories are merged, and every important item is ranked."),
    (r"وضعیت کانال‌ها: هر (\d+) کانال پیمایش شد؛ (\d+) کانال در این بازه پیام داشت\.", r"Channel status: scanned all \1 channels; \2 had messages in this range."),
    (r"خبر مهمی پیدا نشد", "No important stories found"),
    (r"تمام پیام‌های این بازه بررسی شدند\.", "Every message in this range was checked."),
    (r"گزارش لغو شد", "Report canceled"),
    (r"هر وقت خواستی از منو دوباره درخواست بده\.", "Request a new report from the menu anytime."),
    (r"سرویس تحلیل هوش مصنوعی پاسخ نمی‌دهد", "The AI analysis service is not responding"),
    (r"پیام‌ها دریافت شدند، اما سرویس مدل بعد از چند تلاش خطای موقت داد؛ برای جلوگیری از گزارش خام یا ساختگی، چیزی منتشر نشد\.", "Messages were collected, but the model failed after several attempts. Nothing raw or fabricated was published."),
    (r"پیام‌ها دریافت شدند، اما سرویس مدل بعد از چند تلاش خطای موقت داد\.", "Messages were collected, but the model failed after several attempts."),
    (r"ساخت گزارش کامل نشد", "The report could not be completed"),
    (r"دریافت نرخ دلار و طلا کامل نشد", "USD and gold rates could not be retrieved"),
    (r"چند دقیقه دیگر دوباره امتحان کن\.", "Please try again in a few minutes."),
    (r"بررسی عمیق بازار کریپتو و جنگ", "Deep Crypto and Geopolitical Market Scan"),
    (r"در حال خواندن کانال‌های بازار و تحلیل پیام‌های (\d+) ساعت اخیر", r"Reading market channels and analyzing the last \1 hours"),
    (r"وضعیت کلی بازار و ریسک‌های جنگ/ژئوپلیتیک مؤثر بر آن جمع‌بندی می‌شود\.", "The report summarizes market conditions and relevant geopolitical risks."),
    (r"نکته منبع‌دار مجزایی پیدا نشد", "No separate sourced highlights were found"),
    (r"وضعیت کلی بازار در پیام بالا آمد\.", "The market overview is shown above."),
    (r"این گزارش منقضی شده", "This report has expired"),
    (r"از منو گزارش تازه بگیر\.", "Request a fresh report from the menu."),
    (r"در حال ارسال 10 خبر بعدی", "Sending the next 10 stories"),
    (r"در حال ارسال 10 نکته بعدی", "Sending the next 10 highlights"),
    (r"(\d+) خبر دیگر ارسال شد", r"Sent \1 more stories"),
    (r"(\d+) نکته دیگر ارسال شد", r"Sent \1 more highlights"),
    (r"هنوز (\d+) خبر مهم باقی مانده\.", r"\1 important stories remain."),
    (r"هنوز (\d+) نکته مهم باقی مانده\.", r"\1 important highlights remain."),
    (r"همه خبرهای مهم(?: این بازه)? ارسال شدند\.", "All important stories were sent."),
    (r"همهٔ? نکته‌های مهم بازار رمز ارز ارسال شدند\.", "All important market highlights were sent."),
    (r"مشاهده خبرهای بعدی \((\d+) تا از (\d+) خبر باقی‌مانده\) 🌀", r"View next stories (\1 of \2 remaining) 🌀"),
    (r"مشاهده نکته‌های بعدی \((\d+) تا از (\d+) نکته باقی‌مانده\) 🌀", r"View next highlights (\1 of \2 remaining) 🌀"),
]

PERSIAN = re.compile(r"[\u0600-\u06ff]")

def translate(text: str) -> str:
    if not text or not PERSIAN.search(text):
        return text
    if text.startswith("🌐 <b>زبان خود را انتخاب کنید | Choose your language</b>") or text == "🇮🇷 فارسی":
        return text
    clean = text.replace("\u200f", "").replace("\u200e", "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    if clean.startswith("📖 <b>راهنمای TeleBrief</b>"):
        return "📖 <b>TeleBrief Help</b>\n\nChoose a category and time range. The bot scans every message, removes low-value content, merges related stories, and ranks the results.\n\n<blockquote>USD & Gold returns the freshest trusted rates. Crypto & Geopolitics builds a market overview plus sourced highlights.</blockquote>\n\n<b>Commands</b>\n/start - choose language and open the main menu\n/menu - open the category menu\n/ai - AI report\n/security - cybersecurity report\n/crypto - crypto and geopolitical risk report\n/addchannel - add a personal channel\n/price - latest USD and gold rates\n/help - usage guide\n/about - about TeleBrief\n/language - change language\n\n<blockquote>Use each source link to open the original Telegram message.</blockquote>"
    if clean.startswith("ℹ️ <b>درباره</b>"):
        return "ℹ️ <b>About TeleBrief</b>\n\nAn analytical intelligence feed for <b>artificial intelligence</b>, <b>cybersecurity</b>, <b>USD and gold</b>, and <b>crypto and geopolitics</b>.\n\n<blockquote>Scroll less. Know more.</blockquote>"
    if clean.startswith("👋 <b>سلام "):
        name = re.search(r"👋 <b>سلام (.+?) عزیز", clean)
        who = name.group(1) if name else "there"
        return f"👋 <b>Hi {who}, welcome!</b>\n\nI’m <b>TeleBrief</b>, an intelligence assistant for AI, cybersecurity, USD and gold, crypto, and geopolitics.\n\n<blockquote>I identify high-value updates, remove noise and duplicates, then deliver concise ranked reports with direct source links.</blockquote>\n\nChoose an option below to get started:"
    if "خبر اول از مجموع" in clean:
        nums = re.findall(r"\d+", clean)
        if len(nums) >= 2:
            remaining = int(nums[1]) - int(nums[0])
            tail = f"{remaining} important stories remain." if remaining else "All important stories were sent."
            return f"✅ <b>Sent the first {nums[0]} of {nums[1]} stories</b>\n\n{tail}"
    if "نکته اول از مجموع" in clean:
        nums = re.findall(r"\d+", clean.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")))
        if len(nums) >= 2:
            remaining = int(nums[1]) - int(nums[0])
            tail = f"{remaining} important highlights remain." if remaining else "All important market highlights were sent."
            return f"✅ <b>Sent the first {nums[0]} of {nums[1]} highlights</b>\n\n{tail}"
    text = clean
    text = EXACT.get(text, text).replace("\u200f", "").replace("\u200e", "")
    for pattern, replacement in REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.S)
    # Safety net: English users must never receive a partially Persian UI.
    if PERSIAN.search(text):
        return "⚠️ <b>This message is unavailable in English.</b>\n\nPlease return to the main menu and try again."
    return text
