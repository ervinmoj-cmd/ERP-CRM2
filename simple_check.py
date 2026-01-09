import sqlite3
import json

try:
    conn = sqlite3.connect("inair_reportes.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM draft_reports WHERE folio = ?", ("A-0021",))
    draft = c.fetchone()

    if draft:
        form_data = json.loads(draft['form_data']) if isinstance(draft['form_data'], str) else draft['form_data']
        
        print("CRITICAL FIELDS:")
        print(f"cliente: '{form_data.get('cliente', 'EMPTY')}'")
        print(f"tipo_equipo: '{form_data.get('tipo_equipo', 'EMPTY')}'")
        print(f"modelo: '{form_data.get('modelo', 'EMPTY')}'")
        print(f"serie: '{form_data.get('serie', 'EMPTY')}'")
        print(f"contacto: '{form_data.get('contacto', 'EMPTY')}'")
        print(f"telefono: '{form_data.get('telefono', 'EMPTY')}'")
        print(f"email: '{form_data.get('email', 'EMPTY')}'")
        print(f"direccion: '{form_data.get('direccion', 'EMPTY')}'")
    else:
        print("Draft A-0021 not found")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
