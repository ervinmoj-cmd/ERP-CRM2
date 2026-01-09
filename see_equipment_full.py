"""
See full structure of equipos_calendario to find client identifier
"""
import sqlite3

conn = sqlite3.connect('inair_reportes.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get first 3 equipos with ALL columns
cursor.execute('SELECT * FROM equipos_calendario LIMIT 3')
equipos = cursor.fetchall()

print("\n📋 PRIMEROS 3 EQUIPOS (TODAS LAS COLUMNAS):")
print("="*60)

for i, eq in enumerate(equipos, 1):
    print(f"\n🔧 EQUIPO {i}:")
    data = dict(eq)
    for key, value in sorted(data.items()):
        if value is not None:
            print(f"  {key:30} = {value}")

conn.close()
