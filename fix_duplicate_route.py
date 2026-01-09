# Fix duplicate editar_reporte route
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 1166-1181 (0-indexed: 1165-1180)
# These are the duplicate editar_reporte function
new_lines = lines[:1165] + lines[1181:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Removed duplicate editar_reporte function (lines 1166-1181)")
print("The existing editar_reporte at line ~1222 will be used instead")
