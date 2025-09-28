import os
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask, redirect
from threading import Thread
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")  # Without @

# Database
client = AsyncIOMotorClient(DATABASE_URL)
db = client['database']  # spelling fixed
groups = db['group_id']

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
    button = [[
        InlineKeyboardButton(
            "🎈 Aᴅᴅ ʏᴏᴜʀ Gʀᴏᴜᴘ 🎈", 
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
        ),
    ]]
    await message.reply_text(
        "I ᴀᴍ Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Bᴏᴛ, I ᴄᴀɴ ᴅᴇʟᴇᴛᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘs ᴍᴇssᴀɢᴇs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴀғᴛᴇʀ ᴀ ᴄᴇʀᴛᴀɪɴ ᴘᴇʀɪᴏᴅ ᴏғ ᴛɪᴍᴇ.",
        reply_markup=InlineKeyboardMarkup(button),
        parse_mode=enums.ParseMode.MARKDOWN
    )

@bot.on_message(filters.command("set") & filters.group)
async def set_delete_time(_, message):
    args = message.text.split()
    if len(args) < 2 or not args.isdigit():
        await message.reply_text(
            "Dᴇʟᴇᴛᴇ ᴛɪᴍᴇ ᴍᴜsᴛ ʙᴇ ᴀɴ ɴᴜᴍʙᴇʀ...\n\n"
            "Exᴀᴍᴘʟᴇ: /set 10\n"
            "Exᴀᴍᴘʟᴇ: /set 20\n"
            "Oɴʟʏ Sᴇᴄᴏᴜɴᴅ 🙌"
        )
        return

    delete_time = int(args)
    chat_id = message.chat.id
    user_id = message.from_user.id

    admin_ids = []
    async for member in bot.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        admin_ids.append(member.user.id)

    if user_id not in admin_ids:
        await message.reply_text("Oɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs....😘")
        return

    await groups.update_one(
        {"group_id": chat_id},
        {"$set": {"delete_time": delete_time}},
        upsert=True
    )
    await message.reply_text(f"Sᴜᴄᴄᴇssғᴜʟʟʏ Sᴇᴛ {delete_time} Sᴇᴄᴏᴜɴᴅ....✅")

@bot.on_message(filters.group & filters.text)
async def delete_message(_, message):
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
        print(f"An error occurred: {e} /n Group ID: {chat_id}")

# Flask setup for keepalive web server
app = Flask(__name__)

@app.route('/')
def index():
    return redirect(f"https://telegram.me/{BOT_USERNAME}", code=302)

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.run()
