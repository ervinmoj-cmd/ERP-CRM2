
import sqlite3
from database import get_db, create_refaccion, create_reserva, get_reservas_by_refaccion, fulfill_reserva, delete_refaccion, delete_reserva, get_refaccion_by_id, search_refacciones

def test_warehouse_flow():
    print("🚀 Starting Warehouse Verification...")
    
    # 1. Create a dummy refaccion
    ref_data = {
        'numero_parte': 'TEST-PART-001',
        'descripcion': 'Test Part for Verification',
        'unidad': 'PZA',
        'cantidad': 100,
        'ubicacion': 'Mexicali',
        'ubicacion_especifica': 'A-1',
        'detalles_importacion': 'Test import'
    }
    
    try:
        # Clean up if exists
        search = search_refacciones('TEST-PART-001')
        for s in search:
            if s['numero_parte'] == 'TEST-PART-001':
                delete_refaccion(s['id'])
                print("   Deleted existing test part.")

        ref_id = create_refaccion(ref_data)
        print(f"✅ Created Refaccion ID: {ref_id}")
        
        # 2. Check initial state
        ref = get_refaccion_by_id(ref_id)
        print(f"   Initial Stock: {ref['cantidad']}")
        assert ref['cantidad'] == 100
        
        # 3. Create Reservation
        res_id = create_reserva(ref_id, cliente_id=1, cantidad=20, orden_compra='OC-TEST', cliente_nombre='Test Client')
        print(f"✅ Created Reservation ID: {res_id} for 20 units")
        
        # 4. Check Reservations & Availability via search (updated query)
        reservas = get_reservas_by_refaccion(ref_id)
        assert len(reservas) == 1
        assert reservas[0]['cantidad'] == 20
        print("✅ Reservation found in DB")
        
        search_res = search_refacciones('TEST-PART-001')
        part_in_search = next(p for p in search_res if p['id'] == ref_id)
        print(f"   Search Result - Stock: {part_in_search['cantidad']}, Apartados: {part_in_search['apartados']}")
        assert part_in_search['apartados'] == 20
        
        # 5. Fulfill Reservation (Simulate Invoice)
        print("🔄 Simulating Invoice (Fulfilling 15 units)...")
        fulfill_reserva(ref_id, cliente_id=1, cantidad_usada=15)
        
        # 6. Check Post-Fulfillment State
        ref_after = get_refaccion_by_id(ref_id)
        reservas_after = get_reservas_by_refaccion(ref_id)
        
        print(f"   Post-Invoice Stock: {ref_after['cantidad']} (Expected 85)")
        assert ref_after['cantidad'] == 85
        
        print(f"   Post-Invoice Reservation Qty: {reservas_after[0]['cantidad']} (Expected 5)")
        assert reservas_after[0]['cantidad'] == 5
        print("✅ Stock deduction logic verified")
        
        # 7. Cleanup
        delete_refaccion(ref_id)
        print("✅ Verification Complete & Cleanup Done!")
        
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_warehouse_flow()
