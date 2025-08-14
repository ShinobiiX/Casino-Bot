import sqlite3
import shutil
import os

CORRUPT = "casino.db"        # your current (malformed) DB
RECOVERED = "recovered.db"   # output file

# Backup original just in case
shutil.copyfile(CORRUPT, f"{CORRUPT}.backup")

def copy_table(src_conn, dst_conn, table):
    src_cur = src_conn.cursor()
    dst_cur = dst_conn.cursor()
    try:
        # Get column names
        src_cur.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in src_cur.fetchall()]
        col_list = ", ".join(cols)
        for row in src_cur.execute(f"SELECT {col_list} FROM {table}"):
            try:
                placeholders = ", ".join("?" for _ in cols)
                dst_cur.execute(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})", row)
            except Exception:
                # skip rows that are causing issues
                continue
        dst_conn.commit()
    except Exception as e:
        print(f"[!] failed copying {table}: {e}")

def main():
    if not os.path.exists(CORRUPT):
        print(f"[!] Source database '{CORRUPT}' not found.")
        return

    src = sqlite3.connect(CORRUPT)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(RECOVERED)

    # Recreate schema (excluding internal sqlite_ tables)
    for row in src.execute("SELECT sql, name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        sql, name = row["sql"], row["name"]
        if sql:
            try:
                dst.execute(sql)
            except Exception as e:
                print(f"[!] schema recreate for {name} failed: {e}")
    dst.commit()

    # Copy data table by table
    for row in src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        table = row["name"]
        print(f"Copying table: {table}")
        copy_table(src, dst, table)

    src.close()
    dst.close()
    print(f"Recovery attempt complete. Check '{RECOVERED}'.")
    print(f"Original backed up as '{CORRUPT}.backup'.")
    
if __name__ == "__main__":
    main()
