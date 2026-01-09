# Final fix: check and fix indentation in loadModuleContent
import re

print("🔧 Verificando y corrigiendo función loadModuleContent...")

with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if lines after 'const dealId' have correct indentation
# They should be indented with 12 spaces (inside the function)

# Find the function and fix indentation if needed
pattern = r'(function loadModuleContent\(\) \{\s*\n\s*const dealId = \{\{ deal\.id \}\};)\n(        const module)'
match = re.search(pattern, content)

if match:
    print("   ⚠️ Detectada indentación incorrecta (8 espacios)")
    # Fix indentation - add 4 more spaces
    content = re.sub(pattern, r'\1\n            const module', content)
    print("   ✅ Corregida indentación (12 espacios)")
else:
    print("   Patrón no encontrado, verificando indentación actual...")
    # Check current state
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'function loadModuleContent()' in line:
            print(f"\n   Líneas de la función (empezando en {i+1}):")
            for j in range(i, min(i+10, len(lines))):
                spaces = len(lines[j]) - len(lines[j].lstrip())
                print(f"   {j+1}: [{spaces} espacios] {lines[j][:80]}")
            break

# Verify there's no syntax error
# Look for common issues
issues = []

# Check for mismatched braces in loadModuleContent
func_match = re.search(r'function loadModuleContent\(\)\s*\{', content)
if func_match:
    # Find end of function (next function or script end)
    start = func_match.start()
    # Get approximate 100 lines
    func_end = content.find('function ', start + 100)
    if func_end == -1:
        func_end = start + 5000
    
    func_content = content[start:func_end]
    opens = func_content.count('{')
    closes = func_content.count('}')
    print(f"\n   Verificación de llaves en loadModuleContent():")
    print(f"   {{ abiertas: {opens}, }} cerradas: {closes}")
    if opens != closes:
        print(f"   ⚠️ DESBALANCE: diferencia de {abs(opens-closes)}")
        issues.append(f"Desbalance de llaves: {opens} {{ vs {closes} }}")
    else:
        print(f"   ✅ Balanceado correctamente")

with open('templates/admin_crm_view.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Archivo guardado")

# Final verification - show lines 1028-1040
print("\n📌 Estado final de líneas 1028-1040:")
lines = content.split('\n')
for i in range(1027, 1040):
    if i < len(lines):
        print(f"{i+1}: {lines[i][:100]}")
