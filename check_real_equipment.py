"""
Find which clients have equipment in equipos_calendario
"""
import sqlite3

conn = sqlite3.connect('inair_reportes.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all unique client names from equipos_calendario
cursor.execute('''
    SELECT DISTINCT *
    FROM equipos_calendario 
    LIMIT 5
''')

equipos = cursor.fetchall()

print("\n📋 PRIMEROS 5 EQUIPOS EN equipos_calendario:")
print("="*60)

for eq in equipos:
    data = dict(eq)
    print("\n🔧 Equipo:")
    for key, value in sorted(data.items()):
        if value and key not in ['created_at', 'updated_at']:
            print(f"  {key}: {value}")

conn.close()
