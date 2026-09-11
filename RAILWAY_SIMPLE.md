# 🚂 راهنمای ساده Deploy روی Railway

## روش پیشنهادی: Deploy مستقیم از Railway

این ساده‌ترین روشه و نیازی به GitHub Actions پیچیده نیست!

---

## مرحله 1️⃣: ساخت پروژه در Railway

1. برو به [railway.app](https://railway.app)
2. Sign in with GitHub
3. **New Project** → **Deploy from GitHub repo**
4. مخزن `TeleBrief` رو انتخاب کن
5. Railway خودکار شروع به deploy می‌کنه

---

## مرحله 2️⃣: تنظیم Environment Variables

در Railway، برو به پروژه → **Variables** و اضافه کن:

```
API_ID = [از GitHub Secrets کپی کن]
API_HASH = [از GitHub Secrets کپی کن]
SESSION_STRING = [از GitHub Secrets کپی کن]
BOT_TOKEN = [از GitHub Secrets کپی کن]
MY_CHAT_ID = [از GitHub Secrets کپی کن]
XKIRO_API_KEY = [از GitHub Secrets کپی کن]
API_BASE_URL = [از GitHub Secrets کپی کن]
DEFAULT_MODEL = deepseek/deepseek-v4-pro
HOURS_WINDOW = 12
```

**چطور GitHub Secrets رو ببینم؟**
متأسفانه نمی‌تونی مقادیر رو ببینی! باید اونا رو دوباره تولید کنی یا از جایی که اولین بار گرفتی دوباره بگیری.

---

## مرحله 3️⃣: چک کردن Deploy

1. در Railway → **Deployments**
2. باید ببینی که deployment موفق شده ✅
3. **View Logs** → باید ببینی:
   ```
   🚀 در حال راه‌اندازی ربات TeleBrief...
   ✅ ربات آماده است و منتظر دستورات...
   ```

---

## مرحله 4️⃣: تست ربات

در تلگرام:
- `/start` بفرست
- باید منوی دکمه‌دار رو ببینی
- روی دکمه کلیک کن
- باید کار کنه! 🎉

---

## 🔄 Deploy خودکار

هر بار که به GitHub push می‌کنی، Railway خودکار شناساییش می‌کنه و redeploy می‌کنه!

**نیازی به GitHub Actions نیست!** Railway خودش این کارو می‌کنه.

---

## ⚠️ اگه GitHub Secrets رو نداری چیکار کنم؟

اگه مقادیر رو نداری، باید دوباره بسازیشون:

### 1. BOT_TOKEN
- برو به [@BotFather](https://t.me/BotFather)
- `/mybots` → انتخاب ربات → `API Token`

### 2. API_ID و API_HASH
- برو به [my.telegram.org](https://my.telegram.org)
- API development tools
- کپی کن API_ID و API_HASH

### 3. SESSION_STRING
باید یک اسکریپت اجرا کنی:

```python
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = YOUR_API_ID
API_HASH = "YOUR_API_HASH"

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("SESSION_STRING:")
    print(client.session.save())
```

### 4. MY_CHAT_ID
- به ربات [@userinfobot](https://t.me/userinfobot) پیام `/start` بفرست
- Chat ID رو کپی کن

### 5. XKIRO_API_KEY و API_BASE_URL
- از سرویس XKIRO (یا هر AI provider دیگه‌ای که استفاده می‌کنی)

---

## 🎯 جمع‌بندی

Railway راحت‌ترین راهه:
1. Connect GitHub repo
2. تنظیم Variables (یکبار)
3. هر push خودکار deploy میشه
4. ✅ Done!

**نیازی به GitHub Actions پیچیده نیست!** 🚀
