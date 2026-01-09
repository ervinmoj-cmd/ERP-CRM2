# Fix ALL instances of the bad pattern: 
# const dealId = {{ deal.id }};
#           };  <-- EXTRA, must be removed

import re

print("🔧 Corrigiendo TODAS las llaves extra después de {{ deal.id }};...")

with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)

# The pattern is: {{ deal.id }};\n            };\n        const
# Should be: {{ deal.id }};\n            const

# Fix pattern: {{ deal.id }}; followed by a line with just }; then code
pattern = r'(\{\{ deal\.id \}\};)\s*\n\s*\};\s*\n(\s*const )'
replacement = r'\1\n\2'

count = len(re.findall(pattern, content))
print(f"   Encontradas {count} ocurrencias del patrón problemático")

content = re.sub(pattern, replacement, content)

# Also check for standalone } lines that shouldn't be there after deal.id
pattern2 = r'(\{\{ deal\.id \}\};)\s*\n\s*\}\s*\n(\s*const )'
count2 = len(re.findall(pattern2, content))
if count2:
    print(f"   Encontradas {count2} ocurrencias adicionales (con solo }})")
    content = re.sub(pattern2, replacement, content)

with open('templates/admin_crm_view.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Archivo corregido: {original_len} → {len(content)} bytes")

# Verify balance
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
for script in scripts:
    opens = script.count('{')
    closes = script.count('}')
    balance = opens - closes
    print(f"\n📊 Balance de llaves en script:")
    print(f"   {{ abiertas: {opens}")
    print(f"   }} cerradas: {closes}")
    print(f"   Balance: {balance}")
    if balance == 0:
        print("   ✅ BALANCEADO CORRECTAMENTE")
    else:
        print(f"   ⚠️ Aún hay desbalance de {balance}")
