
with open('app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'ocu' in line.lower():
            print(f"FOUND at {i+1}: {line.strip()}")
