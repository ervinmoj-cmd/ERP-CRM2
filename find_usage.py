
with open('database.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'create_purchase_requisition' in line:
            print(f"FOUND at {i+1}: {line.strip()}")
