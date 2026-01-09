
import sqlite3
from database import DB_NAME

def run_migration():
    print("Running migration for almacen_reservas...")
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS almacen_reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                refaccion_id INTEGER NOT NULL,
                cliente_id INTEGER,
                cliente_nombre TEXT,
                orden_compra TEXT,
                cantidad INTEGER DEFAULT 0,
                fecha_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active', -- active, fulfilled, cancelled
                FOREIGN KEY (refaccion_id) REFERENCES almacen (id) ON DELETE CASCADE,
                FOREIGN KEY (cliente_id) REFERENCES clients (id) ON DELETE SET NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Migration successful: almacen_reservas table created.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
