import os
import threading
from flask import Flask
from bot import bot

app = Flask(__name__)

@app.route('/')
def hello():
    return "Bot is running!"

def run_bot():
    print("Starting bot polling...")
    # non_stop=True ensures it keeps running, and timeout=60 is good for long polling
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == '__main__':
    # When running locally for testing, we can just run the script directly.
    # We spawn the bot polling in a separate daemon thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
else:
    # When running under gunicorn, __name__ != '__main__'
    # We still need to spawn the bot
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
