import sqlite3
import json

# Test the complete load flow
conn = sqlite3.connect("inair_reportes.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Get the most recent draft
c.execute("SELECT * FROM draft_reports ORDER BY created_at DESC LIMIT 1")
draft = c.fetchone()

if draft:
    folio = draft['folio']
    print(f"✓ Most recent draft: {folio}")
    print(f"✓ Created: {draft['created_at']}")
    
    # Parse form_data
    try:
        form_data = json.loads(draft['form_data']) if isinstance(draft['form_data'], str) else draft['form_data']
        
        # Check critical fields
        critical_fields = ['cliente', 'tipo_equipo', 'modelo', 'serie', 'contacto', 'telefono', 'email', 'direccion']
        print(f"\n✓ Form data contains {len(form_data)} fields")
        print("\nCritical fields:")
        for field in critical_fields:
            value = form_data.get(field, 'NOT FOUND')
            status = "✓" if value and value != 'NOT FOUND' else "✗"
            print(f"  {status} {field}: {value[:50] if value else 'EMPTY'}")
        
        # Check if photos exist
        print("\nPhotos:")
        for i in range(1, 5):
            foto = draft[f'foto{i}_data']
            if foto:
                print(f"  ✓ foto{i}: {len(foto)} bytes")
            else:
                print(f"  ✗ foto{i}: EMPTY")
        
        # Check signatures
        print("\nSignatures:")
        if draft['firma_tecnico_data']:
            print(f"  ✓ firma_tecnico: {len(draft['firma_tecnico_data'])} bytes")
        else:
            print(f"  ✗ firma_tecnico: EMPTY")
            
        if draft['firma_cliente_data']:
            print(f"  ✓ firma_cliente: {len(draft['firma_cliente_data'])} bytes")
        else:
            print(f"  ✗ firma_cliente: EMPTY")
            
    except Exception as e:
        print(f"✗ Error parsing form_data: {e}")
else:
    print("✗ No drafts found")

conn.close()
