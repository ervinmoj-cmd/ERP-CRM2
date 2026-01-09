import sqlite3

def update_admin_email():
    db_name = 'inair_reportes.db'
    print(f"Connecting to {db_name}...")
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    new_email = 'ervin.moj@gmail.com'
    
    # Update by username
    print(f"Updating email for user 'admin' to {new_email}...")
    try:
        c.execute("UPDATE users SET email = ?, email_smtp = ? WHERE username = 'admin'", (new_email, new_email))
        print(f"Rows updated (username='admin'): {c.rowcount}")
    except Exception as e:
        print(f"Error updating by username: {e}")
        
    # Update by puesto (just in case)
    print(f"Updating email for puesto 'Administrador' to {new_email}...")
    try:
        c.execute("UPDATE users SET email = ?, email_smtp = ? WHERE puesto = 'Administrador'", (new_email, new_email))
        print(f"Rows updated (puesto='Administrador'): {c.rowcount}")
    except Exception as e:
        print(f"Error updating by puesto: {e}")

    conn.commit()
    conn.close()
    print("Database update complete.")

if __name__ == "__main__":
    update_admin_email()
