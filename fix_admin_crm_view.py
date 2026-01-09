# Fix admin_crm_view.html line 1029
import re

# Read file
with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix line 1029: add ; after {{ deal.id }}
content = re.sub(
    r'const dealId = \{\{ deal\.id \}\}\n',
    'const dealId = {{ deal.id }};\n            ',
    content
)

# Write back
with open('templates/admin_crm_view.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed line 1029 - added semicolon")
