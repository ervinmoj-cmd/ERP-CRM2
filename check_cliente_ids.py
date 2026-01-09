"""
Check what cliente_id values exist
"""
import sqlite3

conn = sqlite3.connect('inair_reportes.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Count equipment per cliente_id
cursor.execute('''
    SELECT cliente_id, COUNT(*) as count
    FROM equipos_calendario
    GROUP BY cliente_id
    ORDER BY count DESC
''')

results = cursor.fetchall()

print("\n📊 EQUIPOS POR cliente_id:")
print("="*60)

for row in results:
    cid = row['cliente_id']
    count = row['count']
    
    # Get client name
    cursor.execute('SELECT nombre FROM clients WHERE id = ?', (cid,))
    client = cursor.fetchone()
    client_name = client['nombre'] if client else '❌ NO EXISTE EN clients'
    
    print(f"cliente_id {cid:3}: {count:2} equipos | {client_name}")

conn.close()
