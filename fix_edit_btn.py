import re

file_path = 'templates/admin_clientes.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the pattern to find the edit button. 
# We look for the onclick attribute starting with 'editClient(' and ending with ')'
# We capture the arguments to replace them or just replace the whole onclick.
# The current arguments end with client.direccion...
pattern = r"onclick='editClient\(\{\{ client\.id\|tojson \}\}, \{\{ client\.nombre\|tojson\|replace\(\"\'\\\\\'\'\", \"&#39;\" \) \}\}, \{\{ client\.contacto\|tojson\|replace\(\"\'\\\\\'\'\", \"&#39;\" \) \}\}, \{\{ client\.telefono\|tojson\|replace\(\"\'\\\\\'\'\", \"&#39;\" \) \}\}, \{\{ client\.email\|tojson\|replace\(\"\'\\\\\'\'\", \"&#39;\" \) \}\}, \{\{ client\.direccion\|tojson\|replace\(\"\'\\\\\'\'\", \"&#39;\" \) \}\}\)'"

# New onclick with added fields
new_onclick = "onclick='editClient({{ client.id|tojson }}, {{ client.nombre|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ client.contacto|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ client.telefono|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ client.email|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ client.direccion|tojson|replace(\"\'\\\\\'\'\", \"&#39;\" ) }}, {{ (client.rfc or \"\")|tojson }}, {{ (client.vendedor_nombre or \"\")|tojson }}, {{ (client.vendedor_email or \"\")|tojson }}, {{ (client.vendedor_telefono or \"\")|tojson }})'"

# Perform replacement
# Since the pattern is complex with regex special chars and escaping, it's better to use exact string replacement if possible, 
# but the file view showed specific spacing.
# Let's try to construct the exact string from the file view I saw earlier.

target_string = '''onclick='editClient({{ client.id|tojson }}, {{ client.nombre|tojson|replace("'
                                \\'\'", "&#39;" ) }}, {{ client.contacto|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.telefono|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.email|tojson|replace("'\\''", "&#39;" ) }}, {{
                                client.direccion|tojson|replace("'\\''", "&#39;" ) }})'>Editar</button>'''

# The file view showed:
# 50:                                 onclick='editClient({{ client.id|tojson }}, {{ client.nombre|tojson|replace("'
# 51:                                 \''", "&#39;" ) }}, {{ client.contacto|tojson|replace("'\''", "&#39;" ) }}, {{
# 52:                                 client.telefono|tojson|replace("'\''", "&#39;" ) }}, {{
# 53:                                 client.email|tojson|replace("'\''", "&#39;" ) }}, {{
# 54:                                 client.direccion|tojson|replace("'\''", "&#39;" ) }})'>Editar</button>

# I'll try to match a simplified version using regex to be safe against whitespace variations.
regex_pattern = r"onclick='editClient\(\{\{ client\.id\|tojson \}\},.*?client\.direccion\|tojson\|replace\(\"\'\\\\'\'\", \"&#39;\" \) \}\}\)'"

match = re.search(regex_pattern, content, re.DOTALL)
if match:
    print("Found match!")
    # Construct the replacement string. I'll keep it on one line for simplicity or try to match indentation.
    replacement = "onclick='editClient({{ client.id|tojson }}, {{ client.nombre|tojson|replace(\"\\'\\'\", \"&#39;\" ) }}, {{ client.contacto|tojson|replace(\"\\'\\'\", \"&#39;\" ) }}, {{ client.telefono|tojson|replace(\"\\'\\'\", \"&#39;\" ) }}, {{ client.email|tojson|replace(\"\\'\\'\", \"&#39;\" ) }}, {{ client.direccion|tojson|replace(\"\\'\\'\", \"&#39;\" ) }}, {{ (client.rfc or \"\")|tojson }}, {{ (client.vendedor_nombre or \"\")|tojson }}, {{ (client.vendedor_email or \"\")|tojson }}, {{ (client.vendedor_telefono or \"\")|tojson }})'"
    
    # Actually, the escaping in the file is very specific: replace("' \''", "&#39;" )
    # Let's just replace the closing part of the function call.
    
    # Find the part ending with client.direccion... and the closing parenthesis
    # ... {{ client.direccion|tojson|replace("'\''", "&#39;" ) }})'>
    
    # I'll search for the specific substring of the last argument
    last_arg = "{{ client.direccion|tojson|replace(\"'\\''\", \"&#39;\" ) }})"
    
    # New arguments to append before the closing parenthesis
    new_args = ", {{ (client.rfc or \"\")|tojson }}, {{ (client.vendedor_nombre or \"\")|tojson }}, {{ (client.vendedor_email or \"\")|tojson }}, {{ (client.vendedor_telefono or \"\")|tojson }})"
    
    # Replace '})' with 'new_args + })'
    # But I need to be careful not to replace other occurrences if any.
    # The editClient call is unique enough.
    
    if last_arg in content:
        new_content = content.replace(last_arg, last_arg[:-1] + new_args + ")")
        with open(file_path, 'w', encoding='utf-8') as f_out:
            f_out.write(new_content)
        print("Successfully updated using string replacement.")
    else:
        print("Could not find exact string match. Trying regex...")
        # Regex to find the end of editClient call
        # Look for editClient( ... )
        # We want to insert before the last )
        
        # This regex finds the whole editClient call
        call_pattern = r"(onclick='editClient\(.*?)(\)\'>Editar</button>)"
        
        def replacer(m):
            return m.group(1) + new_args + m.group(2)
            
        new_content = re.sub(call_pattern, replacer, content, flags=re.DOTALL)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f_out:
                f_out.write(new_content)
            print("Successfully updated using regex.")
        else:
            print("Regex failed to match.")

else:
    print("Regex pattern did not match.")
