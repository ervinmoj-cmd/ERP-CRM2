"""
Check ALL equipment in database
"""
import sqlite3

DATABASE = 'inair_reportes.db'

def check_all_equipment():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get total equipment count
    cursor.execute('SELECT COUNT(*) as total FROM client_equipment')
    total = cursor.fetchone()['total']
    
    print(f"\n{'='*60}")
    print(f"TOTAL EQUIPOS EN BASE DE DATOS: {total}")
    print(f"{'='*60}\n")
    
    # Get clients WITH equipment
    cursor.execute('''
        SELECT c.id, c.nombre, COUNT(e.id) as equipo_count
        FROM clients c
        INNER JOIN client_equipment e ON c.id = e.client_id
        GROUP BY c.id, c.nombre
        ORDER BY equipo_count DESC
    ''')
    
    clients_with_equipment = cursor.fetchall()
    
    print(f"CLIENTES CON EQUIPOS: {len(clients_with_equipment)}\n")
    
    for client in clients_with_equipment:
        print(f"Cliente: {client['nombre']}")
        print(f"  ID: {client['id']}")
        print(f"  Equipos: {client['equipo_count']}")
        
        # Show first 3 equipment
        cursor.execute('''
            SELECT tipo_equipo, modelo, serie 
            FROM client_equipment 
            WHERE client_id = ? 
            LIMIT 3
        ''', (client['id'],))
        
        equipos = cursor.fetchall()
        for eq in equipos:
            print(f"    - {eq['tipo_equipo']} | {eq['modelo'] or 'N/A'} | {eq['serie'] or 'N/A'}")
        
        if client['equipo_count'] > 3:
            print(f"    ... y {client['equipo_count'] - 3} más")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_all_equipment()
