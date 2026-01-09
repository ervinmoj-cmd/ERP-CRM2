"""
Find all tables with equipment data
"""
import sqlite3

DATABASE = 'inair_reportes.db'

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\nBuscando tablas relacionadas con equipos:\n")
for table in tables:
    table_name = table[0]
    if 'equip' in table_name.lower():
        print(f"✓ {table_name}")
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  Registros: {count}\n")

print("\n" + "="*60)
print("VERIFICANDO client_equipment:")
print("="*60)
cursor.execute("SELECT COUNT(*) as total FROM client_equipment")
total = cursor.fetchone()[0]
print(f"Total registros: {total}")

if total > 0:
    cursor.execute("SELECT * FROM client_equipment LIMIT 5")
    rows = cursor.fetchall()
    cursor.execute("PRAGMA table_info(client_equipment)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"\nColumnas: {', '.join(columns)}")
    print("\nPrimeros registros:")
    for row in rows:
        print(row)

conn.close()
