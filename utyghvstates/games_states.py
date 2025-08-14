from aiogram.dispatcher.filters.state import State, StatesGroup

class GameStates(StatesGroup):
    waiting_for_bet = State()
