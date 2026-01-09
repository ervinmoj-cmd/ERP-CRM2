
import sqlite3

DB_NAME = "inair_reportes.db"

def add_solicitado_por_column():
    print("Adding 'solicitado_por' column to 'pis' table...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE pis ADD COLUMN solicitado_por TEXT")
        print("Column 'solicitado_por' added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'solicitado_por' already exists.")
        else:
            print(f"Error: {e}")
            
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    add_solicitado_por_column()
