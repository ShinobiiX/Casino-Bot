from datetime import datetime, timedelta
from database import cursor, conn

DEMO_RESET_INTERVAL = timedelta(days=2)
DEFAULT_DEMO = 1000

def ensure_demo_refill(user_id):
    cursor.execute("SELECT demo_balance, last_demo_refill FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None  # user not registered; caller should handle

    demo_balance, last_refill = row
    if last_refill:
        try:
            last = datetime.fromisoformat(last_refill)
        except Exception:
            last = datetime.min
    else:
        last = datetime.min

    now = datetime.now()
    if now - last >= DEMO_RESET_INTERVAL:
        cursor.execute(
            "UPDATE users SET demo_balance = ?, last_demo_refill = ? WHERE user_id = ?",
            (DEFAULT_DEMO, now.isoformat(), user_id)
        )
        conn.commit()
        return DEFAULT_DEMO
    return demo_balance
