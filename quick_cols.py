import sqlite3
conn = sqlite3.connect('inair_reportes.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(equipos_calendario)")
cols = cursor.fetchall()
for col in cols:
    print(f"{col[1]:30} {col[2]}")
conn.close()
