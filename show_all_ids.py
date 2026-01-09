"""
Show ALL cliente_id values
"""
import sqlite3

conn = sqlite3.connect('inair_reportes.db')
cursor = conn.cursor()

cursor.execute('SELECT DISTINCT cliente_id FROM equipos_calendario ORDER BY cliente_id')
ids = [row[0] for row in cursor.fetchall()]

print(f"\n📋 DISTINTOS cliente_id en equipos_calendario:")
print(f"="*60)
print(f"\nTotal IDs distintos: {len(ids)}")
print(f"IDs: {ids}")

# Show count for each
for cid in ids:
    cursor.execute('SELECT COUNT(*) FROM equipos_calendario WHERE cliente_id = ?', (cid,))
    count = cursor.fetchone()[0]
    
    cursor.execute('SELECT nombre FROM clients WHERE id = ?', (cid,))
    client = cursor.fetchone()
    name = client[0] if client else "NO EXISTE"
    
    print(f"\ncliente_id {cid}: {count} equipos ({name})")

conn.close()
