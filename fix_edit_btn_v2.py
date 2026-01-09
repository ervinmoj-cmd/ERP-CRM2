import re

file_path = 'templates/admin_clientes.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Broad regex to find the editClient call
# It starts with onclick='editClient({{ client.id|tojson }},
# and ends with )'>Editar</button>
# We use DOTALL to match across lines
pattern = r"onclick='editClient\(\{\{ client\.id\|tojson \}\},.*?\)\'>Editar</button>"

# The new onclick string
new_onclick = "onclick='editClient({{ client.id|tojson }}, {{ client.nombre|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ client.contacto|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ client.telefono|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ client.email|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ client.direccion|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ (client.rfc or \"\")|tojson }}, {{ (client.vendedor_nombre or \"\")|tojson }}, {{ (client.vendedor_email or \"\")|tojson }}, {{ (client.vendedor_telefono or \"\")|tojson }})'>Editar</button>"

# Check if we can find it
match = re.search(pattern, content, re.DOTALL)
if match:
    print(f"Found match: {match.group(0)[:50]}...")
    new_content = re.sub(pattern, new_onclick, content, flags=re.DOTALL)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully updated file.")
else:
    print("Still no match found.")
    # Debug: print what we see around the area
    start_marker = "onclick='editClient({{ client.id|tojson }},"
    idx = content.find(start_marker)
    if idx != -1:
        print(f"Found start marker at {idx}")
        print(f"Context: {content[idx:idx+200]}")
    else:
        print("Start marker not found.")
