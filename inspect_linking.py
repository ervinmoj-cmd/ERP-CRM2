import sqlite3

DATABASE = 'inair_reportes.db'

def get_table_info(table_name):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    print(f"\n--- {table_name} ---")
    for col in columns:
        print(col)

get_table_info('cotizaciones')
get_table_info('pis')
get_table_info('deals')
get_table_info('deal_cotizaciones') # Check if this exists
get_table_info('deal_pis') # Check if this exists
