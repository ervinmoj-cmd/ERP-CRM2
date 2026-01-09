"""
Quick script to check if clients have equipment in database
"""
import sqlite3

DATABASE = 'inair_reportes.db'

def check_equipment():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all clients
    cursor.execute('SELECT id, nombre FROM clients ORDER BY nombre LIMIT 10')
    clients = cursor.fetchall()
    
    print("\n" + "="*60)
    print("CLIENTES Y SUS EQUIPOS")
    print("="*60 + "\n")
    
    for client in clients:
        cursor.execute('SELECT COUNT(*) as count FROM client_equipment WHERE client_id = ?', (client['id'],))
        count = cursor.fetchone()['count']
        
        print(f"Cliente: {client['nombre']}")
        print(f"  ID: {client['id']}")
        print(f"  Equipos: {count}")
        
        if count > 0:
            cursor.execute('''
                SELECT tipo_equipo, modelo, serie 
                FROM client_equipment 
                WHERE client_id = ? 
                LIMIT 3
            ''', (client['id'],))
            equipos = cursor.fetchall()
            for eq in equipos:
                print(f"    - {eq['tipo_equipo']} | {eq['modelo']} | {eq['serie']}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_equipment()
