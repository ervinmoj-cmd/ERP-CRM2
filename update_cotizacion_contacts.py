import re

file_path = 'templates/admin_cotizacion_form.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add RFC field after Client Name
# Find: <label>Nombre Cliente *</label> ... </div>
# Insert RFC field after that div
rfc_field = '''
                    <div class="form-group">
                        <label>RFC</label>
                        <input type="text" name="cliente_rfc" id="cliente_rfc" value="{{ cotizacion.cliente_rfc if cotizacion else '' }}" readonly style="background:#f5f5f5;">
                    </div>'''

# We need to find the closing div of the Nombre Cliente group
pattern_name = r'(<label>Nombre Cliente \*</label>\s*<input[^>]*>\s*</div>)'
match = re.search(pattern_name, content)
if match:
    content = content.replace(match.group(1), match.group(1) + rfc_field)
    print("Added RFC field")

# 2. Change "Atención a" to a datalist/select
# Find: <input type="text" name="atencion_a" id="atencion_a" value="{{ cotizacion.atencion_a if cotizacion else '' }}">
# Replace with input + datalist
atencion_field = '''
                        <label>Atención a</label>
                        <input type="text" name="atencion_a" id="atencion_a" list="contactos_list" value="{{ cotizacion.atencion_a if cotizacion else '' }}" autocomplete="off">
                        <datalist id="contactos_list"></datalist>'''

pattern_atencion = r'<label>Atención a</label>\s*<input type="text" name="atencion_a"[^>]*>'
content = re.sub(pattern_atencion, atencion_field, content)
print("Updated Atención a field")

# 3. Update fillClientInfo JS function
# We need to fetch client details including contacts and populate the datalist
js_update = '''
        // Fill client info when selecting client
        function fillClientInfo() {
            var select = document.getElementById('clienteSelect');
            var clientId = select.value;
            
            if (clientId) {
                // Fetch full client details including contacts
                fetch('/api/cliente/' + clientId)
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        document.getElementById('cliente_nombre').value = data.nombre || '';
                        document.getElementById('cliente_direccion').value = data.direccion || '';
                        document.getElementById('cliente_telefono').value = data.telefono || '';
                        document.getElementById('cliente_rfc').value = data.rfc || '';
                        
                        // Populate contacts datalist
                        var datalist = document.getElementById('contactos_list');
                        datalist.innerHTML = '';
                        
                        // Add main contact
                        if (data.contacto) {
                            var opt = document.createElement('option');
                            opt.value = data.contacto;
                            datalist.appendChild(opt);
                            // Default to main contact if field is empty
                            if (!document.getElementById('atencion_a').value) {
                                document.getElementById('atencion_a').value = data.contacto;
                            }
                        }
                        
                        // Add additional contacts
                        if (data.contactos && data.contactos.length > 0) {
                            data.contactos.forEach(function(c) {
                                var opt = document.createElement('option');
                                opt.value = c.nombre; // + (c.puesto ? ' (' + c.puesto + ')' : '');
                                datalist.appendChild(opt);
                            });
                        }
                    });
            } else {
                // Clear fields
                document.getElementById('cliente_nombre').value = '';
                document.getElementById('cliente_direccion').value = '';
                document.getElementById('cliente_telefono').value = '';
                document.getElementById('cliente_rfc').value = '';
                document.getElementById('atencion_a').value = '';
                document.getElementById('contactos_list').innerHTML = '';
            }
        }
'''

# Replace the old fillClientInfo function
# It starts with function fillClientInfo() { and ends before // Search product
pattern_js = r'function fillClientInfo\(\) \{[\s\S]*?\}\s*// Search product'
# We need to be careful with the regex matching too much.
# Let's find the start and the next function start.
start_idx = content.find('function fillClientInfo() {')
end_idx = content.find('// Search product', start_idx)

if start_idx != -1 and end_idx != -1:
    old_js = content[start_idx:end_idx]
    content = content.replace(old_js, js_update + "\n\n        // Search product")
    print("Updated fillClientInfo JS")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
