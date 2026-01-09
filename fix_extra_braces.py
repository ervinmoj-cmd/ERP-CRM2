# Fix the extra braces in admin_crm_view.html
import re

print("🔧 Corrigiendo llaves extra en admin_crm_view.html...")

with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The problem: after my edit, lines 1029-1031 look like:
#   function loadModuleContent() {
#       const dealId = {{ deal.id }};
#   };  <-- EXTRA (should not be here)
#   }   <-- EXTRA (should not be here)
#   const module = document.getElementById('msgModule').value;

# Fix: remove the extra }; and } lines, keep the code inside the function
old_pattern = r'(const dealId = \{\{ deal\.id \}\};)\s*\n\s*\};\s*\n\s*\}\s*\n(\s*const module)'
new_replacement = r'\1\n\2'

match = re.search(old_pattern, content)
if match:
    print(f"   ✅ Encontrado patrón problemático")
    print(f"   Antes: {repr(match.group(0)[:100])}")
    content = re.sub(old_pattern, new_replacement, content)
    print(f"   ✅ Removidas las 2 llaves extra")
else:
    print("   ⚠️ Patrón no encontrado, intentando alternativa...")
    # Try alternative pattern
    alt_pattern = r'const dealId = \{\{ deal\.id \}\};\s*\n\s{8}\};\n\s{8}\}'
    alt_match = re.search(alt_pattern, content)
    if alt_match:
        print(f"   ✅ Encontrado patrón alternativo")
        content = content.replace(alt_match.group(0), 'const dealId = {{ deal.id }};')
        print(f"   ✅ Corregido")
    else:
        # Just show lines 1028-1035 for manual review
        lines = content.split('\n')
        print("\n   📌 Líneas 1028-1035:")
        for i in range(1027, 1036):
            print(f"   {i+1}: {lines[i]}")

# Write back
with open('templates/admin_crm_view.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Archivo guardado")

# Verify the fix
with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    new_content = f.read()

# Check balance again
loadmod = re.search(r'function loadModuleContent\(\)', new_content)
if loadmod:
    lines = new_content.split('\n')
    for i, line in enumerate(lines):
        if 'function loadModuleContent()' in line:
            func_content = '\n'.join(lines[i:i+80])
            opens = func_content.count('{')
            closes = func_content.count('}')
            print(f"\n📊 Verificación: llaves en loadModuleContent()")
            print(f"   {{ abiertas: {opens}")
            print(f"   }} cerradas: {closes}")
            print(f"   Balance: {opens - closes}")
            if opens == closes:
                print("   ✅ FUNCIÓN BALANCEADA CORRECTAMENTE")
            else:
                print("   ⚠️ Aún hay desbalance (revisar manualmente)")
            break
