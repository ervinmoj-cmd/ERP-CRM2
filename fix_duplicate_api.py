# Fix duplicate api_load_draft route
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 1134-1165 (0-indexed: 1133-1164)
# These are the first duplicate api_load_draft function
new_lines = lines[:1133] + lines[1165:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Removed duplicate api_load_draft function (lines 1134-1165)")
print("The existing api_load_draft at line ~1227 will be used instead")
