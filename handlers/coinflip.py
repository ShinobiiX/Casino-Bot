import random
import sqlite3
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher import FSMContext
from handlers.states import CoinflipStates
from handlers import game_menu  # 🆕 Import game menu
from datetime import datetime

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

# Entry: /coinflip or via menu callback "game_coinflip"
async def cmd_coinflip(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🪙 Demo Balance", callback_data="cf_balance_demo"),
        InlineKeyboardButton("💰 Real Balance", callback_data="cf_balance_real")
    )
    await message.answer(
        "🎲 **Coinflip Game**\nChoose which balance to play with:", 
        parse_mode="Markdown", 
        reply_markup=kb
    )
    await CoinflipStates.choosing_balance.set()

# Balance selection
async def balance_chosen(callback: CallbackQuery, state: FSMContext):
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
        f"You picked *{balance_type}* balance. Your current {balance_type} balance is `{current}`.\nEnter your bet amount:",
        parse_mode="Markdown"
    )
    await CoinflipStates.entering_bet.set()

# Bet amount input
async def bet_amount_entered(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    balance_type = data.get("balance_type")
    if not balance_type:
        await message.answer("Flow broken. Start again with /coinflip.")
        await state.finish()
        return

    try:
        bet_amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid bet. Send a number.")
        return

    if bet_amount <= 0:
        await message.answer("❌ Bet must be greater than zero.")
        return

    demo_balance, real_balance = get_user_balances(user_id)
    current = demo_balance if balance_type == "demo" else real_balance

    if bet_amount > current:
        await message.answer(f"🚫 Insufficient {balance_type} balance. You have `{current}`.")
        return

    await state.update_data(bet_amount=bet_amount)

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🪙 Heads", callback_data="cf_side_heads"),
        InlineKeyboardButton("🪙 Tails", callback_data="cf_side_tails")
    )
    await message.answer(
        f"You're betting `{bet_amount}` on *{balance_type}* balance. Pick Heads or Tails:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await CoinflipStates.choosing_side.set()

# Side chosen and resolve
async def side_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    data = await state.get_data()
    balance_type = data.get("balance_type")
    bet_amount = data.get("bet_amount")

    if not balance_type or bet_amount is None:
        await callback.message.answer("Flow broken. Start again with /coinflip.")
        await state.finish()
        return

    user_choice = "heads" if "heads" in callback.data else "tails"
    result = random.choice(["heads", "tails"])

    demo_balance, real_balance = get_user_balances(user_id)
    current = demo_balance if balance_type == "demo" else real_balance

    if user_choice == result:
        new_balance = current + bet_amount
        outcome = f"🎉 It was *{result.upper()}*! You won +{bet_amount} on *{balance_type}*."
    else:
        new_balance = current - bet_amount
        new_balance = max(new_balance, 0)
        outcome = f"😞 It was *{result.upper()}*. You lost -{bet_amount} on *{balance_type}*."

    update_balance(user_id, balance_type, new_balance)

    # 🆕 Add result buttons
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔁 Play Again", callback_data="cf_play_again"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="cf_back_to_menu")
    )

    await callback.message.answer(
        outcome + f"\n\n💳 New {balance_type.capitalize()} Balance: `{new_balance}`",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await state.finish()

# 🆕 Handle "Play Again"
async def play_again_coinflip(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_coinflip(callback.message)

# 🆕 Handle "Back to Menu"
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await game_menu.cmd_games(callback.message)

# Wrapper for /games menu
async def menu_to_coinflip(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_coinflip(callback.message)

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_coinflip, commands=["coinflip"], state="*")
    dp.register_callback_query_handler(menu_to_coinflip, lambda c: c.data == "game_coinflip", state="*")
    dp.register_callback_query_handler(
        balance_chosen,
        lambda c: c.data.startswith("cf_balance_"),
        state=CoinflipStates.choosing_balance
    )
    dp.register_message_handler(bet_amount_entered, state=CoinflipStates.entering_bet)
    dp.register_callback_query_handler(
        side_chosen,
        lambda c: c.data.startswith("cf_side_"),
        state=CoinflipStates.choosing_side
    )
    # 🆕 Register new buttons
    dp.register_callback_query_handler(play_again_coinflip, lambda c: c.data == "cf_play_again", state="*")
    dp.register_callback_query_handler(back_to_menu, lambda c: c.data == "cf_back_to_menu", state="*")
