import sqlite3

conn = sqlite3.connect('inair_reportes.db')
c = conn.cursor()

# Add column for cycle reset configuration
try:
    c.execute("ALTER TABLE equipos_calendario ADD COLUMN reiniciar_en_horas INTEGER DEFAULT NULL")
    print("Columna 'reiniciar_en_horas' agregada")
    print("NULL = continúa aumentando")
    print("Valor (ej: 8000) = reinicia después de ese valor")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("Columna ya existe")
    else:
        print(f"Error: {e}")

conn.commit()
conn.close()
print("Migración completada")
