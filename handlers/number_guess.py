import random
import sqlite3
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher import FSMContext
from handlers.states import NumberGuessStates
from handlers import game_menu  # ✅ Needed for back_to_menu

DB_PATH = "casino.db"

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
    column = "demo_balance" if balance_type == "demo" else "real_balance"
    cursor.execute(f"UPDATE users SET {column} = ? WHERE user_id = ?", (new_amount, user_id))
    conn.commit()
    conn.close()

# Entry: /guess or callback
async def cmd_number_guess(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎲 Demo Balance", callback_data="ng_balance_demo"),
        InlineKeyboardButton("💰 Real Balance", callback_data="ng_balance_real")
    )
    await message.answer(
        "🎯 *Number Guess Game!*\nChoose balance to use:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await NumberGuessStates.choosing_balance.set()

# Handle balance choice
async def balance_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    balance_type = "demo" if "demo" in callback.data else "real"
    user_id = callback.from_user.id
    demo_balance, real_balance = get_user_balances(user_id)
    current = demo_balance if balance_type == "demo" else real_balance

    if current is None:
        await callback.message.answer("❌ You're not registered. Use /start first.")
        await state.finish()
        return

    await state.update_data(balance_type=balance_type)
    await callback.message.answer(
        f"You picked *{balance_type}* balance.\nYour current balance is `{current}`.\n\nEnter your bet amount:",
        parse_mode="Markdown"
    )
    await NumberGuessStates.entering_bet.set()

# Handle bet amount
async def bet_amount_entered(message: types.Message, state: FSMContext):
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
    await message.answer("🔢 Pick a number between 1 and 10:")
    await NumberGuessStates.guessing_number.set()

# Handle number guess
async def number_guessed(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    balance_type = data.get("balance_type")
    bet = data.get("bet_amount")

    try:
        guess = int(message.text.strip())
        if not (1 <= guess <= 10):
            raise ValueError
    except ValueError:
        await message.answer("❌ Enter a number *between 1 and 10*.")
        return

    win_numbers = random.sample(range(1, 11), k=3)
    bot_choice = random.choice(win_numbers)
    won = guess == bot_choice
    reward = bet * 3 if won else 0

    demo, real = get_user_balances(user_id)
    current = demo if balance_type == "demo" else real
    new_balance = current - bet + reward
    update_balance(user_id, balance_type, new_balance)

    # ✅ Add replay/menu buttons
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔁 Play Again", callback_data="ng_play_again"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="ng_back_to_menu")
    )

    await message.answer(
        f"🎯 You guessed: `{guess}`\n"
        f"🎲 Winning number: `{bot_choice}`\n"
        f"{'🎉 You WON!' if won else '💔 You lost!'}\n\n"
        f"{'💰 Reward: `' + str(reward) + '`' if won else ''}\n"
        f"💳 New {balance_type} balance: `{new_balance}`",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await state.finish()

# ✅ Replay
async def play_again_number_guess(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_number_guess(callback.message)

# ✅ Back to Menu
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await game_menu.cmd_games(callback.message)

# From inline menu
async def menu_to_number_guess(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_number_guess(callback.message)

# Register all handlers
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_number_guess, commands=["guess"], state="*")
    dp.register_callback_query_handler(menu_to_number_guess, lambda c: c.data == "game_number_guess", state="*")
    dp.register_callback_query_handler(balance_chosen, lambda c: c.data.startswith("ng_balance_"), state=NumberGuessStates.choosing_balance)
    dp.register_message_handler(bet_amount_entered, state=NumberGuessStates.entering_bet)
    dp.register_message_handler(number_guessed, state=NumberGuessStates.guessing_number)

    # ✅ New Buttons
    dp.register_callback_query_handler(play_again_number_guess, lambda c: c.data == "ng_play_again", state="*")
    dp.register_callback_query_handler(back_to_menu, lambda c: c.data == "ng_back_to_menu", state="*")
