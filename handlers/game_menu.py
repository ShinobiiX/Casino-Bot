# handlers/game_menu.py

from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def cmd_games(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🪙 Coinflip", callback_data="game_coinflip"),
        InlineKeyboardButton("🎳 Bowling", callback_data="game_bowling"),
        InlineKeyboardButton("🏀 Basketball", callback_data="game_basketball"),
        InlineKeyboardButton("🔢 Number Guess", callback_data="game_number_guess"),
        InlineKeyboardButton("🎨 Color Guess", callback_data="game_color_guess"),
        InlineKeyboardButton("🔫 Russian Roulette", callback_data="game_russian_roulette")
    )
    await message.answer("🎮 Choose a game to play:", reply_markup=kb)

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_games, commands=["games"])
