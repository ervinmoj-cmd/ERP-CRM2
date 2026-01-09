# Diagnose JavaScript syntax errors in admin_crm_view.html
import re

print("🔍 Analizando admin_crm_view.html...")

with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

print(f"   Total de líneas: {len(lines)}")

# Check for bad Unicode sequences that break JavaScript
issues = []

bad_patterns = [
    (r'\\u0026', 'Unicode escapado mal formado: \\u0026'),
    (r'\\u003c', 'Unicode escapado mal formado: \\u003c'),
    (r'\\u003e', 'Unicode escapado mal formado: \\u003e'),
    (r'\{\{ deal\.id \}\}[^\s;]', 'Falta ; después de {{ deal.id }}'),
    (r'\}\s*\}\s*const ', 'Posible cierre de función prematuro'),
]

for pattern, desc in bad_patterns:
    matches = list(re.finditer(pattern, content))
    if matches:
        for m in matches[:3]:  # Show first 3
            # Find line number
            line_start = content.rfind('\n', 0, m.start()) + 1
            line_num = content[:m.start()].count('\n') + 1
            issues.append(f"Línea {line_num}: {desc}")

# Find the loadEmails function and show its first 30 lines
loadEmails_match = re.search(r'function loadEmails\(\) \{', content)
if loadEmails_match:
    start = loadEmails_match.start()
    line_num = content[:start].count('\n') + 1
    print(f"\n📧 function loadEmails() encontrada en línea {line_num}")
    
    # Show first 20 lines of the function
    print("\nPrimeras 20 líneas de loadEmails():")
    start_line = line_num - 1
    for i in range(start_line, min(start_line + 20, len(lines))):
        print(f"{i+1}: {lines[i][:120]}")
else:
    print("❌ function loadEmails() NO encontrada!")

if issues:
    print(f"\n❌ PROBLEMAS ENCONTRADOS ({len(issues)}):")
    for issue in issues[:10]:
        print(f"   - {issue}")
else:
    print("\n✅ No se encontraron patrones problemáticos obvios")

# Check if there's a syntax error before loadEmails
# by looking for unbalanced braces before line 1367
print("\n🔍 Verificando balance de llaves antes de loadEmails...")
if loadEmails_match:
    code_before = content[:loadEmails_match.start()]
    open_braces = code_before.count('{')
    close_braces = code_before.count('}')
    diff = open_braces - close_braces
    print(f"   Llaves abiertas: {open_braces}")
    print(f"   Llaves cerradas: {close_braces}")
    print(f"   Diferencia: {diff} (debería ser pequeño, +10 a +30 es normal)")
    if diff > 50 or diff < 0:
        print("   ⚠️ POSIBLE DESBALANCE DE LLAVES")
