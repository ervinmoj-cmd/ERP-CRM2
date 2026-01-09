import sqlite3

DATABASE = 'inair_reportes.db'

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Check if table exists
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='crm_deal_pis'
""")
result = cursor.fetchone()

if result:
    print("✓ Tabla crm_deal_pis existe")
    
    # Check structure
    cursor.execute("PRAGMA table_info(crm_deal_pis)")
    columns = cursor.fetchall()
    print("\nEstructura:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
    
    # Count links
    cursor.execute("SELECT COUNT(*) FROM crm_deal_pis")
    count = cursor.fetchone()[0]
    print(f"\nTotal vinculaciones: {count}")
else:
    print("✗ ERROR: Tabla crm_deal_pis NO existe")

conn.close()
