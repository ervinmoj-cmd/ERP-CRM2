
import sqlite3

DB_NAME = "inair_reportes.db"

def add_cotizacion_id_column():
    print("Adding 'cotizacion_id' column to 'pis' table...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE pis ADD COLUMN cotizacion_id INTEGER")
        print("Column 'cotizacion_id' added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'cotizacion_id' already exists.")
        else:
            print(f"Error: {e}")
            
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    add_cotizacion_id_column()
