import sqlite3

DATABASE = 'inair_reportes.db'

def migrate():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # 1. Add 'clasificacion' column to 'equipos_calendario'
    try:
        c.execute("ALTER TABLE equipos_calendario ADD COLUMN clasificacion TEXT DEFAULT 'General'")
        print("Column 'clasificacion' added to 'equipos_calendario'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'clasificacion' already exists in 'equipos_calendario'.")
        else:
            print(f"Error adding column: {e}")

    # 2. Create 'equipos_kits' table
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS equipos_kits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipo_id INTEGER NOT NULL,
                tipo_servicio TEXT NOT NULL,
                refacciones_json TEXT,
                FOREIGN KEY (equipo_id) REFERENCES equipos_calendario (id) ON DELETE CASCADE
            )
        """)
        print("Table 'equipos_kits' created (or already exists).")
    except Exception as e:
        print(f"Error creating table 'equipos_kits': {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
