# 🚂 راهنمای Deploy با GitHub Actions → Railway

## چرا این روش؟

✅ GitHub Secrets محفوظ می‌مونن  
✅ نیازی به کپی دستی ENV variables نیست  
✅ هر push خودکار deploy میشه  
✅ Railway رایگانه (500 ساعت/ماه)

---

## مرحله 1️⃣: ساخت پروژه در Railway

1. برو به [railway.app](https://railway.app)
2. Sign in with GitHub
3. کلیک روی **New Project**
4. انتخاب **Empty Project**
5. نام پروژه: `TeleBrief`

---

## مرحله 2️⃣: دریافت Railway Token

1. در Railway، برو به **Account Settings**
2. تب **Tokens**
3. کلیک روی **Create Token**
4. نام بده: `GitHub Actions`
5. کپی کن Token رو (فقط یکبار نشون داده میشه!)

---

## مرحله 3️⃣: دریافت Railway Project ID

1. در پروژه Railway، برو به **Settings**
2. پیدا کن **Project ID** (مثلاً: `abc123-def456-...`)
3. کپی کن

---

## مرحله 4️⃣: اضافه کردن Secrets به GitHub

برو به repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

اضافه کن این دو تا:

```
RAILWAY_TOKEN = [توکنی که کپی کردی]
RAILWAY_PROJECT_ID = [Project ID که کپی کردی]
```

**نکته:** باقی secrets (API_ID, BOT_TOKEN و...) قبلاً اضافه کردی، پس لازم نیست دوباره اضافه کنی.

---

## مرحله 5️⃣: Push کردن کد

```bash
git add .
git commit -m "feat: add Railway deployment via GitHub Actions"
git push origin master
```

---

## مرحله 6️⃣: چک کردن Deploy

1. برو به GitHub repository → **Actions**
2. باید workflow "Deploy to Railway" رو ببینی
3. اگه سبز شد ✅ = Deploy موفق!
4. اگه قرمز شد ❌ = برو تو logs ببین چه خطایی داده

---

## مرحله 7️⃣: چک کردن که ربات کار میکنه

1. در Railway → پروژه TeleBrief → **Deployments**
2. باید ببینی که deployment در حال اجراست
3. کلیک روی **View Logs**
4. باید ببینی:
   ```
   🚀 در حال راه‌اندازی ربات TeleBrief...
   ✅ ربات آماده است و منتظر دستورات...
   ```

5. در تلگرام، به ربات `/start` بفرست
6. باید منوی دکمه‌دار رو ببینی!

---

## ⚠️ نکات مهم:

### 1. حذف GitHub Actions قدیمی
فایل `.github/workflows/check-command.yml.disabled` رو می‌تونی حذف کنی (دیگه لازم نیست)

### 2. نگه داشتن daily.yml
فایل `.github/workflows/daily.yml` رو نگه دار - این برای ارسال گزارش روزانه خودکاره

### 3. محدودیت رایگان Railway
- 500 ساعت در ماه
- یعنی ~16 ساعت در روز
- برای یک ربات کافیه!

### 4. مانیتورینگ
در Railway می‌تونی logs رو ببینی و ببینی ربات چطور کار میکنه

---

## 🐛 رفع مشکلات متداول:

### خطا: "RAILWAY_TOKEN not found"
→ مطمئن شو که در GitHub Secrets درست اضافه کردی

### خطا: "Project not found"
→ RAILWAY_PROJECT_ID رو چک کن

### ربات آنلاین نیست
→ در Railway logs رو چک کن، شاید یکی از ENV variables اشتباهه

### خطای "telethon"
→ مطمئن شو `requirements.txt` هم push شده

---

## 🎉 تمام!

حالا هر بار که کد رو push کنی، خودکار روی Railway deploy میشه و ربات 24/7 اجراست!

**دیگه نیازی به کپی دستی secrets نیست!** 🔐✨
