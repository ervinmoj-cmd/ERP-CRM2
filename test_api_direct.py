"""
Test API endpoint directly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Simulate Flask app context
from app import app
from database import get_client_equipment

print("\n🧪 TESTING get_client_equipment():")
print("="*60)

# Test with varios cliente_id
test_ids = [1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14]

for cid in test_ids:
    results = get_client_equipment(cid)
    if results:
        print(f"\n✅ cliente_id {cid}: {len(results)} equipos")
        for eq in results[:2]:  # Show first 2
            print(f"   - {eq.get('tipo_equipo')} | {eq.get('modelo')}")
    else:
        print(f"❌ cliente_id {cid}: 0 equipos")
