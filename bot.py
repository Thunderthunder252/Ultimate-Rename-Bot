import os
import asyncio
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER ---
app_server = Flask(__name__)
@app_server.route('/')
def home():
    return "Bot is Live"

def run_server():
    # Use the port Render expects
    port = int(os.environ.get("PORT", 8080))
    app_server.run(host='0.0.0.0', port=port)

# --- 2. PYTHON 3.14 PATCH ---
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# --- 3. CONFIGURATION ---
API_ID = 37674103
API_HASH = "f9ecc621ed4865256f94f71a7dd6a1c8"
BOT_TOKEN = "8709295055:AAHOv4sHtQA6eletK7jc1Nw1REeajbadYNQ"

bot = Client("ultimate_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_thumbnails = {}

# --- 4. HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(f"✨ **Welcome {message.from_user.first_name}!**\n\nSend a Photo for a thumbnail or a File to rename.")

@bot.on_message(filters.photo & filters.private)
async def set_thumbnail(client, message):
    user_id = message.from_user.id
    path = os.path.join(os.getcwd(), f"thumb_{user_id}.jpg")
    await message.download(file_name=path)
    user_thumbnails[user_id] = path
    await message.reply_text("✅ **Thumbnail Saved!**")

@bot.on_message((filters.document | filters.video) & filters.private)
async def file_received(client, message):
    user_thumbnails[f"file_{message.from_user.id}"] = message
    await message.reply_text("📝 **File Received!** Send the **NEW NAME** (with extension).")

@bot.on_message(filters.text & filters.private & ~filters.command("start"))
async def rename_process(client, message):
    user_id = message.from_user.id
    file_key = f"file_{user_id}"
    if file_key not in user_thumbnails: return

    new_name = message.text
    old_file_msg = user_thumbnails[file_key]
    thumb = user_thumbnails.get(user_id)

    status = await message.reply_text("📥 **Downloading...**")
    try:
        file_path = await client.download_media(old_file_msg)
        await status.edit("📤 **Uploading...**")
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            file_name=new_name,
            thumb=thumb if thumb and os.path.exists(thumb) else None,
            caption=f"✅ **Renamed:** `{new_name}`",
            force_document=True
        )
        await status.delete()
        if os.path.exists(file_path): os.remove(file_path)
        del user_thumbnails[file_key]
    except Exception as e:
        await status.edit(f"❌ **Error:** `{str(e)}`")

# --- 5. START ---
if __name__ == "__main__":
    # Start Flask
    t = Thread(target=run_server)
    t.daemon = True
    t.start()
    
    # Start Bot
    print("🚀 Starting Bot...")
    bot.run()    
