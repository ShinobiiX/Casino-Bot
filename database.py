# database.py
import sqlite3
from datetime import datetime

DB_PATH = "casino.db"  # new clean DB

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    demo_balance REAL DEFAULT 1000,
    real_balance REAL DEFAULT 0,
    last_demo_refill TEXT,
    wallet_address TEXT,
    referral_by TEXT,
    is_banned INTEGER DEFAULT 0
)
''')

# Transactions log (optional but useful)
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    amount REAL,
    balance_type TEXT,
    status TEXT,
    timestamp TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS game_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    game TEXT,
    balance_type TEXT,
    bet_amount REAL,
    result TEXT,
    payout REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS cooldowns (
    user_id INTEGER,
    game TEXT,
    last_played DATETIME,
    PRIMARY KEY (user_id, game)
)
''')

conn.commit()
