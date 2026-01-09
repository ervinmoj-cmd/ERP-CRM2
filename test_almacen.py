from database import (
    init_db, create_refaccion, get_all_refacciones, 
    get_refaccion_by_id, update_refaccion, delete_refaccion, 
    search_refacciones, get_dashboard_stats
)
import sqlite3

def test_almacen():
    print("Initializing DB...")
    init_db()
    
    # 1. Create
    print("\n1. Testing Create...")
    ref_id = create_refaccion(
        numero_parte="TEST-001",
        descripcion="Filtro de Prueba",
        unidad="pza",
        cantidad=10,
        ubicacion="Mexicali",
        detalles_importacion="Importado de USA"
    )
    
    if ref_id:
        print(f"✅ Created refaccion with ID: {ref_id}")
    else:
        print("❌ Failed to create refaccion (might already exist)")
        # Try to get it if it exists
        refs = search_refacciones("TEST-001")
        if refs:
            ref_id = refs[0]['id']
            print(f"Found existing ID: {ref_id}")

    # 2. Read
    print("\n2. Testing Read...")
    ref = get_refaccion_by_id(ref_id)
    if ref and ref['numero_parte'] == "TEST-001":
        print(f"✅ Read success: {ref['descripcion']}")
    else:
        print("❌ Read failed")

    # 3. Update
    print("\n3. Testing Update...")
    success = update_refaccion(
        ref_id,
        numero_parte="TEST-001",
        descripcion="Filtro de Prueba UPDATED",
        unidad="pza",
        cantidad=5,
        ubicacion="Tijuana",
        detalles_importacion="Actualizado"
    )
    
    ref_updated = get_refaccion_by_id(ref_id)
    if success and ref_updated['descripcion'] == "Filtro de Prueba UPDATED" and ref_updated['ubicacion'] == "Tijuana":
        print("✅ Update success")
    else:
        print("❌ Update failed")

    # 4. Search
    print("\n4. Testing Search...")
    results = search_refacciones("UPDATED")
    if len(results) > 0:
        print(f"✅ Search success: Found {len(results)} items")
    else:
        print("❌ Search failed")
        
    # 5. Dashboard Stats
    print("\n5. Testing Stats...")
    stats = get_dashboard_stats()
    print(f"Total Refacciones: {stats['total_refacciones']}")
    if 'total_refacciones' in stats:
        print("✅ Stats success")
    else:
        print("❌ Stats failed")

    # 6. Delete
    print("\n6. Testing Delete...")
    success = delete_refaccion(ref_id)
    ref_deleted = get_refaccion_by_id(ref_id)
    if success and not ref_deleted:
        print("✅ Delete success")
    else:
        print("❌ Delete failed")

if __name__ == "__main__":
    try:
        test_almacen()
        print("\n✨ All tests completed!")
    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
