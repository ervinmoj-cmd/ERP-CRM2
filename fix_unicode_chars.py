# Fix Unicode characters in admin_crm_view.html
import re

print("🔧 Limpiando caracteres mal codificados en admin_crm_view.html...")

# Read file
with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()

original_length = len(content)

# Fix bad Unicode escapes that break JavaScript
replacements = {
    r'\\u0026\\u0026': '&&',  # Fix &&
    r'\\u003c': '<',           # Fix <
    r'\\u003e': '>',           # Fix >
}

changes = 0
for pattern, replacement in replacements.items():
    matches = len(re.findall(pattern, content))
    if matches > 0:
        content = re.sub(pattern, replacement, content)
        changes += matches
        print(f"  ✅ Reemplazadas {matches} ocurrencias de {pattern}")

# Write back
with open('templates/admin_crm_view.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Archivo limpiado: {changes} cambios realizados")
print(f"   Tamaño: {original_length} → {len(content)} bytes")
