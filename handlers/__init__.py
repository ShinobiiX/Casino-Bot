from handlers.start import register_handlers as register_start
from handlers.balance import register_handlers as register_balance
from handlers.bet import register_handlers as register_bet

def register_all_handlers(dp):
    register_start(dp)
    register_balance(dp)
    register_bet(dp)
