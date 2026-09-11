# 🚂 Railway Setup - راهنمای سریع

## مراحل 3 تایی:

### 1️⃣ در Railway

```
- برو railway.app
- New Project → Empty Project
- نام: TeleBrief
- Settings → Variables
- تمام این موارد رو دستی اضافه کن:
  • API_ID
  • API_HASH
  • SESSION_STRING
  • BOT_TOKEN
  • MY_CHAT_ID
  • XKIRO_API_KEY
  • API_BASE_URL
  • DEFAULT_MODEL
```

### 2️⃣ در GitHub

```
Settings → Secrets → New Secret:
- RAILWAY_TOKEN = [دریافت از railway.app/account]
- RAILWAY_PROJECT_ID = [دریافت از Settings پروژه]
```

### 3️⃣ Connect کردن

```
- Railway: Connect Repository → Select GitHub repo
- بس! خودکار deploy میشه
```

---

## ✅ چک کردن

```
Railway → Deployments → Logs
باید ببینی:
✅ ربات آماده است و منتظر دستورات...
```

---

**تموم!** 🎉
