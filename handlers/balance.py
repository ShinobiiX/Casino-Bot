from aiogram import types, Dispatcher
from database import conn, cursor
from utils.balance_utils import ensure_demo_refill
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers import game_menu  # so we can call your games menu handler

# Replace this with your actual wallet
WALLET_ADDRESS = "UQAHUIZi1rgSXTy6lh3ZhJD_3reSIH6nvXs5e1xWKpm1_l-E"

# Balance Command Handler
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id

    # auto-refill demo if interval passed
    demo_balance = ensure_demo_refill(user_id)

    # fetch balances
    cursor.execute("SELECT demo_balance, real_balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        demo, real = result

        # Inline keyboard for Deposit + Back
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(
            InlineKeyboardButton("➕ Deposit via Wallet", callback_data="deposit_wallet"),
            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
        )

        await message.answer(
            f"💳 *Your Balances:*\n\n"
            f"🧪 Demo: `{demo}`\n"
            f"💰 Real: `{real}`\n\n"
            f"You can top-up your real balance below 👇",
            parse_mode="Markdown",
            reply_markup=kb
        )
    else:
        await message.answer("❌ You are not registered yet. Type /start to register.")

# Callback Handler for Deposit Button
async def deposit_via_wallet(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id

    await callback.message.answer(
        f"💼 *Deposit Instructions:*\n\n"
        f"1. Send TON to this wallet:\n`{WALLET_ADDRESS}`\n"
        f"2. In the transaction *comment*, put this number:\n`{user_id}`\n"
        f"3. ✅ The bot will detect your deposit and credit your account automatically.\n\n"
        f"⚠️ Make sure you include the correct comment or the bot won't know it's you.",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# Callback Handler for Back Button
async def back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    await game_menu.cmd_games(callback.message)  # sends them to games menu

# Register Handlers
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_balance, commands=["balance"])
    dp.register_callback_query_handler(deposit_via_wallet, lambda c: c.data == "deposit_wallet")
    dp.register_callback_query_handler(back_to_menu, lambda c: c.data == "back_to_menu")
