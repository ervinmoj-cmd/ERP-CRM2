
import os

target = "purchase_requisitions"
print(f"Searching for '{target}'...")
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if target in line:
                            print(f"{path}:{i+1}: {line.strip()}")
            except:
                pass
