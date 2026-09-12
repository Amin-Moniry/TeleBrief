<div align="center">

# 🤖 TeleBrief
### رصدخانه هوشمند تلگرام | خلاصه و تحلیل اخبار AI و امنیت سایبری با هوش مصنوعی

<p align="center">
  <a href="https://github.com/Amin-Moniry/TeleBrief">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=00B4D8&center=true&vCenter=true&random=false&width=650&lines=⚡+TeleBrief%3A+Next-Gen+Telegram+AI+Intelligence;🔍+رصد+هوشمند+اخبار+داغ+هوش+مصنوعی+و+امنیت;🛡+فیلتر+اسپم+و+تبلیغات+%7C+خلاصه+ناب+و+مستند;🚀+کمتر+اسکرول+کن%D8%8C+عمیق‌تر+و+سریع‌تر+باخبر+شو!" alt="TeleBrief Animated Typing Header" />
  </a>
</p>

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Telethon](https://img.shields.io/badge/Telethon-MTProto-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://github.com/LonamiWebs/Telethon)
[![PTB](https://img.shields.io/badge/PTB-v20.7-blue?style=for-the-badge&logo=telegram&logoColor=white)](https://python-telegram-bot.org/)
[![LLM Powered](https://img.shields.io/badge/LLM-DeepSeek%20%2F%20OpenAI-8A2BE2?style=for-the-badge&logo=openai&logoColor=white)](https://deepseek.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Amin-Moniry/TeleBrief?style=for-the-badge&color=gold)](https://github.com/Amin-Moniry/TeleBrief/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Amin-Moniry/TeleBrief?style=for-the-badge&color=orange)](https://github.com/Amin-Moniry/TeleBrief/network/members)

<br/>

<p align="center">
  <a href="https://t.me/telebriefdata_bot">
    <img src="https://img.shields.io/badge/🤖_امتحان_ربات_در_تلگرام-@telebriefdata__bot-0088cc?style=for-the-badge&logo=telegram&logoColor=white" height="38" />
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/Amin-Moniry/TeleBrief">
    <img src="https://img.shields.io/badge/⭐_ثبت_ستاره_در_گیت‌هاب-Star_Repo-FFB800?style=for-the-badge&logo=github&logoColor=black" height="38" />
  </a>
</p>

---

<p align="center">
  <b>«در دنیای بمباران اطلاعاتی، ارزش در نشنیدن نویزهاست.»</b><br/>
  <b>TeleBrief</b> ربات هوشمند تحلیلی است که صدها کانال تخصصی تلگرام را اسکن کرده، اخبار زرد، اسپم و تبلیغات را حذف می‌کند و با کمک مدل‌های زبانی پیشرفته (LLM)، پرمغزترین گزارش‌ها را همراه با نمره اهمیت، نکات کلیدی و ارجاع مستقیم به پیام اصلی به دست شما می‌رساند.
</p>

</div>

<br/>

## 📑 فهرست مطالب
- [🌟 چرا TeleBrief؟ (معضل و راه‌حل)](#-چرا-telebrief-معضل-و-راه‌حل)
- [✨ قابلیت‌های برجسته (Key Features)](#-قابلیت‌های-برجسته-key-features)
- [🔄 معماری و نحوه عملکرد (Pipeline Architecture)](#-معماری-و-نحوه-عملکرد-pipeline-architecture)
- [🖼 پیش‌نمایش خروجی و تجربه کاربری (UI & Showcase)](#-پیش‌نمایش-خروجی-و-تجربه-کاربری-ui--showcase)
- [📡 کانال‌های رصدشونده (Monitored Channels)](#-کانال‌های-رصدشونده-monitored-channels)
- [🎮 لیست دستورات ربات (Bot Commands)](#-لیست-دستورات-ربات-bot-commands)
- [⚙️ متغیرهای محیطی (Environment Variables)](#️-متغیرهای-محیطی-environment-variables)
- [🚀 راهنمای نصب و راه‌اندازی محلی (Quickstart)](#-راهنمای-نصب-و-راه‌اندازی-محلی-quickstart)
- [☁️ روش‌های استقرار و دیپلوی (Deployment)](#️-روش‌های-استقرار-و-دیپلوی-deployment)
- [🛠 تکنولوژی‌های استفاده‌شده (Tech Stack)](#-تکنولوژی‌های-استفاده‌شده-tech-stack)
- [👤 توسعه‌دهنده و راه‌های ارتباطی (Author)](#-توسعه‌دهنده-و-راه‌های-ارتباطی-author)
- [📜 مجوز (License)](#-مجوز-license)

---

## 🌟 چرا TeleBrief؟ (معضل و راه‌حل)

در کانال‌های تلگرامی حوزه تکنولوژی، روزانه هزاران پست منتشر می‌شود:
* ❌ پست‌های تکراری و فورواردهای مکرر یک خبر واحد
* ❌ تبلیغات رمزارزی، پکیج‌فروشی و تیترهای زرد کلیک‌بیت (Clickbait)
* ❌ اخبار کم‌اهمیت یا نامعتبر که وقت ارزشمند متخصص را تلف می‌کنند

### 💡 راهکار انقلابی TeleBrief:
1. **کرول سطح پایین با کلاینت واقعی (Telethon MTProto):** دسترسی به پیام‌ها حتی بدون نیاز به اینکه بات در کانال‌ها ادمین یا عضو باشد.
2. **فیلتراسیون هوش مصنوعی دو مرحله‌ای (Two-Stage AI Filter):**
   - **فاز غربال‌گری (Shortlisting):** خواندن دسته‌ای (Batching) پیام‌ها، پالایش اسپم و تولید نامزدهای اولیه.
   - **فاز ترکیب و رتبه‌بندی (Merge & Ranking):** ادغام پوشش‌های مشترک و نمره‌دهی سخت‌گیرانه بر اساس فاکتورهای واقعی (0 تا 100).
3. **فرمت مدرن و استاندارد تلگرام:** کارت‌های فوق‌العاده شکیل فارسی مجهز به Quoteهای بازشونده (`expandable`)، بولت‌پوینت‌های نکات کلیدی، توصیه‌های عملیاتی و لینک معتبر به مبدا خبر.

---

## ✨ قابلیت‌های برجسته (Key Features)

<table>
  <tr>
    <td width="50%">
      <h3>🧠 هوش مصنوعی دو سطحی (Deep Analysis)</h3>
      تحلیل توسط قوی‌ترین مدل‌های هوش مصنوعی تحلیلی (مانند DeepSeek V3/V4 و OpenAI). استخراج دلیل اهمیت رویداد، پیامدهای فنی و اکشن‌های پیشنهادی به زبان فارسی شیوا و اصیل.
    </td>
    <td width="50%">
      <h3>🔄 لودینگ داشبوردی متحرک (Live Animation)</h3>
      هنگام آماده‌سازی گزارش، ربات در تلگرام یک وضعیت متحرک زنده با فریم‌های اسپینر <code>⣾ ⣽ ⣻ ⢿</code> و مراحل کار (اتصال ➔ استخراج ➔ پاکسازی ➔ رتبه‌بندی) نمایش می‌دهد.
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>⏱ فیلتر زمانی کاملاً منعطف</h3>
      انتخاب بازه بررسی با دکمه‌های شیشه‌ای: ۶ ساعت، ۱۲ ساعت، ۲۴ ساعت، ۴۸ ساعت، ۷ روز، ۱۵ روز و حتی <b>بازه دلخواه دستی (به ساعت)</b>.
    </td>
    <td width="50%">
      <h3>📚 شخصی‌سازی و افزودن کانال‌های دلخواه</h3>
      کاربران علاوه بر کانال‌های مرجع سیستمی می‌توانند کانال‌های تخصصی موردنظر خود را نیز به ربات بسپارند تا در گزارش اختصاصی لحاظ شود.
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📑 صفحه‌بندی هوشمند خبرها (Pagination)</h3>
      جلوگیری از ارسال رگباری صدها پیام؛ اخبار بر اساس رتبه اهمیت ۱۰ تا ۱۰ تا با دکمه <i>«مشاهده ۱۰ خبر بعدی»</i> در اختیار شما قرار می‌گیرد.
    </td>
    <td width="50%">
      <h3>🛡 مکانیزم تاب‌آوری و فال‌بک (Resilience)</h3>
      در صورت قطعی موقت سرویس LLM، سیستم از کار نمی‌افتد! یک موتور Fallback هوشمند پیام‌های پرمخاطب (بر اساس ترکیب بازدید و فوروارد) را استخراج کرده و به کاربر ارائه می‌دهد.
    </td>
  </tr>
</table>

---

## 🔄 معماری و نحوه عملکرد (Pipeline Architecture)

جریان داده در **TeleBrief** بر اساس معماری دقیق خط لوله پردازشی طراحی شده است:

```mermaid
flowchart TD
    subgraph Sources["📡 لایه منابع تلگرام"]
        A1[کانال‌های هوش مصنوعی]
        A2[کانال‌های امنیت سایبری]
        A3[کانال‌های شخصی کاربر]
    end

    subgraph Harvester["⚙️ لایه خزش و جمع‌آوری (Telethon)"]
        B[TelegramClient MTProto]
        C[فیلتر بازه زمانی: 6h/12h/24h/Custom]
        D[پکیج‌بندی و دسته‌بندی دسته‌ای (Batching Engine)]
    end

    subgraph Intelligence["🧠 موتور پالایش و هوش مصنوعی"]
        E[مرحله اول: غربال‌گری عمیق & حذف نویز / اسپم]
        F[مرحله دوم: ادغام رویدادهای تکراری & امتیازدهی 0-100]
        G[اعتبارسنجی منابع واقعی و پاکسازی HTML]
    end

    subgraph Delivery["🚀 لایه توزیع و تعامل"]
        H[ربات تعاملی تلگرام (python-telegram-bot)]
        I[گزارش‌دهی خودکار زمان‌بندی‌شده (GitHub Actions)]
        J[کارت‌های استاندارد تلگرام با لینک منبع]
    end

    Sources --> B
    B --> C --> D
    D --> E
    E --> F
    F --> G
    G --> H & I
    H & I --> J
```

---

## 🖼 پیش‌نمایش خروجی و تجربه کاربری (UI & Showcase)

خروجی‌های ارسالی ربات با رعایت بالاترین اصول زیبایی‌شناسی و ساختار بصری مدرن تلگرام فرمت می‌شوند:

```text
🗞 گزارش تحلیلی TeleBrief
بازه بررسی: 1405/06/22 06:00 تا 1405/06/22 18:00
پیام‌های بررسی‌شده: 248 پیام از 10 کانال فعال

🤖 1. گزارش: انتشار مدل متن‌باز چندوجهی DeepSeek-VL2
اهمیت: 96/100

خلاصه خبر:
تیم دیپ‌سیک از مدل ویژن پیشرفته خود رونمایی کرد که در بنچمارک‌های
بینایی ماشین و درک اسناد، مدل‌های اختصاصی تجاری را با هزینه بسیار کمتر به چالش می‌کشد.

دلیل اهمیت:
کاهش چشمگیر هزینه پردازش تصاویر و نمودارها برای توسعه‌دهندگان مستقل.
نکات کلیدی:
• سازگاری کامل با اکوسیستم HuggingFace
• پشتیبانی پیشرفته از OCR زبان‌های ترکیبی
• لایسنس تجاری مجاز برای کسب‌وکارها

اقدام‌های پیشنهادی:
• بررسی ریپو و پیاده‌سازی آزمایشی روی سرور لوکال

📎 منبع مستقیم
مشاهده پیام @digiai | مشاهده پیام @Hugging_face_news

𝐉𝐎𝐈𝐍 ➣ TeleBrief
```

---

## 📡 کانال‌های رصدشونده (Monitored Channels)

ربات به صورت پیش‌فرض کانال‌های تراز اول و مرجع را مورد رصد قرار می‌دهد:

<div align="center">

| 🤖 حوزه هوش مصنوعی (AI) | 🛡 حوزه امنیت سایبری (Security) |
|:---:|:---:|
| [@digiai](https://t.me/digiai) | [@cybersecurityexperts](https://t.me/cybersecurityexperts) |
| [@RoidBest](https://t.me/RoidBest) | [@thehackernews](https://t.me/thehackernews) |
| [@Farda_Ai](https://t.me/Farda_Ai) | [@cibsecurity](https://t.me/cibsecurity) |
| [@Lumosel](https://t.me/Lumosel) | [@Cyber_Security_Channel](https://t.me/Cyber_Security_Channel) |
| [@asrnovin_ir](https://t.me/asrnovin_ir) | [@androidMalware](https://t.me/androidMalware) |
| [@perplexity](https://t.me/perplexity) | [@cloudandcybersecurity](https://t.me/cloudandcybersecurity) |
| [@cryptoquant_official](https://t.me/cryptoquant_official) | *(امکان افزودن کانال دلخواه توسط کاربر)* |
| [@Hugging_face_news](https://t.me/Hugging_face_news) | *(پشتیبانی از هر دو کانال فارسی و انگلیسی)* |

</div>

---

## 🎮 لیست دستورات ربات (Bot Commands)

| دستور | توضیح عملکرد |
|:---|:---|
| `/start` | شروع به کار، ثبت کاربر و نمایش منوی اصلی ربات |
| `/menu` | باز کردن سریع داشبورد دکمه‌ها و دسته‌بندی‌ها |
| `/ai` | دریافت مستقیم خلاصه‌اخبار ۱۲ ساعت گذشته هوش مصنوعی |
| `/security` | دریافت مستقیم خلاصه‌اخبار ۱۲ ساعت گذشته امنیت سایبری |
| `/todaynews` | دسترسی سریع به منوی انتخاب دسته‌بندی |
| `/help` | مشاهده راهنمای جامع استفاده از قابلیت‌ها |
| `/about` | درباره اهداف و نحوه کارکرد TeleBrief |

---

## ⚙️ متغیرهای محیطی (Environment Variables)

برای راه‌اندازی پروژه، تنظیم متغیرهای زیر (در فایل `.env` یا Secrets پلتفرم) الزامی است:

| کلید تنظیمات | نمونه مقدار | توضیحات |
|:---|:---|:---|
| `API_ID` | `1234567` | شناسه اختصاصی API تلگرام (از [my.telegram.org](https://my.telegram.org)) |
| `API_HASH` | `a1b2c3d4e5...` | کلید هش API تلگرام |
| `SESSION_STRING` | `1BJWap...` | رشته اتصال نشست کاربری Telethon (بدون نیاز به لاگین مجدد) |
| `BOT_TOKEN` | `7123456:AAF...` | توکن رسمی ربات تلگرام دریافتی از [@BotFather](https://t.me/BotFather) |
| `MY_CHAT_ID` | `987654321` | چت‌آیدی عددی شما برای دریافت لاگ‌ها و گزارش‌های ادمین |
| `XKIRO_API_KEY` | `sk-...` | کلید دسترسی به API مدل هوش مصنوعی |
| `API_BASE_URL` | `https://api.deepseek.com/v1` | آدرس پایه API سازگار با OpenAI |
| `DEFAULT_MODEL` | `deepseek/deepseek-v4-pro` | مدل انتخابی برای تحلیل و رتبه‌بندی |
| `HOURS_WINDOW` | `12` | بازه زمانی پیش‌فرض بررسی اخبار (ساعت) |

---

## 🚀 راهنمای نصب و راه‌اندازی محلی (Quickstart)

### ۱. پیش‌نیازها
* پایتون نسخه `3.11` یا بالاتر
* حساب کاربری تلگرام + ساخت ربات در BotFather
* دسترسی به اینترنت پایدار و بدون تحریم تلگرام/OpenAI

### ۲. کلون و راه‌اندازی مخزن
```bash
# کلون کردن ریپازیتوری
git clone https://github.com/Amin-Moniry/TeleBrief.git
cd TeleBrief

# ایجاد محیط مجازی (Virtual Environment)
python -m venv venv

# فعال‌سازی محیط مجازی
# در ویندوز:
venv\Scripts\activate
# در لینوکس یا مک:
source venv/bin/activate

# نصب وابستگی‌ها
pip install -r requirements.txt
```

### ۳. دریافت SESSION_STRING تلگرام
برای اتصال Telethon، اسکریپت تک‌خطی زیر را اجرا کنید:
```python
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = 1234567       # جایگزین کنید
API_HASH = "your_hash" # جایگزین کنید

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\nSESSION STRING شما:\n")
    print(client.session.save())
```

### ۴. اجرای ربات
```bash
# اجرای ربات تعاملی (Interactive Mode)
python command_bot.py

# یا اجرای تک‌نوبته موتور خلاصه‌ساز (Digest Core)
python main.py
```

---

## ☁️ روش‌های استقرار و دیپلوی (Deployment)

<details>
<summary><b>🔹 روش ۱: اجرای رایگان ابری ۲۴/۷ (Railway / Render / Fly.io) - پیشنهادی</b></summary>
<br/>

این پروژه دارای فایل آماده `Procfile` با محتوای `worker: python command_bot.py` است.
1. مخزن خود را به **Railway** یا **Render** متصل کنید.
2. نوع سرویس را بر روی **Background Worker** تنظیم نمایید.
3. متغیرهای محیطی (Environment Variables) را در پنل وارد کنید.
4. پروژه به صورت خودکار بیلد و به صورت ۲۴ ساعته اجرا می‌شود.
</details>

<details>
<summary><b>🔹 روش ۲: اجرای خودکار با GitHub Actions (کاملاً رایگان و بدون سرور)</b></summary>
<br/>

اگر نیازی به حالت ربات تعاملی دکمه‌ای ندارید و صرفاً مایلید **هر ۱۲ ساعت یکبار** گزارش کامل در پیوی یا کانال تلگرام شما ارسال شود:
1. در ریپوی گیت‌هاب به بخش **Settings > Secrets and variables > Actions** بروید.
2. تمامی متغیرهای جدول بالا را به عنوان **Repository Secrets** اضافه کنید.
3. ورک‌فلو `.github/workflows/daily.yml` به طور خودکار طبق برنامه زمانی (Cron) هر ۱۲ ساعت یکبار اجرا شده و گزارش جامع را ارسال می‌کند.
</details>

<details>
<summary><b>🔹 روش ۳: سرویس لینوکس (Systemd Daemon روی VPS)</b></summary>
<br/>

برای اجرای مداوم روی سرور اختصاصی لینوکسی خود، یک سرویس بسازید:
```ini
# /etc/systemd/system/telebrief.service
[Unit]
Description=TeleBrief Telegram Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/TeleBrief
EnvironmentFile=/root/TeleBrief/.env
ExecStart=/root/TeleBrief/venv/bin/python command_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
سپس فعال‌سازی کنید:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now telebrief
sudo systemctl status telebrief
```
</details>

<details>
<summary><b>🔹 روش ۴: اجرای ایزوله با داکر (Docker & Docker Compose)</b></summary>
<br/>

اجرای تک‌دستوری با داکر:
```bash
docker run -d --name telebrief \
  --env-file .env \
  --restart unless-stopped \
  python:3.11-slim sh -c "pip install telethon requests python-telegram-bot==20.7 && python command_bot.py"
```
</details>

---

## 🛠 تکنولوژی‌های استفاده‌شده (Tech Stack)

<div align="center">

| مولفه | تکنولوژی | نقش در سامانه |
|:---:|:---:|:---|
| **Language** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) | زبان اصلی پردازش ناهمگام و منطق برنامه |
| **MTProto Scraper** | ![Telethon](https://img.shields.io/badge/Telethon-2CA5E0?style=flat-square&logo=telegram&logoColor=white) | خواندن و مانیتورینگ امن پیام‌های کانال‌ها بدون محدودیت بات |
| **Bot Framework** | ![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-2CA5E0?style=flat-square&logo=telegram&logoColor=white) | هندلینگ دستورات، منوهای شیشه‌ای و انیمیشن لودینگ |
| **Reasoning Engine** | ![DeepSeek](https://img.shields.io/badge/DeepSeek_AI-8A2BE2?style=flat-square&logo=openai&logoColor=white) | تحلیل هوشمند متن، سنجش اعتبار، غربالگری و رتبه‌بندی |
| **Automation** | ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white) | گزارش‌گیری زمان‌بندی‌شده بدون نیاز به سرور |
| **State Storage** | ![JSON](https://img.shields.io/badge/JSON_Store-000000?style=flat-square&logo=json&logoColor=white) | ذخیره مطمئن و اتمیک (Atomic) تنظیمات کاربران |

</div>

---

## 🤝 مشارکت در توسعه (Contributing)

از هرگونه مشارکت، پیشنهاد قابلیت جدید یا گزارش باگ صمیمانه استقبال می‌شود!
1. مخزن را فورک کنید (**Fork**).
2. یک برنچ جدید برای قابلیت خود بسازید: `git checkout -b feature/AmazingFeature`
3. تغییرات خود را کامیت کنید: `git commit -m 'feat: Add some AmazingFeature'`
4. برنچ را پوش کنید: `git push origin feature/AmazingFeature`
5. یک **Pull Request** ارسال کنید.

---

## 👤 توسعه‌دهنده و راه‌های ارتباطی (Author)

<div align="center">

توسعه داده شده با ❤️ و ☕ توسط **امین منیری (Amin Moniry)**

<p align="center">
  <a href="https://github.com/Amin-Moniry">
    <img src="https://img.shields.io/badge/GitHub-Amin--Moniry-181717?style=for-the-badge&logo=github&logoColor=white" />
  </a>
  &nbsp;&nbsp;
  <a href="https://t.me/telebriefdata_bot">
    <img src="https://img.shields.io/badge/Telegram_Bot-@telebriefdata__bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" />
  </a>
</p>

⭐ **اگر این پروژه برایتان کاربردی بود، خوشحال می‌شویم با دادن یک ستاره (Star) در گیت‌هاب از آن حمایت کنید!**

</div>

---

## 📜 مجوز (License)

این پروژه تحت مجوز **MIT** منتشر شده است. برای اطلاعات بیشتر فایل [LICENSE](LICENSE) را مشاهده کنید.
