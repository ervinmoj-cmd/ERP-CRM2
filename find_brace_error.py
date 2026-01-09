# Find the exact location of the brace imbalance
import re

with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Track brace balance line by line
print("🔍 Buscando desbalance de llaves...")
balance = 0
in_script = False
script_start = 0

for i, line in enumerate(lines):
    line_num = i + 1
    
    # Track script blocks
    if '<script' in line.lower():
        in_script = True
        script_start = line_num
        balance = 0
    
    if in_script:
        opens = line.count('{')
        closes = line.count('}')
        prev_balance = balance
        balance += opens - closes
        
        # Report significant changes
        if opens > 0 or closes > 0:
            if prev_balance > 0 and balance <= 0 and 'function' not in line.lower():
                pass  # Normal function close
            elif balance < 0:
                print(f"❌ Línea {line_num}: Balance negativo ({balance})")
                print(f"   Contenido: {line[:100]}")
    
    if '</script' in line.lower():
        if balance != 0:
            print(f"⚠️ Script terminó con balance {balance} (línea {script_start}-{line_num})")
        in_script = False

# Now check specifically around line 1029-1031 where we know there's an issue
print("\n📌 Revisando líneas 1025-1035 (zona problemática):")
for i in range(1024, 1036):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}")

# Check balance at key points
print("\n📊 Balance de llaves en puntos clave:")
for checkpoint in [1000, 1028, 1032, 1100, 1367]:
    code_slice = '\n'.join(lines[:checkpoint])
    op = code_slice.count('{')
    cl = code_slice.count('}')
    print(f"   Línea {checkpoint}: {{{op}}} abiertas, {{{cl}}} cerradas, balance = {op-cl}")
