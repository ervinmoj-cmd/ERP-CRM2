import sqlite3

DATABASE = 'inair_reportes.db'

# Test updating a PI item status
conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get first PI item
cursor.execute("SELECT * FROM pi_items LIMIT 1")
item = cursor.fetchone()

if item:
    print(f"Item encontrado:")
    print(f"  ID: {item['id']}")
    print(f"  Número de parte: {item['numero_parte']}")
    print(f"  Estatus actual: {item['estatus']}")
    
    # Try to update
    new_status = 'En Tránsito' if item['estatus'] != 'En Tránsito' else 'Recibido'
    print(f"\nIntentando cambiar estatus a: {new_status}")
    
    cursor.execute("UPDATE pi_items SET estatus = ? WHERE id = ?", (new_status, item['id']))
    conn.commit()
    
    # Verify
    cursor.execute("SELECT estatus FROM pi_items WHERE id = ?", (item['id'],))
    updated = cursor.fetchone()
    print(f"Estatus después de actualizar: {updated['estatus']}")
    
    if updated['estatus'] == new_status:
        print("✓ Actualización exitosa")
    else:
        print("✗ Actualización falló")
else:
    print("No hay items de PI en la base de datos")

conn.close()
