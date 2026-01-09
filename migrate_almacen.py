import sqlite3
from database import DB_NAME

def migrate_db():
    print(f"Migrating {DB_NAME}...")
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("ALTER TABLE almacen ADD COLUMN ubicacion_especifica TEXT")
            print("✅ Added column 'ubicacion_especifica'")
        except sqlite3.OperationalError as e:
            print(f"ℹ️ Column might already exist: {e}")
            
        conn.commit()
        conn.close()
        print("Migration completed.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_db()
