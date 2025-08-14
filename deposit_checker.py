import time
import requests
import sqlite3

TON_API_KEY = "AEZREY4SL7EPIXQAAAAK67DYHTTQPTOGBFN2MLLHANGOQLFNM3EX25Z5BU7MSPPYAXNOMPY"  # from tonapi.io
WALLET_ADDRESS = "UQAHUIZi1rgSXTy6lh3ZhJD_3reSIH6nvXs5e1xWKpm1_l-E"  # where users send funds
DB_PATH = "casino.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def update_balance(user_id, amount):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET real_balance = real_balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def check_deposits():
    headers = {"Authorization": f"Bearer {TON_API_KEY}"}
    url = f"https://tonapi.io/v2/blockchain/getTransactions?account={WALLET_ADDRESS}&limit=10"
    resp = requests.get(url, headers=headers)
    data = resp.json()

    if "transactions" not in data:
        return

    for tx in data["transactions"]:
        tx_hash = tx["hash"]
        amount_ton = int(tx["in_msg"]["value"]) / 1e9  # convert nanotons to TON
        comment = tx["in_msg"].get("message", "")

        # The comment will store the Telegram user_id
        if comment.isdigit():
            user_id = int(comment)
            print(f"💰 Deposit detected: {amount_ton} TON from user {user_id}")
            update_balance(user_id, amount_ton)
            mark_as_processed(tx_hash)

def mark_as_processed(tx_hash):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO processed_txs (tx_hash) VALUES (?)", (tx_hash,))
    conn.commit()
    conn.close()

def ensure_tables():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_txs (
            tx_hash TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    ensure_tables()
    while True:
        check_deposits()
        time.sleep(10)  # check every 10 seconds
