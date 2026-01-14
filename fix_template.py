import re

# Read the file
with open(r'c:\ERP-CRM\templates\admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix line 2035-2036: Add missing closing brace
# Pattern: {{ linked_cotizaciones[0].id } followed by newline and };
pattern1 = r'const cotizacionId = \{\{ linked_cotizaciones\[0\]\.id \}\r?\n\s*\};'
replacement1 = 'const cotizacionId = {{ linked_cotizaciones[0].id }};'

content = re.sub(pattern1, replacement1, content)

# Fix line 2138-2139: Add missing closing brace  
pattern2 = r'const dealId = \{\{ deal\.id \}\r?\n\s*\};'
replacement2 = 'const dealId = {{ deal.id }};'

content = re.sub(pattern2, replacement2, content)

# Write back
with open(r'c:\ERP-CRM\templates\admin_crm_view.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed template syntax errors")
