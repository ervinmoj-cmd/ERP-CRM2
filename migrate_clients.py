import sqlite3

SOURCE_DB = "inair.db"
TARGET_DB = "inair_reportes.db"

def migrate_clients():
    print(f"Migrating clients from {SOURCE_DB} to {TARGET_DB}...")
    
    try:
        source_conn = sqlite3.connect(SOURCE_DB)
        source_conn.row_factory = sqlite3.Row
        source_c = source_conn.cursor()
        
        target_conn = sqlite3.connect(TARGET_DB)
        target_c = target_conn.cursor()
        
        # Get all clients from source
        source_c.execute("SELECT * FROM clients")
        clients = source_c.fetchall()
        
        print(f"Found {len(clients)} clients in source DB.")
        
        migrated_count = 0
        for client in clients:
            # Check if exists in target
            target_c.execute("SELECT id FROM clients WHERE id = ?", (client['id'],))
            if target_c.fetchone():
                print(f"Client ID {client['id']} ({client['nombre']}) already exists. Skipping.")
            else:
                print(f"Migrating Client ID {client['id']} ({client['nombre']})...")
                target_c.execute("""
                    INSERT INTO clients (id, nombre, contacto, telefono, email, direccion, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    client['id'],
                    client['nombre'],
                    client['contacto'],
                    client['telefono'],
                    client['email'],
                    client['direccion'],
                    client['created_at']
                ))
                migrated_count += 1
        
        target_conn.commit()
        print(f"Migration complete. Migrated {migrated_count} clients.")
        
        source_conn.close()
        target_conn.close()
        
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_clients()
