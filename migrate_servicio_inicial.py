import sqlite3

conn = sqlite3.connect('inair_reportes.db')
c = conn.cursor()

# Add new column for initial service type
try:
    c.execute("ALTER TABLE equipos_calendario ADD COLUMN tipo_servicio_inicial TEXT DEFAULT '2000 Horas'")
    print("Columna 'tipo_servicio_inicial' agregada")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("Columna ya existe")
    else:
        print(f"Error: {e}")

# Remove old column (SQLite doesn't support DROP COLUMN easily, so we'll just stop using it)
print("Campo 'tipo_servicio_defecto' se dejará de usar en el frontend")

conn.commit()
conn.close()
print("Migración completada")
