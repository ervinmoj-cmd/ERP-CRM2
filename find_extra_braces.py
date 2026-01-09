# Find and fix the extra closing braces
import re

with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("🔍 Buscando llaves extra entre línea 1028 y 1100...")

# Show the problematic area
for i in range(1027, 1105):
    line = lines[i].rstrip()
    line_num = i + 1
    
    # Highlight lines with only closing braces
    has_open = '{' in line
    has_close = '}' in line
    only_close = has_close and not has_open and line.strip() in ['}', '};', '        }', '        };']
    
    if only_close or 'function' in line.lower() or 'const dealId' in line:
        marker = '⚠️' if only_close else '📌'
        print(f"{marker} {line_num}: {line[:100]}")
    
print("\n🔧 Analizando la función loadModuleContent()...")

# Find loadModuleContent and count its braces
loadmod_match = re.search(r'function loadModuleContent\(\)', '\n'.join([l for l in lines]))
if loadmod_match:
    # Find the line number
    content_up_to = ''.join(lines[:1100])
    for i, line in enumerate(lines):
        if 'function loadModuleContent()' in line:
            print(f"   Empieza en línea {i+1}")
            
            # Count braces within the function (approximate to line 1100)
            func_content = ''.join(lines[i:1100])
            opens = func_content.count('{')
            closes = func_content.count('}')
            print(f"   Llaves {{ en función: {opens}")
            print(f"   Llaves }} en función: {closes}")
            print(f"   Diferencia: {opens - closes}")
            break
