import random
import sqlite3
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher import FSMContext
from handlers.states import BowlingStates
from handlers import game_menu  # Needed to access the game menu

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

# Entry point for /bowling command or menu callback
async def cmd_bowling(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎳 Demo Balance", callback_data="bowl_balance_demo"),
        InlineKeyboardButton("💰 Real Balance", callback_data="bowl_balance_real")
    )
    await message.answer(
        "🎯 *Bowling Game*\nChoose a balance to play with:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await BowlingStates.choosing_balance.set()

# Handle balance type selection
async def bowling_balance_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    balance_type = "demo" if "demo" in callback.data else "real"
    user_id = callback.from_user.id
    demo_balance, real_balance = get_user_balances(user_id)
    current = demo_balance if balance_type == "demo" else real_balance

    if current is None:
        await callback.message.answer("❌ You are not registered. Use /start first.")
        await state.finish()
        return

    await state.update_data(balance_type=balance_type)
    await callback.message.answer(
        f"You picked *{balance_type}* balance. You have `{current}` points.\nEnter your bet amount:",
        parse_mode="Markdown"
    )
    await BowlingStates.entering_bet.set()

# Handle bet amount input
async def bowling_bet_entered(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    balance_type = data.get("balance_type")

    try:
        bet = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid number. Please enter a valid bet amount.")
        return

    if bet <= 0:
        await message.answer("🚫 Bet must be greater than 0.")
        return

    demo_balance, real_balance = get_user_balances(user_id)
    current = demo_balance if balance_type == "demo" else real_balance

    if bet > current:
        await message.answer(f"❌ You don’t have enough {balance_type} balance. Current: `{current}`")
        return

    # Roll the ball (random pins 0-10)
    pins_knocked = random.randint(0, 10)
    win = pins_knocked >= 7
    new_balance = current + bet if win else current - bet
    new_balance = max(new_balance, 0)

    update_balance(user_id, balance_type, new_balance)

    if win:
        msg = f"🎳 *Strike!* You knocked down {pins_knocked} pins!\n🎉 You won `{bet}`!"
    else:
        msg = f"😓 Only {pins_knocked} pins... You lost `{bet}`."

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔁 Play Again", callback_data="bowl_play_again"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="bowl_back_to_menu")
    )

    await message.answer(
        msg + f"\n\n💼 New {balance_type.capitalize()} Balance: `{new_balance}`",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await state.finish()

# Handle "Play Again"
async def play_again_bowling(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_bowling(callback.message)

# Handle "Back to Menu"
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await game_menu.cmd_games(callback.message)

# Wrapper for /games callback button
async def menu_to_bowling(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_bowling(callback.message)

# Register handlers
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_bowling, commands=["bowling"], state="*")
    dp.register_callback_query_handler(menu_to_bowling, lambda c: c.data == "game_bowling", state="*")
    dp.register_callback_query_handler(
        bowling_balance_chosen,
        lambda c: c.data.startswith("bowl_balance_"),
        state=BowlingStates.choosing_balance
    )
    dp.register_message_handler(bowling_bet_entered, state=BowlingStates.entering_bet)

    # NEW: register play again & back to menu buttons
    dp.register_callback_query_handler(play_again_bowling, lambda c: c.data == "bowl_play_again", state="*")
    dp.register_callback_query_handler(back_to_menu, lambda c: c.data == "bowl_back_to_menu", state="*")
