import random, requests, openai
from datetime import datetime
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext, Dispatcher
from dotenv import load_dotenv
from flask import Flask, request
import os

# Cargar variables del archivo .env
load_dotenv()

# API Tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

print("🔍 TOKEN:", TELEGRAM_TOKEN)

user_context = {}

CATEGORIES = [
    "Bubble Keychain", "Puffy Keychain", "Glam Keychain", "Sweet Keychain", "Teachy Keychain", "Happy Keychain",
    "Pasha Keychain", "Love Candy Steel Tumbler", "Hearts & Kisses Water Bottle", "Love & Sip Tumbler",
    "Gradient Glow Tumbler", "Love Heart Sports Bottle", "Plush Heart Pillow – Let Me Sleep", "XO Plush Pillow",
    "Velvet Heart Pillow", "Cozy Pup Blanket", "Cute & Cozy Kitchen Towel Set", "Happy Vibes Coaster Collection",
    "Smiley Cosmetic Bag", "Smiley Tote Bag", "Hello Kitty Dinner Set"
]

CATEGORY_DESCRIPTIONS = {
    "Bubble Keychain": "cute and bouncy keychain full of bubble joy",
    "Puffy Keychain": "fluffy little charm that adds soft energy to any look",
    "Glam Keychain": "sparkly glam for your keys or your pastel purse",
    "Sweet Keychain": "a sprinkle of sweetness you can carry everywhere",
    "Teachy Keychain": "chic and smart with a touch of pastel sass",
    "Happy Keychain": "a smiley reminder to stay happy and bright",
    "Pasha Keychain": "signature charm of cuteness with attitude",
    "Love Candy Steel Tumbler": "sweetest way to sip your favorite drinks on the go",
    "Hearts & Kisses Water Bottle": "hydration with heart and kissy vibes 💋",
    "Love & Sip Tumbler": "sip the love in pastel perfection",
    "Gradient Glow Tumbler": "ombre dreams in a glowing gradient bottle",
    "Love Heart Sports Bottle": "sporty, sweet, and heart-filled hydration",
    "Plush Heart Pillow – Let Me Sleep": "soft, sleepy heart that just wants nap time",
    "XO Plush Pillow": "snuggly XO love that feels like a warm hug",
    "Velvet Heart Pillow": "velvety smooth heart pillow for cozy chic vibes",
    "Cozy Pup Blanket": "pastel puppy dreams in the softest blanket",
    "Cute & Cozy Kitchen Towel Set": "make your kitchen the coziest corner",
    "Happy Vibes Coaster Collection": "smiley coasters to brighten your table",
    "Smiley Cosmetic Bag": "carry your joy and glam in one cute pouch",
    "Smiley Tote Bag": "sunny tote full of pastel personality",
    "Hello Kitty Dinner Set": "adorable Hello Kitty vibes for every meal"
}

DATES = {
    "02-14": "Valentine’s Day", "05-10": "Mother’s Day", "06-17": "Father’s Day", "10-31": "Halloween",
    "12-25": "Christmas", "01-01": "New Year", "spring": "Spring", "summer": "Summer",
    "autumn": "Autumn", "winter": "Winter", "none": ""
}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🧁 ESTE ES EL BOT NUEVO 100% CON PRODUCTOS REALES ✨")

def check(update: Update, context: CallbackContext):
    update.message.reply_text("✨ El bot está funcionando y estás usando la versión actualizada con catálogo real.")

def handle_media(update: Update, context: CallbackContext):
    uid = update.message.from_user.id
    media = update.message.photo[-1].file_id if update.message.photo else update.message.video.file_id
    mtype = "photo" if update.message.photo else "video"
    user_context[uid] = {"file": media, "type": mtype}
    kb = [[InlineKeyboardButton(cat, callback_data=f"cat|{cat}")] for cat in CATEGORIES]
    update.message.reply_text("✨ Choose your exact product:", reply_markup=InlineKeyboardMarkup(kb))

def category_handler(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()
    uid = q.from_user.id
    user_context[uid]["cat"] = q.data.split("|")[1]
    kb = [
        [InlineKeyboardButton("💖 Valentine’s Day", callback_data="date|02-14")],
        [InlineKeyboardButton("👩‍👧 Mother’s Day", callback_data="date|05-10")],
        [InlineKeyboardButton("👨 Father’s Day", callback_data="date|06-17")],
        [InlineKeyboardButton("🎃 Halloween", callback_data="date|10-31")],
        [InlineKeyboardButton("🎄 Christmas", callback_data="date|12-25")],
        [InlineKeyboardButton("🎆 New Year", callback_data="date|01-01")],
        [InlineKeyboardButton("🌸 Spring", callback_data="date|spring")],
        [InlineKeyboardButton("☀️ Summer", callback_data="date|summer")],
        [InlineKeyboardButton("🍁 Autumn", callback_data="date|autumn")],
        [InlineKeyboardButton("❄️ Winter", callback_data="date|winter")],
        [InlineKeyboardButton("🚫 None", callback_data="date|none")]
    ]
    q.edit_message_text("✨ Is there a special occasion?", reply_markup=InlineKeyboardMarkup(kb))

def date_handler(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()
    uid = q.from_user.id
    selection = q.data.split("|")[1]
    fest = DATES.get(selection, "")
    user_context[uid]["date"] = fest
    send_caption(uid, context)

def send_caption(uid, context: CallbackContext):
    data = user_context[uid]
    cat, mtype, file_id, fest = data["cat"], data["type"], data["file"], data.get("date", "")
    desc = CATEGORY_DESCRIPTIONS.get(cat, cat)
    prompt = (
        f"You are a glam, pastel-toned content creator for a nostalgic and emotional gift brand.\n"
        f"Write a viral Instagram + TikTok caption for a {desc}.\n"
        f"The caption should feel dreamy, funny, emotional or nostalgic — NOT like an ad.\n"
        f"{('This is for ' + fest) if fest else 'No special occasion.'}\n"
        f"Write the caption in English and Spanish TOGETHER, as one post.\n"
        f"Add a line break before the Spanish part.\n"
        f"Include English hashtags, then Spanish hashtags. Add emojis and keep it super aesthetic.\n"
        f"Do NOT say 'English:' or 'Spanish:'. Just flow like a real creator post."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        lines = [line for line in raw.splitlines() if "english" not in line.lower() and "spanish" not in line.lower()]
        caption = "\n".join(lines).strip()
    except Exception as e:
        caption = f"⚠️ Error generating caption: {e}"

    kb = [[InlineKeyboardButton("✅ Approve", callback_data="app"), InlineKeyboardButton("❌ Reject", callback_data="rej")]]
    markup = InlineKeyboardMarkup(kb)

    bot = context.bot
    if mtype == "photo":
        bot.send_photo(uid, photo=file_id, caption=caption, reply_markup=markup)
    else:
        bot.send_video(uid, video=file_id, caption=caption, reply_markup=markup)

def approve_reject(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()
    text = "✅ Approved for posting" if q.data == "app" else "❌ Rejected"
    q.edit_message_text(text=text)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("check", check))
    dp.add_handler(MessageHandler(Filters.photo | Filters.video, handle_media))
    dp.add_handler(CallbackQueryHandler(category_handler, pattern="^cat\\|"))
    dp.add_handler(CallbackQueryHandler(date_handler, pattern="^date\\|"))
    dp.add_handler(CallbackQueryHandler(approve_reject, pattern="^(app|rej)$"))
    print("🌸 PASHABOT ACTUALIZADO: catálogo real y sin música 🌸")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
