"""
Enhanced Service Deal Equipment - Photos and Comments
Adds tables for:
- Equipment photos (up to 10 per equipment)
- Equipment comments (chat-style with images)
"""
import sqlite3

DATABASE = 'inair_reportes.db'

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Table for equipment photos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_deal_equipo_fotos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipo_id INTEGER NOT NULL,
                foto_data TEXT NOT NULL,
                descripcion TEXT,
                uploaded_by INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                orden INTEGER DEFAULT 0,
                FOREIGN KEY (equipo_id) REFERENCES crm_deal_equipos (id) ON DELETE CASCADE,
                FOREIGN KEY (uploaded_by) REFERENCES users (id)
            )
        ''')
        print("✅ Tabla crm_deal_equipo_fotos creada")
        
        # Table for equipment comments (chat-style)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_deal_equipo_comentarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipo_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                mensaje TEXT NOT NULL,
                imagen_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipo_id) REFERENCES crm_deal_equipos (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("✅ Tabla crm_deal_equipo_comentarios creada")
        
        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_equipo_fotos ON crm_deal_equipo_fotos(equipo_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_equipo_comentarios ON crm_deal_equipo_comentarios(equipo_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comentarios_created ON crm_deal_equipo_comentarios(created_at DESC)')
        
        print("✅ Índices creados")
        
        conn.commit()
        print("\n🎉 Migración completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
