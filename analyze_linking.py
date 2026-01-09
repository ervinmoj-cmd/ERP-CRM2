"""
Auto-link equipment to clients by updating cliente_id
This assumes equipos_calendario rows already have some client reference
"""
import sqlite3

conn = sqlite3.connect('inair_reportes.db')
cursor = conn.cursor()

print("\n🔗 AUTO-LINKING EQUIPOS TO CLIENTS")
print("="*60)

# Strategy: If cliente_id is already set (not NULL), we'll verify it's correct
# If it's NULL or invalid, we need another way to identify the client

# First, check how many have NULL or invalid cliente_id
cursor.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN cliente_id IS NULL THEN 1 ELSE 0 END) as nulls,
        SUM(CASE WHEN cliente_id IS NOT NULL THEN 1 ELSE 0 END) as has_value
    FROM equipos_calendario
''')

stats = cursor.fetchone()
print(f"\n📊 ESTADÍSTICAS:")
print(f"  Total equipos: {stats[0]}")
print(f"  Con cliente_id NULL: {stats[1]}")
print(f"  Con cliente_id definido: {stats[2]}")

# Check if cliente_id values match existing clients
cursor.execute('''
    SELECT DISTINCT e.cliente_id, c.nombre
    FROM equipos_calendario e
    LEFT JOIN clients c ON e.cliente_id = c.id
    WHERE e.cliente_id IS NOT NULL
    ORDER BY e.cliente_id
''')

print(f"\n🔍 VERIFICACIÓN DE cliente_id EXISTENTES:")
for row in cursor.fetchall():
    cid, name = row
    status = "✅" if name else "❌ NO EXISTE"
    print(f"  cliente_id {cid}: {status} {name or ''}")

conn.close()

print("\n" + "="*60)
print("💡 SOLUCIÓN:")
print("Si los cliente_id ya están correctos, solo falta actualizar los NULL.")
print("Si hay equipos sin cliente_id, necesitas decirme cómo identificar")
print("a qué cliente pertenecen (¿hay otro campo? ¿serie? ¿nombre?).")
