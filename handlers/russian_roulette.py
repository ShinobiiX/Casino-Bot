import random
import sqlite3
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher import FSMContext
from handlers.states import RussianRouletteStates
from handlers import game_menu  # ✅ For "Back to Menu"

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

# /roulette command or callback
async def cmd_russian_roulette(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎲 Demo Balance", callback_data="rr_balance_demo"),
        InlineKeyboardButton("💰 Real Balance", callback_data="rr_balance_real")
    )
    await message.answer(
        "🔫 *Russian Roulette!*\nChoose balance to use:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await RussianRouletteStates.choosing_balance.set()

# Handle balance selection
async def roulette_balance_chosen(callback: CallbackQuery, state: FSMContext):
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
    await RussianRouletteStates.entering_bet.set()

# Handle bet entry
async def roulette_bet_entered(message: types.Message, state: FSMContext):
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

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("😰 Pull the trigger!", callback_data="rr_pull"))
    await message.answer("🧠 Spinning the chamber...\n\nAre you ready?", reply_markup=kb)
    await RussianRouletteStates.ready_to_fire.set()

# Handle outcome
async def trigger_pulled(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    data = await state.get_data()
    balance_type = data.get("balance_type")
    bet = data.get("bet_amount")

    win_chambers = random.sample(range(1, 7), k=2)
    fired_chamber = random.randint(1, 6)
    survived = fired_chamber in win_chambers
    reward = bet * 3 if survived else 0

    demo, real = get_user_balances(user_id)
    current = demo if balance_type == "demo" else real
    new_balance = current - bet + reward

    update_balance(user_id, balance_type, new_balance)

    # ✅ Add Replay + Menu buttons
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔁 Play Again", callback_data="rr_play_again"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="rr_back_to_menu")
    )

    await callback.message.answer(
        f"🔫 Chamber: `{fired_chamber}`\n"
        f"💥 {'💀 BANG! You survived!' if survived else '☠️ BANG! You lost your bet.'}\n\n"
        f"{'💰 Reward: `' + str(reward) + '`' if survived else ''}\n"
        f"💳 New {balance_type} balance: `{new_balance}`",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await state.finish()

# ✅ Replay handler
async def play_again_russian_roulette(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_russian_roulette(callback.message)

# ✅ Back to Menu handler
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await game_menu.cmd_games(callback.message)

# From inline menu
async def menu_to_roulette(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_russian_roulette(callback.message)

# Register
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_russian_roulette, commands=["roulette"], state="*")
    dp.register_callback_query_handler(menu_to_roulette, lambda c: c.data == "game_russian_roulette", state="*")
    dp.register_callback_query_handler(roulette_balance_chosen, lambda c: c.data.startswith("rr_balance_"), state=RussianRouletteStates.choosing_balance)
    dp.register_message_handler(roulette_bet_entered, state=RussianRouletteStates.entering_bet)
    dp.register_callback_query_handler(trigger_pulled, lambda c: c.data == "rr_pull", state=RussianRouletteStates.ready_to_fire)

    # ✅ New replay/menu handlers
    dp.register_callback_query_handler(play_again_russian_roulette, lambda c: c.data == "rr_play_again", state="*")
    dp.register_callback_query_handler(back_to_menu, lambda c: c.data == "rr_back_to_menu", state="*")
