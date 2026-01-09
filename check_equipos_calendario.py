"""
Check equipos_calendario structure
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
    print(f"{col['name']:20} {col['type']:15} {'NOT NULL' if col['notnull'] else ''}")

# Get sample data
print("\n" + "="*60)
print("EJEMPLOS (primeros 5):")
print("="*60 + "\n")

cursor.execute("SELECT * FROM equipos_calendario LIMIT 5")
equipos = cursor.fetchall()

for eq in equipos:
    print(dict(eq))
    print()

# Check if there's a client_id or similar
cursor.execute('''
    SELECT DISTINCT 
        CASE 
            WHEN cliente_id IS NOT NULL THEN 'cliente_id'
            WHEN client_id IS NOT NULL THEN 'client_id'
            ELSE 'otro'
        END as client_column
    FROM equipos_calendario
''')

conn.close()
