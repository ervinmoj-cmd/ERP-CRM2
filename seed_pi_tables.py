
import sqlite3
from database import DB_NAME

def seed_pi_tables():
    print("Creating PI (Proforma Invoice) tables...")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. PI Master Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE NOT NULL,
            fecha DATE NOT NULL,
            proveedor_id INTEGER,
            proveedor_nombre TEXT,
            atencion_a TEXT,
            referencia TEXT,
            orden_compra_id INTEGER,
            moneda TEXT DEFAULT 'USD',
            tipo_cambio REAL DEFAULT 1.0,
            tiempo_entrega TEXT,
            condiciones_pago TEXT,
            notas TEXT,
            subtotal REAL DEFAULT 0.0,
            iva_porcentaje REAL DEFAULT 16.0,
            iva_monto REAL DEFAULT 0.0,
            total REAL DEFAULT 0.0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    print("Created table: pis")

    # 2. PI Items Table with Status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pi_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pi_id INTEGER NOT NULL,
            linea INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            unidad TEXT,
            numero_parte TEXT,
            descripcion TEXT,
            estatus TEXT DEFAULT 'Pendiente', 
            tiempo_entrega_item TEXT,
            precio_unitario REAL NOT NULL,
            importe REAL NOT NULL,
            FOREIGN KEY (pi_id) REFERENCES pis (id) ON DELETE CASCADE
        )
    ''')
    print("Created table: pi_items")

    # 3. Folios for PIs (Using 'PI' prefix)
    cursor.execute("INSERT OR IGNORE INTO folios (prefijo, ultimo_numero) VALUES ('PI', 0)")
    print("Initialized PI folio counter")

    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    seed_pi_tables()
