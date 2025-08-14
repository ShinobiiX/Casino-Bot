# handlers/start.py

import datetime
from aiogram import types, Dispatcher
from database import cursor, conn  # Make sure you have this file that sets up your DB connection

async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        now = datetime.datetime.now().isoformat()
        cursor.execute("INSERT INTO users (user_id, username, last_demo_refill) VALUES (?, ?, ?)",
                       (user_id, username, now))
        conn.commit()
        await message.answer("🎉 Welcome to the Casino Bot!\nYou’ve received 1000 demo credits to try out the games!")
    else:
        await message.answer("Welcome back 🎰\nUse /games to see what you can play!")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'])
