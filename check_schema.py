import sqlite3

def check_schema():
    try:
        conn = sqlite3.connect("inair_reportes.db")
        c = conn.cursor()
        c.execute("PRAGMA table_info(equipos)")
        columns = c.fetchall()
        print("Schema for 'equipos':")
        for col in columns:
            print(col)
        
        print("\nSchema for 'clientes':")
        c.execute("PRAGMA table_info(clientes)")
        columns = c.fetchall()
        for col in columns:
            print(col)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
