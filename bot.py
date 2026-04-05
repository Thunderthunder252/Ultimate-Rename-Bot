import os
import asyncio
import time
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER (FOR RENDER HEARTBEAT) ---
app_server = Flask(__name__)
@app_server.route('/')
def home():
    return "Bot is Live"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app_server.run(host='0.0.0.0', port=port)

# --- 2. PYTHON 3.14 COMPATIBILITY ---
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

# --- 4. PROGRESS BAR HELPER ---
async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(elapsed_time)
        estimated_total_time = TimeFormatter(estimated_total_time)

        progress = "[{0}{1}] \n**Progress**: {2}%\n".format(
            ''.join(["▰" for i in range(os.path.floor(percentage / 10))]),
            ''.join(["▱" for i in range(10 - os.path.floor(percentage / 10))]),
            round(percentage, 2))

        tmp = progress + "**{0}**: {1} of {2}\n**Speed**: {3}/s\n**ETA**: {4}\n".format(
            ud_type,
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(text="{}\n {}".format("📥 Processing...", tmp))
        except:
            pass

def humanbytes(size):
    if not size: return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

# --- 5. AUTO-DELETE FUNCTION ---
async def delete_after_delay(client, chat_id, message_id, delay):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, message_id)
    except Exception:
        pass 

# --- 6. HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        f"✨ **Welcome {message.from_user.first_name}!**\n\n"
        "📸 Send a **Photo** for a thumbnail.\n"
        "📁 Send a **File** to rename."
    )

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
    await message.reply_text(
        f"📝 **File Received!**\n\n📂 **Old Name:** `{file_name}`\n\n"
        " (✨ **Tip:** Tap the name above to copy it, then send me the **NEW NAME** (with extension).)"
    )

@bot.on_message(filters.text & filters.private & ~filters.command("start"))
async def rename_process(client, message):
    user_id = message.from_user.id
    file_key = f"file_{user_id}"
    if file_key not in user_thumbnails: return

    new_name = message.text
    old_file_msg = user_thumbnails[file_key]
    thumb = user_thumbnails.get(user_id)

    status = await message.reply_text("📥 **Processing...**")
    try:
        start_time = time.time()
        # DOWNLOAD WITH PROGRESS
        file_path = await client.download_media(
            message=old_file_msg,
            progress=progress_for_pyrogram,
            progress_args=("Downloading", status, start_time)
        )
        
        await status.edit("📤 **Uploading...**")
        start_time = time.time()
        
        # UPLOAD WITH PROGRESS
        sent_file = await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            file_name=new_name,
            thumb=thumb if thumb and os.path.exists(thumb) else None,
            caption=(
                f"✅ **RENAMED BY THUNDER RENAME BOT**\n\n"
                f"📂 **New Name:** `{new_name}`\n\n"
                f"⚠️ **WARNING:** _This file will be automatically deleted from this chat in 10 minutes for security Reasons!_"
            ),
            force_document=True,
            progress=progress_for_pyrogram,
            progress_args=("Uploading", status, start_time)
        )
        
        await status.delete()
        if os.path.exists(file_path): os.remove(file_path)
        del user_thumbnails[file_key]

        asyncio.create_task(delete_after_delay(client, message.chat.id, sent_file.id, 600))

    except Exception as e:
        await status.edit(f"❌ **Error:** `{str(e)}`")

# --- 7. START ---
if __name__ == "__main__":
    t = Thread(target=run_server)
    t.daemon = True
    t.start()
    print("🚀 Thunder Bot is Live!")
    bot.run()
