import os
import asyncio
import time
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER ---
app_server = Flask(__name__)
@app_server.route('/')
def home():
    return "Bot is Live"

def run_server():
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

bot = Client("thunder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_thumbnails = {}

# --- 4. STABILIZED PROGRESS BAR ---
async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        progress = "[{0}{1}]".format(
            ''.join(["▰" for i in range(int(percentage // 10))]),
            ''.join(["▱" for i in range(10 - int(percentage // 10))])
        )
        tmp = f"📥 **{ud_type}**\n{progress} **{round(percentage, 2)}%**"
        try:
            if message:
                await message.edit(tmp)
        except:
            pass

# --- 5. AUTO-DELETE ---
async def delete_after_delay(client, chat_id, message_ids, delay):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, message_ids)
    except:
        pass 

# --- 6. HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(f"✨ **Welcome {message.from_user.first_name}!**\n\n📸 Send a Photo for a thumb.\n📁 Send a File to rename.")

@bot.on_message(filters.photo & filters.private)
async def set_thumbnail(client, message):
    user_id = message.from_user.id
    path = os.path.join(os.getcwd(), f"thumb_{user_id}.jpg")
    await message.download(file_name=path)
    user_thumbnails[user_id] = path
    await message.reply_text("✅ **Thumbnail Saved Successfully!**")

@bot.on_message((filters.document | filters.video) & filters.private)
async def file_received(client, message):
    user_id = message.from_user.id
    file_name = message.document.file_name if message.document else (message.video.file_name if message.video else "File")
    user_thumbnails[f"file_{user_id}"] = message
    await message.reply_text(f"📝 **File Received!**\n\n📂 **Old Name:** `{file_name}`\n\n✨ Send the **NEW NAME** now.")

@bot.on_message(filters.text & filters.private & ~filters.command("start"))
async def rename_process(client, message):
    user_id = message.from_user.id
    file_key = f"file_{user_id}"
    if file_key not in user_thumbnails: return

    new_name = message.text
    old_file_msg = user_thumbnails[file_key]
    thumb = user_thumbnails.get(user_id)

    status = await message.reply_text("📥 **Starting Process...**")
    try:
        start_time = time.time()
        file_path = await client.download_media(
            message=old_file_msg,
            progress=progress_for_pyrogram,
            progress_args=("Downloading", status, start_time)
        )
        
        await status.edit("📤 **Starting Upload...**")
        start_time = time.time()
        
        # 1. SEND THE FILE (Caption is ONLY the new name)
        sent_file = await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            file_name=new_name,
            thumb=thumb if thumb and os.path.exists(thumb) else None,
            caption=f"{new_name}", # Caption is strictly the name
            force_document=True,
            progress=progress_for_pyrogram,
            progress_args=("Uploading", status, start_time)
        )
        
        # 2. SEND THE SEPARATE WARNING MESSAGE (Minimal text)
        warning_text = await message.reply_text(
            f"⚠️ **WARNING:** _This file will be deleted in 10 minutes!_"
        )
        
        await status.delete()
        if os.path.exists(file_path): os.remove(file_path)
        del user_thumbnails[file_key]
        
        # Auto-delete BOTH
        asyncio.create_task(delete_after_delay(client, message.chat.id, [sent_file.id, warning_text.id], 600))

    except Exception as e:
        if status: await status.edit(f"❌ **Error:** `{str(e)}`")

# --- 7. START ---
if __name__ == "__main__":
    t = Thread(target=run_server)
    t.daemon = True
    t.start()
    print("🚀 Thunder Bot is Live!")
    bot.run()
