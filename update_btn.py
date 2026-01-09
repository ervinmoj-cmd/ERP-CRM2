import re

# Read file
with open('templates/admin_clientes.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update edit button onclick to include new fields
old_edit_btn = '''onclick='editClient({{ client.id|tojson }}, {{ client.nombre|tojson|replace("'
                                \\'\'", "&#39;" ) }}, {{ client.contacto|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.telefono|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.email|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.direccion|tojson|replace("'\\''", "&#39;" ) }})''>Editar</button>'''

new_edit_btn = '''onclick='editClient({{ client.id|tojson }}, {{ client.nombre|tojson|replace("'
                                \\'\'", "&#39;" ) }}, {{ client.contacto|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.telefono|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.email|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.direccion|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.rfc|default("")|tojson }}, {{
                                client.vendedor_nombre|default("")|tojson }}, {{
                                client.vendedor_email|default("")|tojson }}, {{
                                client.vendedor_telefono|default("")|tojson }})''>Editar</button>'''

if old_edit_btn in content:
    content = content.replace(old_edit_btn, new_edit_btn)
    print("Updated edit button onclick")
else:
    print("Edit button pattern not found, trying simpler approach...")
    # Try simpler pattern
    old = "client.direccion|tojson|replace(\"'\\\\''\"" 
    if old in content:
        print("Found direccion pattern")

# Write back
with open('templates/admin_clientes.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
