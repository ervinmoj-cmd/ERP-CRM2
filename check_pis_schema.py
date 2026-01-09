
import sqlite3

def check_pis_schema():
    conn = sqlite3.connect('inair_reportes.db')
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(pis)")
        columns = cursor.fetchall()
        if not columns:
            print("Table 'pis' does not exist.")
        else:
            print("Columns in 'pis' table:")
            found = False
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
                if col[1] == 'solicitado_por':
                    found = True
            
            if found:
                print("\nSUCCESS: 'solicitado_por' column exists.")
            else:
                print("\nWARNING: 'solicitado_por' column MISSING.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_pis_schema()
