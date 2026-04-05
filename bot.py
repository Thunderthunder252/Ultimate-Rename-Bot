import os
import asyncio
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# --- 1. KEEP-ALIVE SERVER (FOR RENDER) ---
# This stops the 'Exited with status 1' error
app_server = Flask(__name__)
@app_server.route('/')
def home():
    return "Bot is Running"

def run_server():
    app_server.run(host='0.0.0.0', port=8080)

# --- 2. PYTHON 3.14 PATCH ---
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# --- 3. CONFIGURATION ---
API_ID = 37674103
API_HASH = "f9ecc621ed4865256f94f71a7dd6a1c8"
BOT_TOKEN = "8709295055:AAFDxRIdEO3upWylyGjHasus9mv_ME0o5ik"

bot = Client("rename_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# (Paste your existing command handlers here: start, set_thumbnail, file_received, etc.)

# --- 4. RUN EVERYTHING ---
if __name__ == "__main__":
    # Start the web server in a separate thread
    Thread(target=run_server).start()
    print("🚀 Bot and Server Started!")
    bot.run()
