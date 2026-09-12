# 🤖 TeleBrief
## رصدخانه هوشمند تلگرام | تحلیل اخبار AI و امنیت سایبری

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Telegram](https://img.shields.io/badge/Try%20Bot-@telebriefdata__bot-0088cc?style=flat-square&logo=telegram)](https://t.me/telebriefdata_bot)

> **"In a world drowning in information, the art is in what you ignore."**

TeleBrief scans hundreds of Telegram tech channels, filters spam, and delivers AI-analyzed reports with importance scores, key insights, and direct source links.

## 📖 Quick Navigation

- [Why TeleBrief?](#why)
- [Core Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Deployment](#deployment)
- [Tech Stack](#tech)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Contributing](#contributing)

---

## <a id="why"></a>🎯 Why TeleBrief?

**The Problem:** Telegram tech channels = 1000s posts/day but 70% spam, 20% clickbait, 10% valuable

**The Solution:** Deep MTProto scraping + Two-stage AI filtering + Modern Telegram UI

### Three Revolutionary Components

1. **Deep MTProto Scraping (Telethon)**
   - Access without admin permissions
   - Real-time monitoring
   - Bypass rate limits

2. **Two-Stage AI Pipeline**
   - Stage 1: Shortlisting & spam removal
   - Stage 2: Merge & importance scoring (0-100)

3. **Beautiful Telegram UI**
   - Persian-native formatted cards
   - Expandable details
   - Direct source links

---

## <a id="features"></a>✨ Core Features

### 🧠 Two-Tier AI Analysis
Powered by DeepSeek V3/V4 & OpenAI. Extracts importance, reasoning, technical implications.

### 🔄 Live Loading Dashboard
Real-time animated status with phase tracking.

### ⏱️ Flexible Time Filtering
Presets: 6h, 12h, 24h, 48h, 7d, 15d. Custom ranges (1-720 hours).

### 📚 Channel Personalization
Start with curated defaults. Add unlimited custom channels.

### 📑 Smart Pagination
10 items/page by importance. Progressive loading.

### 🛡️ Intelligent Resilience
LLM fails? Fallback to engagement-ranked posts. Never fake analysis.

---

## <a id="architecture"></a>🏗️ Architecture

```
📡 Telegram Channels
     ↓
⚙️ Harvesting (Telethon MTProto)
     ↓
🧠 AI Pipeline (2-Stage Analysis)
     ↓
🚀 Delivery (Telegram Bot + GitHub Actions)
```

### Performance

| Metric | Value |
|:---:|:---:|
| Analysis Time | 15-45s |
| Scan Speed | ~100 msg/s |
| Memory | <150MB |
| Pagination | <1s |

---

## <a id="installation"></a>🚀 Installation

### Prerequisites
- Python 3.11+
- Telegram account
- Telegram API ID/Hash (from https://my.telegram.org)
- Bot Token (from @BotFather)
- xKiro API Key (for LLM)

### Quick Setup

```bash
# 1. Clone
git clone https://github.com/Amin-Moniry/TeleBrief.git
cd TeleBrief

# 2. Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Get Telegram session
python -c "
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
API_ID = YOUR_API_ID
API_HASH = 'YOUR_API_HASH'
with TelegramClient(StringSession(), API_ID, API_HASH) as c:
    print(c.session.save())
"

# 5. Configure .env
cp .env.example .env
# Edit .env with your credentials

# 6. Run
python command_bot.py
```

---

## <a id="deployment"></a>☁️ Deployment

### Railway / Render / Fly.io (24/7, Free)
1. Connect GitHub repo
2. Start command: `python command_bot.py`
3. Add env vars
4. Deploy

### GitHub Actions (Scheduled)
Create `.github/workflows/daily.yml` for automated 12h reports

### Linux Systemd
Create `/etc/systemd/system/telebrief.service`

### Docker
```bash
docker run -d --name telebrief --env-file .env telebrief:latest
```

---

## <a id="tech"></a>🛠️ Tech Stack

| Component | Technology |
|:---|:---|
| Language | Python 3.11+ |
| Telegram Client | Telethon |
| Bot Framework | python-telegram-bot |
| LLM Gateway | xKiro (OpenAI-compatible) |
| Storage | JSON |
| Async | asyncio |
| CI/CD | GitHub Actions |

---

## ⚙️ Configuration

### Environment Variables

```bash
API_ID=YOUR_ID
API_HASH=YOUR_HASH
SESSION_STRING=YOUR_SESSION
BOT_TOKEN=YOUR_TOKEN
XKIRO_API_KEY=YOUR_KEY
API_BASE_URL=https://api.xkiro.com/v1
DEFAULT_MODEL=openai/gpt-5.6-luna
FALLBACK_MODELS=z-ai/glm-5.3-flash
HOURS_WINDOW=12
BATCH_CHAR_LIMIT=12000
MODEL_RETRIES=4
ANALYSIS_CONCURRENCY=1
```

### Model Selection

```python
DEFAULT_MODEL = "openai/gpt-5.6-luna"  # Fast & cheap
FALLBACK_MODELS = "z-ai/glm-5.3-flash"  # Better reasoning
```

---

## <a id="troubleshooting"></a>🐛 Troubleshooting

### Bot Won't Start
```bash
ps aux | grep command_bot.py
kill -9 PID
# Get new token from @BotFather
```

### LLM Service 503
```bash
# Check model exists
curl https://api.xkiro.com/v1/models

# Switch model
DEFAULT_MODEL=openai/gpt-5.6-luna
```

### Session Expired
Regenerate using the SESSION_STRING script above.

### Rate Limiting
Reduce `ANALYSIS_CONCURRENCY=1` or increase `BATCH_CHAR_LIMIT=20000`

---

## <a id="faq"></a>❓ FAQ

**Q: How accurate is analysis?**  
A: 80-90% on importance scoring, trained on tech/security patterns.

**Q: Self-hosted LLM?**  
A: Yes! Any OpenAI-compatible API (Ollama, LocalAI, etc).

**Q: Privacy?**  
A: Local analysis, no logging, follows API provider ToS.

**Q: Add custom channels?**  
A: Use `/addchannel` → enter `@channel_name`

**Q: Why slow?**  
A: Large batches or slow LLM. Try increasing `ANALYSIS_CONCURRENCY`.

---

## 📡 Default Channels

### AI Channels
@digiai, @RoidBest, @Farda_Ai, @Lumosel, @asrnovin_ir, @perplexity, @cryptoquant_official, @Hugging_face_news

### Security Channels
@cybersecurityexperts, @thehackernews, @cibsecurity, @Cyber_Security_Channel, @androidMalware, @cloudandcybersecurity

**Add unlimited custom channels via bot menu**

---

## 🎮 Bot Commands

```
/start          → Initialize, show main menu
/menu           → Quick category selector
/ai             → Last 12h AI summary
/security       → Last 12h security summary
/help           → Usage guide
/about          → Project info
```

---

## <a id="contributing"></a>🤝 Contributing

1. Fork repo
2. Create branch: `git checkout -b feature/your-idea`
3. Commit: `git commit -m 'feat: description'`
4. Push: `git push origin feature/your-idea`
5. PR

---

## 👤 Author

**Created with ❤️ by Amin Moniry**

[![GitHub](https://img.shields.io/badge/GitHub-Amin--Moniry-181717?style=flat-square&logo=github)](https://github.com/Amin-Moniry)
[![Telegram](https://img.shields.io/badge/Telegram-@telebriefdata__bot-2CA5E0?style=flat-square&logo=telegram)](https://t.me/telebriefdata_bot)

⭐ **Star the repo if this helped you!**

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details