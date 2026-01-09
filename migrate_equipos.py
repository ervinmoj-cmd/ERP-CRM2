"""
Script de migración para agregar tablas del módulo de equipos
Ejecutar una vez para crear las nuevas tablas
"""
import sqlite3

DB_PATH = "inair_reportes.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabla: Equipos en calendario
    c.execute("""
        CREATE TABLE IF NOT EXISTS equipos_calendario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            serie TEXT NOT NULL UNIQUE,
            tipo_equipo TEXT NOT NULL,
            modelo TEXT,
            marca TEXT,
            potencia TEXT,
            frecuencia_meses INTEGER NOT NULL,
            mes_inicio INTEGER NOT NULL,
            anio_inicio INTEGER NOT NULL,
            tipo_servicio_defecto TEXT,
            activo BOOLEAN DEFAULT 1,
            notas TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)
    
    # Tabla: Catálogo general de refacciones
    c.execute("""
        CREATE TABLE IF NOT EXISTS refacciones_catalogo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_equipo TEXT NOT NULL,
            tipo_servicio TEXT NOT NULL,
            nombre_refaccion TEXT NOT NULL,
            cantidad REAL NOT NULL,
            unidad TEXT,
            UNIQUE(tipo_equipo, tipo_servicio, nombre_refaccion)
        )
    """)
    
    # Tabla: Refacciones custom por equipo
    c.execute("""
        CREATE TABLE IF NOT EXISTS equipos_refacciones_custom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER NOT NULL,
            tipo_servicio TEXT NOT NULL,
            nombre_refaccion TEXT NOT NULL,
            cantidad REAL NOT NULL,
            unidad TEXT,
            FOREIGN KEY (equipo_id) REFERENCES equipos_calendario(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Migración completada: Tablas creadas exitosamente")

if __name__ == "__main__":
    migrate()
