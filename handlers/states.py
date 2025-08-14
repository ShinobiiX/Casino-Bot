from aiogram.dispatcher.filters.state import State, StatesGroup

class CoinflipStates(StatesGroup):
    choosing_balance = State()
    entering_bet = State()
    choosing_side = State()

class BowlingStates(StatesGroup):
    choosing_balance = State()
    entering_bet = State()
    
    
class BasketballStates(StatesGroup):
    choosing_balance = State()
    entering_bet = State()
    
class NumberGuessStates(StatesGroup):
    choosing_balance = State()
    entering_bet = State()
    guessing_number = State()
    

class ColorGuessStates(StatesGroup):
    choosing_balance = State()
    entering_bet = State()
    guessing_color = State()
    

class RussianRouletteStates(StatesGroup):
    choosing_balance = State()
    entering_bet = State()
    ready_to_fire = State()