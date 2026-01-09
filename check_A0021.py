import sqlite3
import json

conn = sqlite3.connect("inair_reportes.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Get the A-0021 draft specifically
c.execute("SELECT * FROM draft_reports WHERE folio = ?", ("A-0021",))
draft = c.fetchone()

if draft:
    print(f"✓ Found draft for A-0021")
    print(f"✓ Created: {draft['created_at']}")
    
    # Parse form_data
    try:
        form_data = json.loads(draft['form_data']) if isinstance(draft['form_data'], str) else draft['form_data']
        
        print(f"\n✓ Form data has {len(form_data)} fields")
        
        # Show ALL fields with values
        print("\nALL fields in form_data:")
        for key, value in sorted(form_data.items()):
            if value and value != '':
                print(f"  ✓ {key}: {value[:100]}")
                
        # Check critical fields specifically
        print("\n\nCRITICAL fields:")
        critical = ['cliente', 'tipo_equipo', 'modelo', 'serie', 'contacto', 'telefono', 'email', 'direccion']
        for field in critical:
            value = form_data.get(field, '')
            if value:
                print(f"  ✓ {field}: {value}")
            else:
                print(f"  ✗ {field}: EMPTY")
                
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("✗ No draft found for A-0021")

conn.close()
