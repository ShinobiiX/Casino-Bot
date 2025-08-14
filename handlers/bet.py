from aiogram import types, Dispatcher
from database import conn
import random

cursor = conn.cursor()

async def cmd_bet(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    if not args:
        await message.answer("💡 Usage: `/bet amount` (e.g., `/bet 100`)", parse_mode="Markdown")
        return

    try:
        bet_amount = float(args)
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a number.", parse_mode="Markdown")
        return

    # Get current demo balance
    cursor.execute("SELECT demo_balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if not result:
        await message.answer("❌ You're not registered. Use /start first.")
        return

    demo_balance = result[0]

    if bet_amount <= 0:
        await message.answer("❌ Bet amount must be greater than zero.")
        return

    if bet_amount > demo_balance:
        await message.answer("🚫 You don’t have enough demo balance.")
        return

    # Game Logic: 50/50 chance
    win = random.choice([True, False])
    if win:
        winnings = bet_amount
        new_balance = demo_balance + winnings
        result_text = f"🎉 You won `{winnings}` demo credits!"
    else:
        winnings = -bet_amount
        new_balance = demo_balance + winnings
        result_text = f"😢 You lost `{bet_amount}` demo credits."

    # Update DB
    cursor.execute("UPDATE users SET demo_balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()

    await message.answer(
        f"{result_text}\n\n💳 New Demo Balance: `{new_balance}`",
        parse_mode="Markdown"
    )

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_bet, commands=["bet"])
