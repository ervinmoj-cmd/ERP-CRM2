"""
Verify equipos_calendario has cliente_id column
"""
import sqlite3

conn = sqlite3.connect('inair_reportes.db')
cursor = conn.cursor()

print("\n📋 ESTRUCTURA DE equipos_calendario:")
print("="*60)

cursor.execute("PRAGMA table_info(equipos_calendario)")
columns = cursor.fetchall()

for col in columns:
    cid, name, ctype, notnull, default, pk = col
    print(f"{name:30} {ctype:15} {'PK' if pk else ''}")

print("\n🔍 PROBANDO QUERY:")
print("="*60)

try:
    cursor.execute('''
        SELECT id, cliente_id, tipo_equipo, modelo, serie
        FROM equipos_calendario
        WHERE cliente_id = 1
        LIMIT 3
    ''')
    
    results = cursor.fetchall()
    print(f"\nResultados para cliente_id=1: {len(results)} equipos\n")
    
    for row in results:
        print(f"  ID: {row[0]} | Cliente: {row[1]} | {row[2]} | {row[3]} | {row[4]}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")

conn.close()
