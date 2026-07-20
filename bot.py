import os
import logging
import urllib.parse
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Prompt Engineer
# Expands a short user idea into a more detailed image prompt.
# Rule-based, so it works immediately with no extra API key.
# ---------------------------------------------------------
STYLE_BOOSTERS = [
    "highly detailed",
    "sharp focus",
    "professional",
    "cinematic lighting",
    "8k resolution",
    "trending on artstation",
]

def enhance_prompt(raw_prompt: str) -> str:
    raw_prompt = raw_prompt.strip()
    boosters = ", ".join(STYLE_BOOSTERS)
    return f"{raw_prompt}, {boosters}"


# ---------------------------------------------------------
# Image Generation
# Uses Pollinations.ai — free, no API key required.
# ---------------------------------------------------------
def generate_image_url(prompt: str) -> str:
    encoded_prompt = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"


# ---------------------------------------------------------
# Handlers
# ---------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Kynexa Bot!\n\n"
        "Commands:\n"
        "/generate <idea> — generate an AI image from your idea\n"
        "/enhance <idea> — see the enhanced prompt only\n"
        "/help — show this message"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def enhance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /enhance a cat riding a bicycle")
        return
    raw_prompt = " ".join(context.args)
    enhanced = enhance_prompt(raw_prompt)
    await update.message.reply_text(f"Enhanced prompt:\n{enhanced}")

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /generate a cat riding a bicycle")
        return

    raw_prompt = " ".join(context.args)
    enhanced_prompt = enhance_prompt(raw_prompt)

    await update.message.reply_text(f"Generating image for:\n{enhanced_prompt}\n\nPlease wait...")

    try:
        image_url = generate_image_url(enhanced_prompt)
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
        await update.message.reply_photo(photo=response.content, caption=f"Prompt: {raw_prompt}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Image generation failed: {e}")
        await update.message.reply_text(
            "Sorry, something went wrong generating the image. Please try again."
        )

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I didn't understand that. Try /generate <your idea> or /help"
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CommandHandler("enhance", enhance))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("Kynexa Bot started polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
