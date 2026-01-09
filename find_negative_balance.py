# Find exactly where the brace imbalance occurs
import re

with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Track balance line by line in the main script
balance = 0
in_script = False
problem_lines = []

for i, line in enumerate(lines):
    line_num = i + 1
    
    if '<script>' in line.lower() or '<script ' in line.lower():
        in_script = True
        balance = 0
        continue
    
    if '</script>' in line.lower():
        in_script = False
        continue
    
    if in_script:
        opens = line.count('{')
        closes = line.count('}')
        old_balance = balance
        balance += opens - closes
        
        # Record when balance goes negative
        if balance < 0 and old_balance >= 0:
            problem_lines.append((line_num, f"Balance became negative here: {balance}"))
            print(f"⚠️ Línea {line_num}: Balance se vuelve negativo ({balance})")
            print(f"   Contenido: {line.strip()[:80]}")
            print()

print(f"\nTotal líneas problemáticas: {len(problem_lines)}")

if problem_lines:
    first_problem = problem_lines[0][0]
    print(f"\n📌 Contexto alrededor de línea {first_problem}:")
    for i in range(first_problem - 5, first_problem + 5):
        if 0 <= i < len(lines):
            marker = ">>>" if i+1 == first_problem else "   "
            print(f"{marker} {i+1}: {lines[i][:100]}")
