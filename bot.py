import os
import asyncio
from threading import Thread
from flask import Flask, redirect
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from motor.motor_asyncio import AsyncIOMotorClient

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")  # Without @

# Database init
mongo_client = AsyncIOMotorClient(DATABASE_URL)
db = mongo_client['database']
groups = db['group_id']

# Bot init
bot = Client(
    "deletebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=10
)

@bot.on_message(filters.command("thewarriorsreal") & filters.private)
async def start(_, message):
    buttons = [[
        InlineKeyboardButton(
            "🎈 Add your Group 🎈",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
        )
    ]]
    await message.reply_text(
        "I am Auto Delete Bot. I can delete your group messages automatically after a certain period of time.",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.MARKDOWN
    )

@bot.on_message(filters.command("set") & filters.group)
async def set_delete_time_handler(_, message):
    args = message.text.split()
    if len(args) < 2 or not args.isdigit():
        await message.reply_text(
            "Delete time must be a number!\nExample: /set 10\nOnly seconds accepted."
        )
        return

    delete_time = int(args)
    chat_id = message.chat.id
    user_id = message.from_user.id

    admins = []
    async for member in bot.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if user_id not in admins:
        await message.reply_text("Only group admins can do this.")
        return

    await groups.update_one(
        {"group_id": chat_id},
        {"$set": {"delete_time": delete_time}},
        upsert=True
    )
    await message.reply_text(f"Successfully set message delete time to {delete_time} seconds.")

@bot.on_message(filters.group & filters.text)
async def auto_delete_handler(_, message):
    chat_id = message.chat.id
    group = await groups.find_one({"group_id": chat_id})
    if not group:
        return
    delete_time = int(group.get("delete_time", 0))
    if delete_time <= 0:
        return

    try:
        await asyncio.sleep(delete_time)
        await message.delete()
    except Exception as e:
        print(f"Error deleting message {message.message_id} in group {chat_id}: {e}")

# Flask app for keepalive
app = Flask(__name__)

@app.route('/')
def index():
    return redirect(f"https://t.me/{BOT_USERNAME}", code=302)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    # Start Flask in separate thread
    Thread(target=run_flask).start()
    # Run the bot
    bot.run()
