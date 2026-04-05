import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- 1. PYTHON 3.14 PATCH (CRITICAL) ---
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# --- 2. CONFIGURATION ---
# Replace these with your actual tokens
API_ID = 37674103
API_HASH = "f9ecc621ed4865256f94f71a7dd6a1c8"
BOT_TOKEN = "8709295055:AAFDxRIDE03upWylyGjHasus9mv_ME0o5ik"

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# In-memory storage for thumbnails
user_thumbnails = {}

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        f"✨ **Welcome {message.from_user.first_name}!**\n\n"
        "1️⃣ Send a **Photo** to set it as a thumbnail.\n"
        "2️⃣ Send a **File** to rename it."
    )

@app.on_message(filters.photo & filters.private)
async def set_thumbnail(client, message):
    user_id = message.from_user.id
    path = f"thumb_{user_id}.jpg"
    
    status = await message.reply_text("⏳ **Saving Thumbnail...**")
    await message.download(file_name=path)
    
    user_thumbnails[user_id] = path
    await status.edit("✅ **Thumbnail Saved!** Now send the file.")

@app.on_message((filters.document | filters.video) & filters.private)
async def file_received(client, message):
    await message.reply_text(
        "📝 **File Received!**\n\n"
        "Please send the **NEW NAME** for this file now.",
        reply_to_message_id=message.id
    )
    # Store the file object temporarily
    user_thumbnails[f"file_{message.from_user.id}"] = message

@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def rename_process(client, message):
    user_id = message.from_user.id
    file_key = f"file_{user_id}"
    
    if file_key not in user_thumbnails:
        return # Ignore random text

    new_name = message.text
    old_file_msg = user_thumbnails[file_key]
    thumb = user_thumbnails.get(user_id)

    status = await message.reply_text("📥 **Downloading...**")
    file_path = await client.download_media(old_file_msg)
    
    await status.edit("📤 **Uploading with new name...**")
    
    await client.send_document(
        chat_id=message.chat.id,
        document=file_path,
        file_name=new_name,
        thumb=thumb,
        caption=f"✅ **Successfully Renamed to:** `{new_name}`"
    )
    
    await status.delete()
    if os.path.exists(file_path):
        os.remove(file_path) # Clean up HP Victus disk space
    del user_thumbnails[file_key]

print("🚀 Bot Started Successfully!")
app.run()
