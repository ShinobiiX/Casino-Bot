import random
import sqlite3
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher import FSMContext
from handlers.states import ColorGuessStates
from handlers import game_menu  # 🆕 Required for back_to_menu

DB_PATH = "casino.db"

COLORS = ["🔴 Red", "🔵 Blue", "🟢 Green", "🟡 Yellow", "🟣 Purple", "🟠 Orange", "⚫ Black", "⚪ White", "🟤 Brown", "🟥 Pink"]

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def get_user_balances(user_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT demo_balance, real_balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (None, None)

def update_balance(user_id, balance_type, new_amount):
    conn = get_conn()
    cursor = conn.cursor()
    if balance_type == "demo":
        cursor.execute("UPDATE users SET demo_balance = ? WHERE user_id = ?", (new_amount, user_id))
    else:
        cursor.execute("UPDATE users SET real_balance = ? WHERE user_id = ?", (new_amount, user_id))
    conn.commit()
    conn.close()

# /color command or callback
async def cmd_color_guess(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎲 Demo Balance", callback_data="cg_balance_demo"),
        InlineKeyboardButton("💰 Real Balance", callback_data="cg_balance_real")
    )
    await message.answer(
        "🎨 *Color Guess Game!*\nChoose balance to use:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await ColorGuessStates.choosing_balance.set()

# Balance chosen
async def color_balance_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    balance_type = "demo" if "demo" in callback.data else "real"
    user_id = callback.from_user.id
    demo, real = get_user_balances(user_id)
    current = demo if balance_type == "demo" else real

    if current is None:
        await callback.message.answer("❌ You're not registered. Use /start first.")
        await state.finish()
        return

    await state.update_data(balance_type=balance_type)
    await callback.message.answer(
        f"You picked *{balance_type}* balance.\nYour current balance is `{current}`.\n\nEnter your bet amount:",
        parse_mode="Markdown"
    )
    await ColorGuessStates.entering_bet.set()

# Bet entered
async def color_bet_entered(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    balance_type = data.get("balance_type")

    try:
        bet = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid bet. Enter a number.")
        return

    if bet <= 0:
        await message.answer("❌ Bet must be more than zero.")
        return

    demo, real = get_user_balances(user_id)
    current = demo if balance_type == "demo" else real

    if bet > current:
        await message.answer(f"🚫 Insufficient {balance_type} balance. You have `{current}`.")
        return

    await state.update_data(bet_amount=bet)

    kb = InlineKeyboardMarkup(row_width=2)
    for color in COLORS:
        kb.add(InlineKeyboardButton(color, callback_data=f"color_{color.split()[-1].lower()}"))
    
    await message.answer("🎨 Pick a color:", reply_markup=kb)
    await ColorGuessStates.guessing_color.set()

# Color guessed and result
async def color_guessed(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    data = await state.get_data()
    balance_type = data.get("balance_type")
    bet = data.get("bet_amount")

    guess_color = callback.data.split("_")[1]

    winning_colors = random.sample([c.split()[-1].lower() for c in COLORS], 3)
    bot_pick = random.choice(winning_colors)
    won = guess_color == bot_pick
    reward = bet * 3 if won else 0

    demo, real = get_user_balances(user_id)
    current = demo if balance_type == "demo" else real
    new_balance = current - bet + reward

    update_balance(user_id, balance_type, new_balance)

    # 🆕 Add replay & menu buttons
    buttons = InlineKeyboardMarkup(row_width=2)
    buttons.add(
        InlineKeyboardButton("🔁 Play Again", callback_data="cg_play_again"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="cg_back_to_menu")
    )

    await callback.message.answer(
        f"🎯 You picked: `{guess_color.title()}`\n"
        f"🎲 Winning color: `{bot_pick.title()}`\n"
        f"{'🎉 You WON!' if won else '💔 You lost!'}\n\n"
        f"{'💰 Reward: `' + str(reward) + '`' if won else ''}\n"
        f"💳 New {balance_type} balance: `{new_balance}`",
        parse_mode="Markdown",
        reply_markup=buttons
    )
    await state.finish()

# 🆕 Replay handler
async def play_again_color_guess(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_color_guess(callback.message)

# 🆕 Back to menu handler
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await game_menu.cmd_games(callback.message)

# From game menu
async def menu_to_color_guess(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_color_guess(callback.message)

# Register
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_color_guess, commands=["colorguess"], state="*")
    dp.register_callback_query_handler(menu_to_color_guess, lambda c: c.data == "game_color_guess", state="*")
    dp.register_callback_query_handler(color_balance_chosen, lambda c: c.data.startswith("cg_balance_"), state=ColorGuessStates.choosing_balance)
    dp.register_message_handler(color_bet_entered, state=ColorGuessStates.entering_bet)
    dp.register_callback_query_handler(color_guessed, lambda c: c.data.startswith("color_"), state=ColorGuessStates.guessing_color)
    # 🆕 Register new buttons
    dp.register_callback_query_handler(play_again_color_guess, lambda c: c.data == "cg_play_again", state="*")
    dp.register_callback_query_handler(back_to_menu, lambda c: c.data == "cg_back_to_menu", state="*")
