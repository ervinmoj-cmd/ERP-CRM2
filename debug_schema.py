import sqlite3

def check_schema():
    print("Checking database schema...")
    try:
        conn = sqlite3.connect('inair_reportes.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('compras', 'compra_items', 'proveedores')")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables found: {tables}")
        
        if 'compras' in tables:
            print("\nSchema for 'compras':")
            cursor.execute("PRAGMA table_info(compras)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col['cid']}: {col['name']} ({col['type']})")
                
        if 'compra_items' in tables:
            print("\nSchema for 'compra_items':")
            cursor.execute("PRAGMA table_info(compra_items)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col['cid']}: {col['name']} ({col['type']})")
                
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_schema()
