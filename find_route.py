
with open('app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if '/api/crm/equipo' in line and 'POST' in line:
            print(f"Found at line {i}: {line.strip()}")
