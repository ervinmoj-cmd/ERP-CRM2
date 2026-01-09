import sqlite3

try:
    conn = sqlite3.connect("inair_reportes.db")
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print("Tablas encontradas:")
    for t in tables:
        print(f" - {t[0]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
