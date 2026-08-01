# 🧹 MetaErase Bot

A Telegram bot that strips **all metadata** from images in seconds.

Removes:
- ✅ EXIF data (camera model, GPS, timestamps)
- ✅ C2PA Content Credentials (AI provenance markers)
- ✅ IPTC tags, color profiles, comments, thumbnails
- ✅ Any other embedded metadata

## Quick Start

### 1. **Create a Telegram Bot**

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow prompts
3. Copy your **API Token** (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
4. Paste it into `.env`:

```bash
cp .env.example .env
# Edit .env and add BOT_TOKEN=your_token_here
```

### 2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install python-telegram-bot pillow c2pa-python httpx
```

### 3. **Run Locally**

```bash
export BOT_TOKEN="your_token_from_botfather"
python bot.py
```

You'll see:
```
============================================================
🤖 MetaErase Bot is starting...
============================================================
```

Open Telegram, find your bot, and send it an image!

---

## Deployment

### Option A: **Render** (Free, recommended)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com)
3. Create **New → Web Service**
4. Connect your repo
5. Settings:
   - **Start Command:** `python bot.py`
   - **Environment variable:** `BOT_TOKEN=your_token`
6. Deploy! Bot runs 24/7 (free tier has 750 free hours/month)

### Option B: **Heroku** (Paid since Nov 2022)

```bash
heroku login
heroku create your-app-name
heroku config:set BOT_TOKEN="your_token"
git push heroku main
```

### Option C: **Railway** (Free tier available)

1. Go to [railway.app](https://railway.app)
2. Import GitHub repo
3. Add `BOT_TOKEN` environment variable
4. Deploy

### Option D: **VPS** (DigitalOcean, Linode, AWS)

```bash
# SSH into server
ssh root@your_server

# Install Python 3.11+
apt update && apt install python3.11 python3.11-venv python3-pip

# Clone repo
git clone https://github.com/ibavi-git/c2pa-bot.git
cd c2pa-bot

# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run in background (using systemd or tmux)
tmux new-session -d -s bot "export BOT_TOKEN='your_token' && python bot.py"
```

---

## Usage

### For Users:
1. Open the bot on Telegram (search by username)
2. Send `/start` to see welcome message
3. Send any image
4. Wait 2-5 seconds
5. Get a clean image with no metadata

### For Developers:

**Extract metadata info:**
```python
from c2pa_tool import detect

info = detect("image.jpg")
if info:
    print(f"C2PA Claim: {info['claim_generator']}")
    print(f"Manifests: {info['num_manifests']}")
```

**Remove metadata programmatically:**
```python
from c2pa_tool import strip_by_resave

# Strip all metadata
strip_by_resave("raw.jpg", "clean.jpg", quality=95)
```

---

## How It Works

1. **Download** – Telegram sends image to bot
2. **Scan** – Check for C2PA credentials (optional)
3. **Process** – Re-encode image using PIL (pixels only)
4. **Upload** – Send cleaned image back to user

The re-encoding is **lossy but high-quality** (95% JPEG quality). 
If you need pixel-perfect preservation, use surgical C2PA removal instead:
```python
from c2pa_tool import strip_c2pa_jpeg
strip_c2pa_jpeg("image.jpg", "output.jpg")  # JPEG only, keeps EXIF
```

---

## File Structure

```
c2pa-bot/
├── bot.py              # Main Telegram bot
├── c2pa_tool.py        # Metadata removal logic
├── requirements.txt    # Python dependencies
├── .env.example        # Config template
├── README.md           # This file
├── downloads/          # Temp storage (input)
└── outputs/            # Temp storage (output)
```

---

## Troubleshooting

### Bot not responding?
- ✅ Check `BOT_TOKEN` is set: `echo $BOT_TOKEN`
- ✅ Restart bot: `Ctrl+C` then `python bot.py`
- ✅ Verify bot is active with @BotFather: `/mybots → select bot → Bot Settings`

### Installation errors?
```bash
# Update pip
pip install --upgrade pip

# Try manual install
pip install --no-cache-dir python-telegram-bot pillow c2pa-python
```

### C2PA detection failing?
It's optional! Bot will continue without it. Check logs:
```bash
python bot.py 2>&1 | grep -i c2pa
```

### Image upload failing?
- Max file size: **20 MB** (configurable in `bot.py`)
- Supported formats: JPEG, PNG, WebP
- Try a smaller/different image

---

## Legal / Ethical Notes

⚠️ **C2PA is a transparency signal.** Some jurisdictions (EU AI Act) require disclosure of AI-generated media. Removing C2PA to pass synthetic content as human-made may violate:
- Local regulations
- Platform ToS
- Copyright/IP laws

**Use on your own files for legitimate privacy purposes.**

---

## Advanced Config

Edit `bot.py` to customize:

```python
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB limit
QUALITY = 95                       # JPEG quality (1-100)
```

---

## Contributing

Found a bug? Want a feature?
- Open an issue on GitHub
- Show logs: `python bot.py 2>&1 | head -50`
- Attach test image (optional)

---

## License

MIT – Use freely, modify as needed.

---

## Made with ❤️ by Bavitha
