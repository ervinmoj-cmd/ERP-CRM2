from database import (
    create_refaccion, get_refaccion_by_id, update_refaccion, 
    delete_refaccion, search_refacciones
)
import sqlite3

def test_bulk_features():
    print("Testing Bulk Upload & Specific Location Features...")
    
    # 1. Test Specific Location in Create
    print("\n1. Testing Specific Location (Create)...")
    ref_id = create_refaccion(
        numero_parte="BULK-TEST-001",
        descripcion="Bulk Test Item",
        unidad="pza",
        cantidad=10,
        ubicacion="Mexicali",
        detalles_importacion="Test",
        ubicacion_especifica="A-1-1"
    )
    
    if ref_id:
        ref = get_refaccion_by_id(ref_id)
        if ref and ref.get('ubicacion_especifica') == "A-1-1":
            print(f"✅ Specific Location saved correctly: {ref['ubicacion_especifica']}")
        else:
            print(f"❌ Specific Location failed. Got: {ref.get('ubicacion_especifica')}")
    else:
        print("❌ Failed to create item")
        # Cleanup if exists
        refs = search_refacciones("BULK-TEST-001")
        if refs:
            ref_id = refs[0]['id']
            delete_refaccion(ref_id)
            # Retry
            ref_id = create_refaccion(
                numero_parte="BULK-TEST-001",
                descripcion="Bulk Test Item",
                unidad="pza",
                cantidad=10,
                ubicacion="Mexicali",
                detalles_importacion="Test",
                ubicacion_especifica="A-1-1"
            )

    # 2. Test Specific Location in Update
    print("\n2. Testing Specific Location (Update)...")
    success = update_refaccion(
        ref_id,
        numero_parte="BULK-TEST-001",
        descripcion="Bulk Test Item Updated",
        unidad="pza",
        cantidad=10,
        ubicacion="Mexicali",
        detalles_importacion="Test",
        ubicacion_especifica="B-2-2"
    )
    
    ref = get_refaccion_by_id(ref_id)
    if success and ref['ubicacion_especifica'] == "B-2-2":
        print(f"✅ Specific Location updated correctly: {ref['ubicacion_especifica']}")
    else:
        print("❌ Specific Location update failed")

    # 3. Simulate Bulk Upload (JSON Logic)
    print("\n3. Simulating Bulk Upload Logic...")
    bulk_data = [
        ["BULK-002", "Bulk Item 2", "5", "pza", "Tijuana", "C-3-3"],
        ["BULK-003", "Bulk Item 3", "8", "lt", "Mexicali", "D-4-4"]
    ]
    
    count = 0
    created_ids = []
    for item in bulk_data:
        try:
            rid = create_refaccion(
                numero_parte=item[0],
                descripcion=item[1],
                cantidad=int(item[2]),
                unidad=item[3],
                ubicacion=item[4],
                ubicacion_especifica=item[5]
            )
            if rid:
                count += 1
                created_ids.append(rid)
                print(f"   Created {item[0]} at {item[5]}")
        except Exception as e:
            print(f"   Error creating {item[0]}: {e}")
            
    if count == 2:
        print(f"✅ Bulk simulation successful: {count} items created")
    else:
        print(f"❌ Bulk simulation failed: {count}/2 items created")

    # Cleanup
    print("\nCleaning up...")
    delete_refaccion(ref_id)
    for rid in created_ids:
        delete_refaccion(rid)
    print("Cleanup done.")

if __name__ == "__main__":
    try:
        test_bulk_features()
        print("\n✨ All tests completed!")
    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
