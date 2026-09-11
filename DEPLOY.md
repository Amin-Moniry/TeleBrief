# 🚂 راهنمای Deploy روی Railway.app

## مراحل نصب:

### 1️⃣ ثبت نام در Railway
- برو به [railway.app](https://railway.app)
- با GitHub لاگین کن

### 2️⃣ ساخت پروژه جدید
- کلیک روی **New Project**
- انتخاب **Deploy from GitHub repo**
- مخزن `TeleBrief` رو انتخاب کن

### 3️⃣ تنظیم Environment Variables
در بخش **Variables** این موارد رو اضافه کن:

```
API_ID=your_api_id
API_HASH=your_api_hash
SESSION_STRING=your_session_string
BOT_TOKEN=your_bot_token
MY_CHAT_ID=your_chat_id
XKIRO_API_KEY=your_xkiro_api_key
API_BASE_URL=your_api_base_url
DEFAULT_MODEL=deepseek/deepseek-v4-pro
HOURS_WINDOW=12
```

### 4️⃣ Deploy
- Railway خودکار از `Procfile` استفاده می‌کنه
- Deploy شروع میشه و ربات 24/7 اجرا میشه

### 5️⃣ مشاهده Logs
- بخش **Deployments** → **View Logs**
- میتونی ببینی ربات چطور کار میکنه

---

## 🎯 سرویس‌های دیگه:

### Render.com
1. ثبت نام در [render.com](https://render.com)
2. New → Background Worker
3. Connect GitHub repo
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python command_bot.py`
6. اضافه کردن Environment Variables

### Fly.io
```bash
# نصب Fly CLI
curl -L https://fly.io/install.sh | sh

# لاگین
fly auth login

# ساخت و deploy
fly launch
fly secrets set API_ID=xxx API_HASH=xxx ...
fly deploy
```

---

## ⚠️ نکات مهم:

1. **حذف GitHub Actions برای command_bot**
   - فایل `.github/workflows/check-command.yml` رو حذف کن یا غیرفعال کن
   - چون حالا ربات روی سرور دائمی اجراست

2. **نگه داشتن daily.yml**
   - این workflow رو نگه دار برای ارسال گزارش روزانه خودکار

3. **پایش مصرف**
   - Railway: 500 ساعت/ماه رایگان
   - Render: 750 ساعت/ماه رایگان
   - یکی رو انتخاب کن که کافیه

---

## ✅ چک کردن اینکه کار میکنه:

1. ربات رو در تلگرام پیدا کن
2. `/start` بفرست
3. `/ai` یا `/security` رو امتحان کن
4. باید فوری جواب بده!

---

Made with ❤️
