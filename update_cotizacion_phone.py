import re

file_path = 'templates/admin_cotizacion_form.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add oninput to atencion_a field
# Find: <input type="text" name="atencion_a" id="atencion_a" list="contactos_list" value="{{ cotizacion.atencion_a if cotizacion else '' }}" autocomplete="off">
# Replace with: ... oninput="updateContactInfo(this)" ...

pattern_input = r'(<input type="text" name="atencion_a" id="atencion_a" list="contactos_list"[^>]*?)>'
match = re.search(pattern_input, content)
if match:
    if 'oninput=' not in match.group(1):
        new_input = match.group(1) + ' oninput="updateContactInfo(this)">'
        content = content.replace(match.group(0), new_input)
        print("Added oninput to atencion_a")
    else:
        print("oninput already present")

# 2. Update fillClientInfo to store contacts data globally
# We'll add a global variable `currentClientData`
# Find: function fillClientInfo() {
# Insert: window.currentClientData = null; before it (or just use window property inside)

# We'll modify the fetch success callback to store data
# Find: .then(function(data) {
# Insert: window.currentClientData = data;

pattern_fetch = r'\.then\(function\(data\) \{'
match = re.search(pattern_fetch, content)
if match:
    content = content.replace(match.group(0), match.group(0) + '\n                        window.currentClientData = data;')
    print("Added data storage to fillClientInfo")

# 3. Add updateContactInfo function
# We'll add it after fillClientInfo
js_func = '''
        function updateContactInfo(input) {
            var val = input.value;
            var data = window.currentClientData;
            
            if (!data) return;
            
            // Check main contact
            if (data.contacto === val) {
                document.getElementById('cliente_telefono').value = data.telefono || '';
                return;
            }
            
            // Check additional contacts
            if (data.contactos && data.contactos.length > 0) {
                var contact = data.contactos.find(function(c) { return c.nombre === val; });
                if (contact) {
                    document.getElementById('cliente_telefono').value = contact.telefono || '';
                }
            }
        }
'''

# Insert after fillClientInfo function closes
# We look for the end of fillClientInfo. It ends before // Search product
pattern_end = r'\}\s*// Search product'
match = re.search(pattern_end, content)
if match:
    content = content.replace(match.group(0), '}\n' + js_func + '\n        // Search product')
    print("Added updateContactInfo function")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
