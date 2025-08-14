import random
import sqlite3
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher import FSMContext
from handlers.states import BasketballStates
from handlers import game_menu  # Ensure this is your main menu handler

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
    if balance_type == "demo":
        cursor.execute("UPDATE users SET demo_balance = ? WHERE user_id = ?", (new_amount, user_id))
    else:
        cursor.execute("UPDATE users SET real_balance = ? WHERE user_id = ?", (new_amount, user_id))
    conn.commit()
    conn.close()

# Entry point: /basketball or "game_basketball" callback
async def cmd_basketball(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🏀 Demo Balance", callback_data="bb_balance_demo"),
        InlineKeyboardButton("💰 Real Balance", callback_data="bb_balance_real")
    )
    await message.answer(
        "🏀 *Basketball Challenge!*\nChoose which balance to use:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await BasketballStates.choosing_balance.set()

# Balance selected
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
        f"You picked *{balance_type}* balance.\nCurrent {balance_type} balance: `{current}`\n\nEnter your bet amount:",
        parse_mode="Markdown"
    )
    await BasketballStates.entering_bet.set()

# Bet entered
async def bet_amount_entered(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    balance_type = data.get("balance_type")

    try:
        bet_amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid bet amount. Please send a number.")
        return

    if bet_amount <= 0:
        await message.answer("❌ Bet must be greater than zero.")
        return

    demo_balance, real_balance = get_user_balances(user_id)
    current = demo_balance if balance_type == "demo" else real_balance

    if bet_amount > current:
        await message.answer(f"🚫 Insufficient {balance_type} balance. You have `{current}`.")
        return

    # Simulate 3 shots (30% chance per shot)
    shots = [random.random() < 0.3 for _ in range(3)]
    made = shots.count(True)
    reward = made * bet_amount * 2
    new_balance = current - bet_amount + reward

    update_balance(user_id, balance_type, new_balance)

    symbols = ['✅' if shot else '❌' for shot in shots]
    shots_display = "\n".join([f"Shot {i+1}: {symbol}" for i, symbol in enumerate(symbols)])

    if made == 0:
        result_msg = "😢 All missed! Better luck next time."
    elif made == 3:
        result_msg = "🔥 Perfect shots! You nailed all three!"
    else:
        result_msg = f"🏀 You scored {made}/3 shots."

    # Buttons for play again or back
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔁 Play Again", callback_data="bb_play_again"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
    )

    await message.answer(
        f"{shots_display}\n\n"
        f"{result_msg}\n"
        f"💵 Reward: `{reward}`\n"
        f"💳 New {balance_type} balance: `{new_balance}`",
        parse_mode="Markdown",
        reply_markup=kb
    )

    await state.finish()

# 🔁 Play Again
async def play_again(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_basketball(callback.message)

# 🔙 Back to Menu
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await game_menu.cmd_games(callback.message)

# Callback shortcut from menu
async def menu_to_basketball(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_basketball(callback.message)

# Register all handlers
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_basketball, commands=["basketball"], state="*")
    dp.register_callback_query_handler(menu_to_basketball, lambda c: c.data == "game_basketball", state="*")
    dp.register_callback_query_handler(
        balance_chosen,
        lambda c: c.data.startswith("bb_balance_"),
        state=BasketballStates.choosing_balance
    )
    dp.register_message_handler(bet_amount_entered, state=BasketballStates.entering_bet)

    # New handlers
    dp.register_callback_query_handler(play_again, lambda c: c.data == "bb_play_again", state="*")
    dp.register_callback_query_handler(back_to_menu, lambda c: c.data == "back_to_menu", state="*")
