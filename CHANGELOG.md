# 📋 خلاصه تغییرات TeleBrief v2.0

## ✨ ویژگی‌های جدید

### 1️⃣ دو دسته خبری
- **🤖 هوش مصنوعی**: 10 کانال (digiai, RoidBest, Farda_Ai, Lumosel, asrnovin_ir, perplexity, cryptoquant_official, hiaimediaen, Hugging_face_news, samiotech)
- **🔒 امنیت سایبری**: 6 کانال (cybersecurityexperts, thehackernews, cibsecurity, Cyber_Security_Channel, androidMalware, cloudandcybersecurity)

### 2️⃣ گزارش‌دهی هوشمند
- ✅ نمایش تعداد پیام‌های بررسی شده
- ✅ اگر خبر خاصی پیدا نشد → خلاصه کلی از محتوای روز با AI
- ✅ لینک مستقیم به هر پیام
- ✅ دسته‌بندی اخبار (خبر / دیتا / ابزار / آموزش / هشدار)

### 3️⃣ ربات 24/7 با دستورات مستقیم
- `/ai` - اخبار هوش مصنوعی
- `/security` - اخبار امنیت سایبری
- `/start` - خوش‌آمدگویی (فقط برای کاربران جدید)
- `/help` - راهنما
- `/todaynews` - سازگاری با نسخه قبل

## 🔧 تغییرات فنی

### فایل‌های تغییر یافته:

1. **digest_core.py**
   - اضافه شدن `SECURITY_CHANNELS` و `AI_CHANNELS`
   - تابع `fetch_recent_messages()` حالا پارامتر `channels` می‌گیره
   - تابع `build_prompt()` حالا پارامتر `category` می‌گیره
   - تابع جدید `get_daily_summary()` برای خلاصه کلی روز
   - تابع `send_digest()` حالا آمار و خلاصه نشون میده
   - تابع `run_digest()` حالا `category` می‌گیره

2. **command_bot.py**
   - تغییر از "run once" به "polling mode" (24/7)
   - استفاده از event handlers بجای manual message checking
   - پشتیبانی از دستورات `/ai` و `/security`

3. **Procfile** (جدید)
   - برای deploy روی Railway/Render/Heroku

4. **runtime.txt** (جدید)
   - مشخص کردن Python 3.11

5. **DEPLOY.md** (جدید)
   - راهنمای کامل deploy روی سرویس‌های رایگان

6. **README.md**
   - آپدیت شده با دستورات جدید
   - اضافه شدن بخش deploy

### فایل‌های حذف شده:

- `.github/workflows/check-command.yml` → غیرفعال شد (تبدیل به `.disabled`)

### فایل‌های بدون تغییر:

- `.github/workflows/daily.yml` - همچنان برای ارسال گزارش روزانه کار می‌کنه
- `main.py` - بدون تغییر
- `requirements.txt` - بدون تغییر

## 🚀 مراحل Deploy

### گزینه 1: Railway.app (پیشنهادی)
1. ثبت نام در railway.app
2. Connect GitHub repo
3. اضافه کردن Environment Variables
4. Deploy خودکار شروع میشه

### گزینه 2: Render.com
1. ثبت نام در render.com
2. New Background Worker
3. Connect GitHub repo
4. تنظیم Environment Variables
5. Deploy

### گزینه 3: Fly.io
```bash
fly launch
fly secrets set API_ID=xxx API_HASH=xxx ...
fly deploy
```

## 📊 مقایسه قبل و بعد

### قبل:
❌ فقط یک دسته (امنیت)
❌ پیام "پیام مهمی پیدا نشد" بدون توضیح
❌ نیاز به GitHub Actions هر 5 دقیقه
❌ چندین بار پیام سلام
❌ بدون آمار

### بعد:
✅ دو دسته (AI + Security)
✅ خلاصه کلی از محتوای روز
✅ ربات 24/7 روی سرور رایگان
✅ فقط یکبار پیام سلام
✅ نمایش تعداد پیام‌های بررسی شده

## 🎯 نتیجه

ربات حالا:
- حرفه‌ای‌تر
- سریع‌تر (پاسخ فوری)
- کامل‌تر (خلاصه روزانه)
- مقیاس‌پذیرتر (چند کاربر همزمان)

---

تاریخ: 2026-09-11
نسخه: 2.0
