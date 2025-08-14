from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, balance, game_menu, game  # make sure these expose register_handlers
from handlers.coinflip import register_handlers as register_coinflip
from handlers.bowling import register_handlers as register_bowling
from handlers.basketball import register_handlers as register_basketball
from handlers.number_guess import register_handlers as register_number_guess
from handlers.color_guess import register_handlers as register_color_guess
from handlers.russian_roulette import register_handlers as register_russian_roulette
from handlers import deposit




import logging

logging.basicConfig(level=logging.INFO)

# Core objects
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Register handlers (order doesn’t hugely matter)
start.register_handlers(dp)
balance.register_handlers(dp)
game_menu.register_handlers(dp)
game.register_handlers(dp)          # generic stub if still used
deposit.register_handlers(dp)
register_coinflip(dp)               # coinflip FSM flow
register_bowling(dp)               # coinflip FSM flow
register_basketball(dp)
register_number_guess(dp)
register_color_guess(dp)
register_russian_roulette(dp)


# Set visible bot commands
async def set_commands():
    await bot.set_my_commands([
        types.BotCommand("start", "Start the bot"),
        types.BotCommand("games", "Show games menu"),
        types.BotCommand("balance", "Check your balances"),
        # types.BotCommand("coinflip", "Play coinflip"),
    ])

if __name__ == "__main__":
    async def on_startup(_):
        await set_commands()

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
