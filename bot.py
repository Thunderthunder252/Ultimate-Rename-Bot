import os
import asyncio
import sys
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER (FOR RENDER HEARTBEAT) ---
app_server = Flask(__name__)
@app_server.route('/')
def home():
    return "Bot is Live"

def run_server():
    # Render uses port 8080 or 10000; Flask will listen on 8080
    app_server.run(host='0.0.0.0', port=8080)

# --- 2. PYTHON 3.14 COMPATIBILITY ---
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# --- 3. CONFIGURATION ---
# Ensure these match your Telegram Developer details
API_ID = 37674103
API_HASH = "f9ecc621ed4865256f94f71a7dd6a1c8"
# Use the NEW token you got from @BotFather
BOT_TOKEN = "8709295055:AAHOv4sHtQA6eletK7jc1Nw1REeajbadYNQ"

bot = Client("rename_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# In-memory storage for file references and thumbnails
user_thumbnails = {}

# --- 4. HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        f"✨ **Welcome {message.from_user.first_name}!**\n\n"
        "1️⃣ Send a **Photo** to set as a thumbnail.\n"
        "2️⃣ Send a **File** to rename it."
    )

@bot.on_message(filters.photo & filters.private)
async def set_thumbnail(client, message):
    user_id = message.from_user.id
    # Absolute path ensures Render finds the file during the upload phase
    path = os.path.join(os.getcwd(), f"thumb_{user_id}.jpg")
    
    status = await message.reply_text("⏳ **Saving Thumbnail...**")
    try:
        await message.download(file_name=path)
        user_thumbnails[user_id] = path
        await status.edit("✅ **Thumbnail Saved Successfully!**")
    except Exception as e:
        await status.edit(f"❌ **Error saving thumb:** `{str(e)}`")

@bot.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def file_received(client, message):
    user_id = message.from_user.id
    # Store the entire message object to access it later for downloading
    user_thumbnails[f"file_{user_id}"] = message
    await message.reply_text(
        "📝 **File Received!**\n\n"
        "Now send me the **NEW NAME** (Example: `MyVideo.mp4`).\n"
        "**Note:** You MUST include the file extension!"
    )

@bot.on_message(filters.text & filters.private & ~filters.command("start"))
async def rename_process(client, message):
    user_id = message.from_user.id
    file_key = f"file_{user_id}"
    
    # If the user hasn't sent a file yet, ignore the text
    if file_key not in user_thumbnails:
        return

    new_name = message.text
    old_file_msg = user_thumbnails[file_key]
    thumb_path = user_thumbnails.get(user_id)

    # SAFETY CHECK: If the thumb file was deleted by Render's cleanup, skip it
    if thumb_path and not os.path.exists(thumb_path):
        thumb_path = None

    status = await message.reply_text("📥 **Downloading to Server...**")
    
    try:
        # Download the original file
        file_path = await client.download_media(old_file_msg)
        
        await status.edit("📤 **Uploading with New Name...**")
        
        # Upload renamed file with thumbnail (if exists)
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            file_name=new_name,
            thumb=thumb_path,
            caption=f"✅ **Renamed Successfully!**\n`{new_name}`"
        )
        
        await status.delete()
        
        # CLEANUP: Remove the downloaded file to save space on Render
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Clear the file reference so the user can send a new one
        del user_thumbnails[file_key]
        
    except Exception as e:
        await status.edit(f"❌ **Rename Error:** `{str(e)}`")

# --- 5. STARTING THE ENGINE ---
if __name__ == "__main__":
    # Run Flask in a background thread to satisfy Render's Port binding
    t = Thread(target=run_server)
    t.daemon = True
    t.start()
    
    print("🚀 Bot and Server are Online!")
    bot.run()
