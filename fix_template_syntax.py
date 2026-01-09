import sys

# Read the file
with open('templates/admin_crm_view.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Original problematic lines
old_text = """        function guardarMensajeEmail() {
            const dealId = {{ deal.id }
        };
        const firma = document.getElementById('firmaVendedor').value;"""

# Corrected version
new_text = """        function guardarMensajeEmail() {
            const dealId = {{ deal.id }};
            const firma = document.getElementById('firmaVendedor').value;"""

# Replace
if old_text in content:
    content = content.replace(old_text, new_text)
    print("✓ Found and replaced the error")
    
    # Write back
    with open('templates/admin_crm_view.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ File saved successfully")
else:
    print("✗ Could not find the exact text to replace")
    print("\nSearching for similar patterns...")
    
    # Try to find the line
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'const dealId = {{ deal.id }' in line and '}}' not in line:
            print(f"Found error at line {i}: {line.strip()}")
