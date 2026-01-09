"""
Direct test of equipment function
"""
import sys
sys.path.insert(0, 'c:\\Users\\INAIR 005\\OneDrive\\Escritorio\\PYTHON\\p9\\p6\\inair_reportes')

from database import get_client_equipment

# Test with client ID 12 (MECALUX from the image)
print("Testing get_client_equipment(12)...")
result = get_client_equipment(12)
print(f"\nResults: {len(result)} equipos")
for eq in result:
    print(f"  - {eq.get('tipo_equipo')} | {eq.get('modelo')} | {eq.get('serie')}")
