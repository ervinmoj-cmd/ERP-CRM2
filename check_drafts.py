import sqlite3

# Open database
conn = sqlite3.connect("inair_reportes.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Check if drafts table exists and what data it has
try:
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='draft_reports'")
    table_exists = c.fetchone()
    
    if table_exists:
        print("✓ draft_reports table exists")
        
        # Get recent drafts
        c.execute("SELECT folio, created_at FROM draft_reports ORDER BY created_at DESC LIMIT 5")
        drafts = c.fetchall()
        
        if drafts:
            print(f"\n✓ Found {len(drafts)} recent drafts:")
            for d in drafts:
                print(f"  - Folio: {d['folio']}, Created: {d['created_at']}")
        else:
            print("\n✗ No drafts found in database")
    else:
        print("✗ draft_reports table does NOT exist")
        
except Exception as e:
    print(f"Error: {e}")

conn.close()
