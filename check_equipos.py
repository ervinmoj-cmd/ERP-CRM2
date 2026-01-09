import sqlite3

conn = sqlite3.connect("inair_reportes.db")
c = conn.cursor()

# Ver equipos
c.execute("SELECT * FROM equipos_calendario")
equipos = c.fetchall()

print(f"Total equipos: {len(equipos)}")
for eq in equipos:
    print(eq)

conn.close()
