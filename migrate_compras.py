
import sqlite3

DATABASE = "inair_reportes.db"

def migrate():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    print("Iniciando migración del módulo de Compras...")
    
    # 1. Tabla Proveedores
    print("Creando tabla 'proveedores'...")
    c.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_empresa TEXT NOT NULL,
            contacto_nombre TEXT,
            telefono TEXT,
            email TEXT,
            direccion TEXT,
            rfc TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Tabla Compras (Ordenes de Compra)
    print("Creando tabla 'compras'...")
    c.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE,
            proveedor_id INTEGER,
            fecha_emision DATE,
            fecha_entrega_estimada DATE,
            estado TEXT DEFAULT 'Borrador', -- Borrador, Enviada, Recibida, Cancelada
            moneda TEXT DEFAULT 'MXN',
            subtotal REAL DEFAULT 0,
            iva REAL DEFAULT 0,
            total REAL DEFAULT 0,
            notas TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # 3. Tabla Compra Items
    print("Creando tabla 'compra_items'...")
    c.execute('''
        CREATE TABLE IF NOT EXISTS compra_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id INTEGER,
            linea INTEGER,
            numero_parte TEXT,
            descripcion TEXT,
            cantidad REAL,
            unidad TEXT,
            precio_unitario REAL,
            importe REAL,
            FOREIGN KEY (compra_id) REFERENCES compras (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Migración completada exitosamente.")

if __name__ == "__main__":
    migrate()
