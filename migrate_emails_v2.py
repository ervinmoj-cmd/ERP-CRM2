import sqlite3
import os
from database import get_db

DATABASE = 'inair_reportes.db'
SQL_FILE = os.path.join('queries', 'schema_updates_emails_v2.sql')

def migrate():
    print(f"🔄 Starting migration from {SQL_FILE}...")
    
    if not os.path.exists(SQL_FILE):
        print(f"❌ Error: File {SQL_FILE} not found!")
        return

    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
        print("✅ Migration completed successfully!")
        
        # Verify
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM crm_module_templates")
            count_tpl = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM crm_deal_message_overrides")
            count_overrides = cursor.fetchone()[0]
            print(f"📊 Templates: {count_tpl}, Overrides: {count_overrides}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
