from database import create_compra, get_db
import sqlite3

def debug_insert():
    print("Attempting debug insert...")
    
    # 1. Get a provider and user
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM proveedores LIMIT 1")
        prov = cursor.fetchone()
        if not prov:
            print("ERROR: No providers found. Cannot test insert.")
            # Create dummy provider
            cursor.execute("INSERT INTO proveedores (nombre_empresa) VALUES ('Test Provider')")
            prov_id = cursor.lastrowid
            print(f"Created dummy provider with ID: {prov_id}")
        else:
            prov_id = prov['id']
            print(f"Using provider ID: {prov_id}")
            
        cursor.execute("SELECT id FROM users LIMIT 1")
        user = cursor.fetchone()
        if not user:
            print("ERROR: No users found. Cannot test insert.")
            user_id = 1 # Fallback
        else:
            user_id = user['id']
            print(f"Using user ID: {user_id}")

    # 2. Prepare data
    data = {
        'folio': 'OC-DEBUG-001',
        'proveedor_id': prov_id,
        'fecha_emision': '2023-10-27',
        'fecha_entrega_estimada': '2023-11-01',
        'estado': 'Borrador',
        'moneda': 'MXN',
        'subtotal': 100.0,
        'iva': 16.0,
        'total': 116.0,
        'notas': 'Debug note'
    }
    
    items = [
        {
            'linea': 1,
            'numero_parte': 'PART-001',
            'descripcion': 'Test Item',
            'cantidad': 10,
            'unidad': 'PZA',
            'precio_unitario': 10.0,
            'importe': 100.0
        }
    ]
    
    # 3. Call actual function
    print("Calling create_compra...")
    try:
        result = create_compra(data, items, user_id)
        print(f"Result: {result}")
        if result:
            print("SUCCESS: Purchase order created.")
        else:
            print("FAILURE: create_compra returned False/None indicating failure.")
            
    except Exception as e:
        print(f"EXCEPTION caught during call: {e}")

if __name__ == "__main__":
    debug_insert()
