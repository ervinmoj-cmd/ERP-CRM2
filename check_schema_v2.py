import sqlite3

def check_schema():
    try:
        conn = sqlite3.connect("inair_reportes.db")
        c = conn.cursor()
        
        tables_to_check = ["equipos_calendario", "clients", "clientes", "refacciones_catalogo", "equipos_refacciones_custom"]
        
        for table in tables_to_check:
            print(f"\nSchema for '{table}':")
            c.execute(f"PRAGMA table_info({table})")
            columns = c.fetchall()
            if not columns:
                print("  (Table not found)")
            else:
                for col in columns:
                    print(f"  {col}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
