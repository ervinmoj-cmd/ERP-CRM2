"""
Script de prueba para validar la vinculación de PIs a CRM Deals
"""
import sqlite3

DATABASE = 'inair_reportes.db'

def test_pi_linking():
    """Prueba la vinculación de PIs a deals"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 60)
    print("PRUEBA DE VINCULACIÓN DE PIs A CRM DEALS")
    print("=" * 60)
    
    # 1. Verificar que la tabla crm_deal_pis existe
    print("\n1. Verificando tabla crm_deal_pis...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='crm_deal_pis'
    """)
    result = cursor.fetchone()
    if result:
        print("   ✓ Tabla crm_deal_pis existe")
    else:
        print("   ✗ ERROR: Tabla crm_deal_pis NO existe")
        return
    
    # 2. Verificar estructura de la tabla
    print("\n2. Estructura de la tabla crm_deal_pis:")
    cursor.execute("PRAGMA table_info(crm_deal_pis)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col['name']}: {col['type']}")
    
    # 3. Contar deals existentes
    print("\n3. Verificando datos existentes:")
    cursor.execute("SELECT COUNT(*) as count FROM crm_deals")
    deal_count = cursor.fetchone()['count']
    print(f"   - Total de deals: {deal_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM pis")
    pi_count = cursor.fetchone()['count']
    print(f"   - Total de PIs: {pi_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM crm_deal_pis")
    link_count = cursor.fetchone()['count']
    print(f"   - Total de vinculaciones: {link_count}")
    
    # 4. Mostrar algunos deals
    print("\n4. Primeros 3 deals:")
    cursor.execute("SELECT id, titulo, valor_estimado FROM crm_deals LIMIT 3")
    deals = cursor.fetchall()
    for deal in deals:
        print(f"   - ID: {deal['id']}, Título: {deal['titulo']}, Valor: ${deal['valor_estimado'] or 0:,.2f}")
    
    # 5. Mostrar algunas PIs
    print("\n5. Primeras 3 PIs:")
    cursor.execute("SELECT id, folio, total, moneda FROM pis LIMIT 3")
    pis = cursor.fetchall()
    for pi in pis:
        print(f"   - ID: {pi['id']}, Folio: {pi['folio']}, Total: ${pi['total'] or 0:,.2f} {pi['moneda']}")
    
    # 6. Si hay vinculaciones, mostrarlas
    if link_count > 0:
        print("\n6. Vinculaciones existentes:")
        cursor.execute("""
            SELECT 
                cdp.id,
                cdp.deal_id,
                cd.titulo as deal_titulo,
                cdp.pi_id,
                p.folio as pi_folio,
                p.total as pi_total
            FROM crm_deal_pis cdp
            JOIN crm_deals cd ON cdp.deal_id = cd.id
            JOIN pis p ON cdp.pi_id = p.id
            LIMIT 5
        """)
        links = cursor.fetchall()
        for link in links:
            print(f"   - Deal '{link['deal_titulo']}' → PI {link['pi_folio']} (${link['pi_total'] or 0:,.2f})")
    
    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    test_pi_linking()
