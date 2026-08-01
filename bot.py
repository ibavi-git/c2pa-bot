import os
import logging
from pathlib import Path
from datetime import datetime
from c2pa_tool import strip_by_resave, detect

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest
from telegram.constants import ChatAction

# ==============================
# Logging Setup
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==============================
# Configuration
# ==============================
TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
QUALITY = 95

# Create directories
Path("downloads").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)

# ==============================
# /start Command
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greet user and show capabilities."""
    await update.message.reply_text(
        "👋 **MetaErase Bot**\n\n"
        "🔍 I'll strip all metadata from your images:\n"
        "  • EXIF data (camera info, GPS, timestamps)\n"
        "  • C2PA Content Credentials\n"
        "  • Comments, color profiles, IPTC tags\n\n"
        "📷 **Usage:** Just send me an image.\n"
        "⏱️ Processing time: ~2-5 seconds per image\n\n"
        "_Note: This re-encodes your image. Quality is high but not lossless._",
        parse_mode="Markdown"
    )

# ==============================
# /info Command (optional)
# ==============================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show metadata info about recent image (if available)."""
    await update.message.reply_text(
        "📊 **About metadata removal:**\n\n"
        "✅ Removes: EXIF, GPS, timestamps, camera model, lens info\n"
        "✅ Removes: C2PA signatures, digital provenance markers\n"
        "✅ Removes: Comments, color profiles, thumbnails\n\n"
        "⚠️ Note: Image is re-encoded at 95% quality for lossy formats.",
        parse_mode="Markdown"
    )

# ==============================
# Photo Handler
# ==============================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download, process, and return cleaned image."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    try:
        logger.info(f"User {user_name} ({user_id}) sent an image")
        
        # Show processing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.UPLOAD_PHOTO
        )
        
        # Get highest quality photo
        telegram_photo = update.message.photo[-1]
        
        # Check file size
        file_info = await context.bot.get_file(telegram_photo.file_id)
        if file_info.file_size > MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ Image too large! Max: {MAX_FILE_SIZE // (1024*1024)}MB, "
                f"Yours: {file_info.file_size // (1024*1024)}MB"
            )
            return
        
        # Generate unique paths
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = f"downloads/raw_{user_id}_{timestamp}.jpg"
        output_path = f"outputs/clean_{user_id}_{timestamp}.jpg"
        
        # Download
        await update.message.reply_text("📥 Receiving image...")
        await file_info.download_to_drive(input_path)
        logger.info(f"Downloaded image to {input_path}")
        
        # Detect C2PA (optional—log it but don't fail)
        await update.message.reply_text("🔍 Scanning for metadata markers...")
        c2pa_info = None
        try:
            c2pa_info = detect(input_path)
        except Exception as e:
            logger.warning(f"C2PA detection skipped: {e}")
        
        if c2pa_info:
            logger.info(f"C2PA found: {c2pa_info}")
            await update.message.reply_text(
                f"⚠️ Detected C2PA marker (claim: {c2pa_info.get('claim_generator', 'unknown')})"
            )
        
        # Process
        await update.message.reply_text("🧹 Removing ALL metadata...")
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.UPLOAD_PHOTO
        )
        strip_by_resave(input_path, output_path, quality=QUALITY)
        logger.info(f"Cleaned image saved to {output_path}")
        
        # Upload result
        with open(output_path, "rb") as img:
            await update.message.reply_photo(
                photo=img,
                caption=(
                    "✅ **Metadata removed!**\n\n"
                    "🧹 Stripped:\n"
                    "  • EXIF, GPS, timestamps\n"
                    "  • C2PA credentials\n"
                    "  • Comments & color profiles\n\n"
                    "_Your image is now anonymous._"
                ),
                parse_mode="Markdown"
            )
        logger.info(f"Sent cleaned image to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing image for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error: {str(e)[:100]}\n\n"
            "Please try again with a different image."
        )
    
    finally:
        # Cleanup (optional—keep last N files or delete immediately)
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
                logger.info(f"Cleaned up {input_path}")
        except:
            pass

# ==============================
# HTTP Timeouts
# ==============================
request = HTTPXRequest(
    connect_timeout=30,
    read_timeout=60,
    write_timeout=60,
    pool_timeout=30,
)

# ==============================
# Create Application
# ==============================
app = (
    Application.builder()
    .token(TOKEN)
    .request(request)
    .build()
)

# ==============================
# Register Handlers
# ==============================
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("info", info))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# ==============================
# Start Bot
# ==============================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🤖 MetaErase Bot is starting...")
    if TOKEN == "YOUR_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN not set! Export it or edit bot.py")
        exit(1)
    logger.info("=" * 60)
    app.run_polling(allowed_updates=["message", "photo"])
