# config.py - Configuración de rutas para desarrollo local y Railway
import os

# Detectar si estamos en Railway (o cualquier ambiente con RAILWAY_ENVIRONMENT)
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

# Directorio raíz del proyecto
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

if IS_RAILWAY:
    # En Railway: usar volumen persistente montado en /app/persistent_data
    PERSISTENT_DIR = "/app/persistent_data"
    DATA_DIR = os.path.join(PERSISTENT_DIR, "data")
    DATABASE_DIR = PERSISTENT_DIR
    UPLOAD_DIR = os.path.join(PERSISTENT_DIR, "uploads")
    FIRMAS_DIR = os.path.join(PERSISTENT_DIR, "firmas")
    GENERADOS_DIR = os.path.join(PERSISTENT_DIR, "generados")
else:
    # Desarrollo local: usar rutas actuales (NO AFECTA TU SETUP ACTUAL)
    PERSISTENT_DIR = APP_ROOT
    DATA_DIR = os.path.join(APP_ROOT, "data")
    DATABASE_DIR = APP_ROOT
    UPLOAD_DIR = os.path.join(APP_ROOT, "static", "uploads")
    FIRMAS_DIR = os.path.join(APP_ROOT, "static", "firmas")
    GENERADOS_DIR = os.path.join(APP_ROOT, "static")

# Crear directorios si no existen (solo en Railway, localmente ya existen)
if IS_RAILWAY:
    for directory in [DATA_DIR, UPLOAD_DIR, FIRMAS_DIR, GENERADOS_DIR]:
        os.makedirs(directory, exist_ok=True)

# Rutas de bases de datos
DATABASE_MAIN = os.path.join(DATABASE_DIR, "inair_reportes.db")
DATABASE_AUX = os.path.join(DATABASE_DIR, "inair.db")
