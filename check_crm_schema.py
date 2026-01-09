import sqlite3

conn = sqlite3.connect('inair_reportes.db')
cursor = conn.cursor()

# Get crm_deals table structure
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='crm_deals'")
result = cursor.fetchone()

if result:
    print("=== CRM_DEALS TABLE SCHEMA ===")
    print(result[0])
    print("\n")
    
    # Get all columns
    cursor.execute("PRAGMA table_info(crm_deals)")
    columns = cursor.fetchall()
    print("=== COLUMNS ===")
    for col in columns:
        print(f"{col[1]} ({col[2]})")
else:
    print("Table crm_deals not found!")

# Check users table for puesto column
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("\n=== USERS TABLE COLUMNS ===")
for col in columns:
    print(f"{col[1]} ({col[2]})")

conn.close()
