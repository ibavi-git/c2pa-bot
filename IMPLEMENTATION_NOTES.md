# 🔧 Implementation Guide

## What I Added

### 1. **c2pa_tool.py** (was empty)
✅ Added complete metadata removal engine:
- `detect(path)` – Scan for C2PA credentials
- `strip_by_resave(path, out, quality)` – Re-encode pixels (removes ALL metadata)
- `strip_c2pa_jpeg(in, out)` – Surgical removal (JPEG only, preserves EXIF)

### 2. **bot.py** (major improvements)
✅ **Security & Robustness:**
- Moved token to environment variable (`os.getenv("BOT_TOKEN")`)
- Added file size limit checking (prevents DoS)
- Added comprehensive error handling with logging
- Unique file naming per user (`{user_id}_{timestamp}`)
- File cleanup after processing

✅ **UX Improvements:**
- Added `/info` command (explain what's removed)
- Status messages: "📥 Receiving", "🔍 Scanning", "🧹 Removing", "📤 Uploading"
- C2PA detection with user notification
- Detailed success message listing removed data
- Formatted responses (Markdown)
- Chat action indicators (shows "uploading...")

✅ **Logging:**
- Structured logs with timestamps
- User tracking (logs which user processed which image)
- Error tracking with full tracebacks
- C2PA detection status

### 3. **New Files**
✅ `requirements.txt` – Pinned dependency versions
✅ `.env.example` – Configuration template
✅ `.gitignore` – Prevent token leaks
✅ `setup.sh` – One-command installation
✅ `README.md` – Full documentation + deployment guides
✅ `IMPLEMENTATION_NOTES.md` – This file

---

## Key Design Decisions

### Why Re-encode (vs Surgical Removal)?
- ✅ **Brute force** (`strip_by_resave`): Removes 100% of metadata (default)
  - Works on all formats (JPEG, PNG, WebP, etc.)
  - No chance of leftover EXIF/IPTC/comments
  - Trade-off: ~5% quality loss (95% JPEG quality is imperceptible)

- ⚠️ **Surgical** (`strip_c2pa_jpeg`): Removes only C2PA + preserves EXIF
  - JPEG-only
  - Keeps camera metadata
  - Use if you want lossless + C2PA removal

Default is **re-encode** because:
1. Most users want complete anonymity
2. Quality impact is minimal
3. No risk of metadata leakage

### Token Management
```python
TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
```
- ✅ Reads from environment (safe for deployment)
- ✅ Falls back to placeholder if not set
- ✅ `.env` file ignored by `.gitignore` (no accidental commits)

### File Naming
```python
input_path = f"downloads/raw_{user_id}_{timestamp}.jpg"
```
- ✅ Prevents collisions if two users upload simultaneously
- ✅ Enables per-user tracking (see logs)
- ✅ Timestamp helps with debugging

### C2PA Detection
Optional (doesn't crash if missing):
```python
try:
    c2pa_info = detect(input_path)
except Exception as e:
    logger.warning(f"C2PA detection skipped: {e}")
```
- ✅ Informs user if synthetic content detected
- ✅ Falls back gracefully if c2pa-python isn't installed
- ✅ Logged but non-blocking

---

## Deployment Checklist

### Local Testing
- [ ] `pip install -r requirements.txt`
- [ ] `export BOT_TOKEN="123456:ABC-DEF..."`
- [ ] `python bot.py`
- [ ] Send test image to bot
- [ ] Verify clean image received

### Before Public Deploy
- [ ] Create new bot with @BotFather (don't use this token—it's an example)
- [ ] Add bot description: "Strip all metadata from images"
- [ ] Set commands via @BotFather:
  ```
  start - Welcome & usage info
  info - Details on what's removed
  ```
- [ ] Test on production (Render/Railway/VPS)

### Post-Deploy
- [ ] Monitor logs for errors
- [ ] Set up alerts if possible
- [ ] Test with various image formats
- [ ] Ask friends to test (find edge cases)

---

## Advanced Customization

### Change JPEG Quality
```python
QUALITY = 85  # Lower = smaller file, more quality loss
```

### Increase File Size Limit
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
```

### Switch to Surgical Mode
```python
# In handle_photo(), replace:
strip_by_resave(input_path, output_path, quality=QUALITY)

# With:
from c2pa_tool import strip_c2pa_jpeg
strip_c2pa_jpeg(input_path, output_path)  # JPEG only
```

### Add Database (track user stats)
```python
import sqlite3

# Create table
conn = sqlite3.connect("bot.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        count INTEGER,
        last_used TIMESTAMP
    )
""")

# In handle_photo():
conn.execute("UPDATE users SET count = count + 1 WHERE user_id = ?", (user_id,))
```

### Add Admin Commands
```python
ADMIN_IDS = [123456789]  # Your Telegram ID

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized")
        return
    # Show stats...

app.add_handler(CommandHandler("stats", stats))
```

---

## Debugging

### Check logs
```bash
python bot.py 2>&1 | grep ERROR
python bot.py 2>&1 | grep C2PA
```

### Test metadata removal locally
```bash
python -c "from c2pa_tool import detect, strip_by_resave
info = detect('test.jpg')
print(info)
strip_by_resave('test.jpg', 'clean.jpg')
"
```

### Verify token
```bash
curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe" | jq .
```

---

## File Cleanup Strategy

Current: Deletes input files after processing
```python
finally:
    if os.path.exists(input_path):
        os.remove(input_path)
```

### Alternative 1: Keep all files (debugging)
```python
# Comment out cleanup
# os.remove(input_path)
```

### Alternative 2: Keep N most recent files
```python
import os, glob
from pathlib import Path

def cleanup_old_files(dir, keep=10):
    files = sorted(glob.glob(f"{dir}/*"), key=os.path.getctime)
    for f in files[:-keep]:
        os.remove(f)

# In finally block:
cleanup_old_files("downloads")
cleanup_old_files("outputs")
```

### Alternative 3: S3 backup
```python
import boto3

s3 = boto3.client('s3')
s3.upload_file(output_path, 'my-bucket', f'images/{output_path.split("/")[-1]}')
```

---

## Monitoring & Metrics (Render/Production)

### Add uptime endpoint (optional)
```python
from aiohttp import web

async def health(request):
    return web.json_response({"status": "ok"})

# Register in app
```

### Monitor in logs
```bash
# Render dashboard shows last 1000 lines
# Set alerts for "❌ Error:"
```

### Use Telegram to send alerts
```python
ADMIN_CHAT_ID = 123456789

async def send_alert(msg):
    await app.bot.send_message(ADMIN_CHAT_ID, f"🚨 {msg}")

# In exception handler:
await send_alert(f"Error processing image: {e}")
```

---

## Performance Notes

- **Download**: ~1-2 sec (Telegram → bot)
- **C2PA scan**: ~0.5 sec
- **Re-encode**: ~0.5-1 sec (depends on image size)
- **Upload**: ~1-2 sec (bot → Telegram)
- **Total**: ~3-5 seconds per image

On Render free tier: Handles ~1-2 concurrent users comfortably.

---

## Next Steps / Ideas

🚀 Future improvements:
- [ ] Batch processing (upload folder)
- [ ] Watermark on output (optional)
- [ ] Compare before/after (overlay tool)
- [ ] Support for video (extract frames)
- [ ] PDF metadata removal
- [ ] Desktop app (PyQt)
- [ ] Web interface
- [ ] API endpoint (for integration)

---

## Questions?

- **Telegram bot issues?** → @BotFather help
- **Deployment issues?** → Render/Railway/VPS docs
- **C2PA questions?** → https://c2pa.org
- **Python bugs?** → Check `bot.py` line 60-80 (error handling)

---

**Happy deploying! 🚀**
