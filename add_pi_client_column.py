import sqlite3

DATABASE = "inair_reportes.db"

def add_columns():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(pis)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'cliente_id' not in columns:
            print("Adding cliente_id column...")
            cursor.execute("ALTER TABLE pis ADD COLUMN cliente_id INTEGER")
            
        if 'cliente_nombre' not in columns:
            print("Adding cliente_nombre column...")
            cursor.execute("ALTER TABLE pis ADD COLUMN cliente_nombre TEXT")
            
        conn.commit()
        print("Migration successful: Columns added to pis table.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_columns()
