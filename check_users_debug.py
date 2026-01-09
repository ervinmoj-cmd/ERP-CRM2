import sqlite3

def check_users():
    db_name = 'inair_reportes.db'
    print(f"Connecting to {db_name}...")
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check schema
    print("Schema of users table:")
    c.execute("PRAGMA table_info(users)")
    columns = [row['name'] for row in c.fetchall()]
    print(columns)
    
    # Check users
    print("\nTargeted Users:")
    query_cols = ['id', 'username', 'nombre']
    if 'email' in columns:
        query_cols.append('email')
    if 'email_smtp' in columns:
        query_cols.append('email_smtp')
    if 'puesto' in columns:
        query_cols.append('puesto')
        
    cols_str = ', '.join(query_cols)
    
    # Filter for relevant users
    print(f"Querying columns: {cols_str}")
    
    where_clauses = []
    where_clauses.append("username LIKE '%admin%'")
    if 'puesto' in columns:
        where_clauses.append("puesto LIKE '%Admin%'")
    if 'email' in columns:
        where_clauses.append("email LIKE '%pedidos%'")
        where_clauses.append("email LIKE '%inair%'")
        
    where_str = " OR ".join(where_clauses)
    
    query = f"SELECT {cols_str} FROM users WHERE {where_str}"
    print(f"Query: {query}")
    
    try:
        c.execute(query)
        results = c.fetchall()
        for row in results:
            print(dict(row))
            
        if not results:
            print("No matching users found with targeted query.")
            # Fallback: print first 5 users
            print("First 5 users:")
            c.execute(f"SELECT {cols_str} FROM users LIMIT 5")
            for row in c.fetchall():
                print(dict(row))
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    check_users()
