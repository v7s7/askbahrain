#!/usr/bin/env python3
"""
Telegram Bot Interface for the Instagram Text Overlay Agent
------------------------------------------------------------
How to use from your phone:
  1. Start the bot on your PC/server: python telegram_bot.py
  2. Open Telegram, find your bot, and send commands:

     Just send any text message → overlays it on the default template and posts to Instagram
     /preview Your text here  → generates image but does NOT post (sends preview back to you)
     /template                → shows which template is currently active
     /settemplate             → reply with a photo to set it as the new template
     /help                    → show all commands
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from image_processor import add_text_to_image
from instagram_publisher import publish_to_instagram

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
ACTIVE_TEMPLATE_FILE = TEMPLATE_DIR / ".active_template"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def _get_active_template() -> str:
    if ACTIVE_TEMPLATE_FILE.exists():
        path = ACTIVE_TEMPLATE_FILE.read_text().strip()
        if Path(path).exists():
            return path
    # Fall back to any image in templates/
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        found = list(TEMPLATE_DIR.glob(ext))
        if found:
            return str(found[0])
    return ""


def _set_active_template(path: str) -> None:
    ACTIVE_TEMPLATE_FILE.write_text(path)


def _missing_env_vars() -> list[str]:
    return [k for k in ("INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN", "IMGBB_API_KEY")
            if not os.getenv(k)]


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm your Instagram posting bot.\n\n"
        "Just send me any text and I'll overlay it on your template and post it to Instagram.\n\n"
        "Commands:\n"
        "/preview <text> — generate image preview without posting\n"
        "/template — show active template\n"
        "/settemplate — send a photo to this command to set a new template\n"
        "/help — show this message"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def template_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    template = _get_active_template()
    if not template:
        await update.message.reply_text(
            "No template set. Send a photo with the caption /settemplate to set one."
        )
        return
    await update.message.reply_photo(
        photo=open(template, "rb"),
        caption=f"Active template: {Path(template).name}",
    )


async def set_template(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User sends a photo with caption '/settemplate' — saves it as the new template."""
    if not update.message.photo:
        await update.message.reply_text(
            "Send a photo with the caption /settemplate to set it as your template."
        )
        return

    photo = update.message.photo[-1]  # highest resolution
    file = await context.bot.get_file(photo.file_id)
    template_path = str(TEMPLATE_DIR / "template.jpg")
    await file.download_to_drive(template_path)
    _set_active_template(template_path)
    await update.message.reply_text("Template updated!")


async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate image and send back as preview without posting."""
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /preview Your text here")
        return

    template = _get_active_template()
    if not template:
        await update.message.reply_text(
            "No template found. Send a photo with caption /settemplate first."
        )
        return

    await update.message.reply_text("Generating preview...")
    try:
        output_path = add_text_to_image(template_path=template, text=text)
        await update.message.reply_photo(
            photo=open(output_path, "rb"),
            caption=f"Preview (not posted)\nText: {text}",
        )
    except Exception as e:
        logger.exception("Preview failed")
        await update.message.reply_text(f"Error generating image: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Any plain text message → generate image + post to Instagram."""
    text = update.message.text.strip()
    if not text:
        return

    missing = _missing_env_vars()
    if missing:
        await update.message.reply_text(
            f"Missing credentials in .env: {', '.join(missing)}\n"
            "Fix your .env file and restart the bot."
        )
        return

    template = _get_active_template()
    if not template:
        await update.message.reply_text(
            "No template found. Send a photo with caption /settemplate first."
        )
        return

    await update.message.reply_text("Generating image...")

    try:
        output_path = add_text_to_image(template_path=template, text=text)
    except Exception as e:
        logger.exception("Image generation failed")
        await update.message.reply_text(f"Failed to generate image: {e}")
        return

    await update.message.reply_photo(
        photo=open(output_path, "rb"),
        caption="Posting to Instagram...",
    )

    try:
        caption = f"{text}\n\n{os.getenv('DEFAULT_CAPTION', '')}".strip()
        media_id = publish_to_instagram(
            image_path=output_path,
            caption=caption,
            user_id=os.getenv("INSTAGRAM_USER_ID"),
            access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN"),
            imgbb_api_key=os.getenv("IMGBB_API_KEY"),
        )
        await update.message.reply_text(f"Posted to Instagram! Media ID: {media_id}")
    except Exception as e:
        logger.exception("Instagram publish failed")
        await update.message.reply_text(f"Image generated but Instagram post failed:\n{e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN not set in .env\n"
            "Get a token from @BotFather on Telegram."
        )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("template", template_command))
    app.add_handler(CommandHandler("preview", preview))
    # Photo sent alone (to set template)
    app.add_handler(MessageHandler(filters.PHOTO & filters.Caption(r"^/settemplate"), set_template))
    # Any plain text message → post to Instagram
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
