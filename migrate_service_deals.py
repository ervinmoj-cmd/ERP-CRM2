"""
Migración: Agregar soporte para Tratos de Servicio
- Agrega tabla crm_deal_equipos
- Agrega tabla crm_deal_tecnicos
- Agrega columnas a crm_deals para servicios
- Agrega deal_id a draft_reports y reports
"""
import sqlite3

DATABASE = 'inair_reportes.db'

def run_migration():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("🚀 Iniciando migración de Tratos de Servicio...")
    
    # 1. Crear tabla crm_deal_equipos
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_deal_equipos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                tipo_equipo TEXT NOT NULL,
                modelo TEXT,
                serie TEXT,
                descripcion_servicio TEXT,
                detalles_adicionales TEXT,
                orden INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals(id) ON DELETE CASCADE
            )
        ''')
        print("✅ Tabla crm_deal_equipos creada")
    except Exception as e:
        print(f"⚠️ Error creando crm_deal_equipos: {e}")
    
    # 2. Crear tabla crm_deal_tecnicos
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_deal_tecnicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                tecnico_id INTEGER NOT NULL,
                asignado_por INTEGER,
                puntos REAL DEFAULT 0,
                asignado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals(id) ON DELETE CASCADE,
                FOREIGN KEY (tecnico_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (asignado_por) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE(deal_id, tecnico_id)
            )
        ''')
        print("✅ Tabla crm_deal_tecnicos creada")
    except Exception as e:
        print(f"⚠️ Error creando crm_deal_tecnicos: {e}")
    
    # 3. Agregar columnas a crm_deals
    columnas_crm_deals = [
        ("tipo_deal", "TEXT DEFAULT 'venta'"),
        ("fecha_servicio", "DATE"),
        ("tiempo_estimado_horas", "REAL")
    ]
    
    for columna, tipo in columnas_crm_deals:
        try:
            cursor.execute(f"ALTER TABLE crm_deals ADD COLUMN {columna} {tipo}")
            print(f"✅ Columna '{columna}' agregada a crm_deals")
        except sqlite3.OperationalError:
            print(f"ℹ️ Columna '{columna}' ya existe en crm_deals")
    
    # 4. Agregar deal_id a draft_reports
    try:
        cursor.execute("ALTER TABLE draft_reports ADD COLUMN deal_id INTEGER REFERENCES crm_deals(id)")
        print("✅ Columna 'deal_id' agregada a draft_reports")
    except sqlite3.OperationalError:
        print("ℹ️ Columna 'deal_id' ya existe en draft_reports")
    
    # 5. Agregar deal_id a reports
    try:
        cursor.execute("ALTER TABLE reports ADD COLUMN deal_id INTEGER REFERENCES crm_deals(id)")
        print("✅ Columna 'deal_id' agregada a reports")
    except sqlite3.OperationalError:
        print("ℹ️ Columna 'deal_id' ya existe en reports")
    
    # 6. Crear índices para mejorar rendimiento
    indices = [
        ("idx_deal_equipos_deal", "crm_deal_equipos", "deal_id"),
        ("idx_deal_tecnicos_deal", "crm_deal_tecnicos", "deal_id"),
        ("idx_deal_tecnicos_tecnico", "crm_deal_tecnicos", "tecnico_id"),
        ("idx_draft_reports_deal", "draft_reports", "deal_id"),
        ("idx_reports_deal", "reports", "deal_id")
    ]
    
    for idx_name, tabla, columna in indices:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tabla}({columna})")
            print(f"✅ Índice '{idx_name}' creado")
        except Exception as e:
            print(f"⚠️ Error creando índice {idx_name}: {e}")
    
    conn.commit()
    
    # Verificar resultados
    print("\n📊 Verificando migración...")
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='crm_deal_equipos'")
    if cursor.fetchone()[0] > 0:
        print("✅ crm_deal_equipos: OK")
    
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='crm_deal_tecnicos'")
    if cursor.fetchone()[0] > 0:
        print("✅ crm_deal_tecnicos: OK")
    
    cursor.execute("PRAGMA table_info(crm_deals)")
    columnas = [col[1] for col in cursor.fetchall()]
    if 'tipo_deal' in columnas:
        print("✅ crm_deals.tipo_deal: OK")
    if 'fecha_servicio' in columnas:
        print("✅ crm_deals.fecha_servicio: OK")
    if 'tiempo_estimado_horas' in columnas:
        print("✅ crm_deals.tiempo_estimado_horas: OK")
    
    conn.close()
    print("\n🎉 Migración completada exitosamente!")

if __name__ == "__main__":
    run_migration()
