# Fix the last extra brace at line 1763
import re

print("🔧 Eliminando última llave extra (línea ~1763)...")

with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The pattern around lines 1758-1765:
# LINE 1758: }
# LINE 1759: (empty)
# LINE 1760: // PASO 9: Retornar texto plano...
# LINE 1761: // Esto permite que el CSS...
# LINE 1762: return textContent || body;
# LINE 1763: }  <-- EXTRA! Should not be here
# LINE 1764: (empty)
# LINE 1765: function renderThreadConversation(messages) {

# The issue: there's a stray } on line 1763 that shouldn't be there
# The return statement on 1762 is the last line of the function
# The } on 1758 closes something else (probably an if block)

# Fix: remove the } that appears after "return textContent || body;" and before "function renderThreadConversation"
pattern = r'(return textContent \|\| body;)\s*\n(\s*\})\s*\n\n(\s*function renderThreadConversation)'
replacement = r'\1\n\n\3'

match = re.search(pattern, content)
if match:
    print(f"   ✅ Encontrado patrón: return -> }} -> function")
    content = re.sub(pattern, replacement, content)
    print(f"   ✅ Eliminada llave extra")
else:
    print("   ⚠️ Patrón exacto no encontrado, buscando alternativa...")
    # Just find line with only } after return textContent
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'return textContent || body;' in line:
            # Check if line i+2 has only }
            if i+2 < len(lines) and lines[i+2].strip() == '}':
                print(f"   ✅ Encontrada llave extra en línea {i+3}")
                lines[i+2] = ''  # Remove the line
                content = '\n'.join(lines)
                break

with open('templates/admin_crm_view.html', 'w', encoding='utf-8') as f:
    f.write(content)

# Final verification
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
for script in scripts:
    opens = script.count('{')
    closes = script.count('}')
    balance = opens - closes
    print(f"\n📊 Balance final:")
    print(f"   {{ abiertas: {opens}")
    print(f"   }} cerradas: {closes}")
    print(f"   Balance: {balance}")
    if balance == 0:
        print("   🎉 ¡BALANCEADO CORRECTAMENTE!")
    else:
        print(f"   ⚠️ Aún hay desbalance de {balance}")
