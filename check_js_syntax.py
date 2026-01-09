import re

file_path = 'templates/admin_crm_view.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the script block
script_start = content.find('<script>')
script_end = content.find('</script>', script_start)

if script_start == -1 or script_end == -1:
    print("No se encontró el bloque <script>")
    exit(1)

script_content = content[script_start:script_end + len('</script>')]

# Count braces
open_braces = script_content.count('{')
close_braces = script_content.count('}')
open_parens = script_content.count('(')
close_parens = script_content.count(')')
open_brackets = script_content.count('[')
close_brackets = script_content.count(']')

print(f"Llaves {{}}: {open_braces} abiertas, {close_braces} cerradas (diferencia: {open_braces - close_braces})")
print(f"Paréntesis (): {open_parens} abiertos, {close_parens} cerrados (diferencia: {open_parens - close_parens})")
print(f"Corchetes []: {open_brackets} abiertos, {close_brackets} cerrados (diferencia: {open_brackets - close_brackets})")

# Check for common syntax errors
lines = script_content.split('\n')
for i, line in enumerate(lines, 1):
    # Check for unclosed strings
    if line.count("'") % 2 != 0 and "'" in line:
        print(f"Línea {i}: Posible comilla simple sin cerrar: {line[:80]}")
    if line.count('"') % 2 != 0 and '"' in line:
        print(f"Línea {i}: Posible comilla doble sin cerrar: {line[:80]}")

