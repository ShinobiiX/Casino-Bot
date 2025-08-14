import sqlite3

# Connect to (or create) the database
conn = sqlite3.connect("casino.db")  # Change this name if you're using a different one
cursor = conn.cursor()

# Create the users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    demo_balance REAL DEFAULT 1000,
    real_balance REAL DEFAULT 0,
    last_demo_reset DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Save and close
conn.commit()
conn.close()

print("✅ Database and users table created successfully.")
