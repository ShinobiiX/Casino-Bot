from aiogram import types, Dispatcher

WALLET_ADDRESS = "UQAHUIZi1rgSXTy6lh3ZhJD_3reSIH6nvXs5e1xWKpm1_l-E"  # Replace with your real TON wallet

async def cmd_deposit(message: types.Message):
    user_id = message.from_user.id
    await message.answer(
        f"💳 Send TON to:\n`{WALLET_ADDRESS}`\n\n"
        f"📌 IMPORTANT: Put this number in the transaction comment:\n`{user_id}`\n\n"
        f"✅ Funds will be credited automatically after confirmation.",
        parse_mode="Markdown"
    )

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_deposit, commands=["deposit"])
