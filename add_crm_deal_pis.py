import sqlite3

DATABASE = 'inair_reportes.db'

def run_migration():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Creating crm_deal_pis table...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_deal_pis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                pi_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals (id),
                FOREIGN KEY (pi_id) REFERENCES pis (id)
            )
        ''')
        print("crm_deal_pis table created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_migration()
