"""
Get equipos_calendario structure
"""
import sqlite3

DATABASE = 'inair_reportes.db'

conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get table structure
cursor.execute("PRAGMA table_info(equipos_calendario)")
columns = cursor.fetchall()

print("\n" + "="*60)
print("ESTRUCTURA DE equipos_calendario:")
print("="*60 + "\n")

for col in columns:
    print(f"{col['name']:25} {col['type']:15}")

# Get sample data
print("\n" + "="*60)
print("EJEMPLOS (primeros 3):")
print("="*60 + "\n")

cursor.execute("SELECT * FROM equipos_calendario LIMIT 3")
equipos = cursor.fetchall()

for eq in equipos:
    data = dict(eq)
    for key, value in data.items():
        if value:  # Only show non-null values
            print(f"  {key}: {value}")
    print()

conn.close()
