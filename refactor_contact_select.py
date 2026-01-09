import re

file_path = 'templates/admin_cotizacion_form.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace the current "Atención a" input/datalist with a container having both Select and Input
# Find the current field
pattern_field = r'<label>Atención a</label>\s*<input type="text" name="atencion_a" id="atencion_a"[^>]*>\s*<datalist id="contactos_list"></datalist>'

# New HTML structure
# We use a container to manage the two states
new_field = '''<label>Atención a</label>
                        <div id="atencion_container">
                            <!-- Select for contacts -->
                            <select id="atencion_select" class="form-control" onchange="onContactSelect(this)" style="display:none;">
                                <option value="">-- Seleccionar --</option>
                            </select>
                            <!-- Input for manual entry -->
                            <div id="atencion_input_group" style="display:flex;">
                                <input type="text" name="atencion_a" id="atencion_a" value="{{ cotizacion.atencion_a if cotizacion else '' }}" placeholder="Nombre del contacto">
                                <button type="button" id="btn_toggle_contact" class="btn btn-secondary btn-sm" onclick="toggleContactMode()" style="margin-left:5px; display:none;" title="Cambiar a lista/manual">🔄</button>
                            </div>
                        </div>'''

# We need to find the exact string to replace. Since I modified it in previous steps, I should be careful.
# The previous step added oninput="updateContactInfo(this)"
# Let's try to match loosely.
pattern_loose = r'<label>Atención a</label>\s*<input[^>]*id="atencion_a"[^>]*>\s*<datalist[^>]*></datalist>'

match = re.search(pattern_loose, content, re.DOTALL)
if match:
    content = content.replace(match.group(0), new_field)
    print("Replaced Atención a field with Select/Input combo")
else:
    print("Could not find Atención a field to replace")

# 2. Add styles if needed (form-control is standard bootstrap, but we might need custom style)
# I'll rely on existing styles for now, assuming input styles apply to select if I don't add class.
# Actually, the existing inputs don't have class="form-control", they are styled by tag.
# So I should remove class="form-control" and let CSS handle `select` tag if it exists, or add inline style.
content = content.replace('class="form-control"', 'style="width:100%; height:38px; padding:8px;"')


# 3. Update JS functions
# We need:
# - fillClientInfo: populate select, show select if contacts exist, else show input.
# - onContactSelect: update hidden input (or the actual input name), update phone.
# - toggleContactMode: switch between select and input.

js_code = '''
        var contactMode = 'manual'; // 'manual' or 'select'

        function toggleContactMode() {
            var select = document.getElementById('atencion_select');
            var inputGroup = document.getElementById('atencion_input_group');
            var input = document.getElementById('atencion_a');
            
            if (contactMode === 'select') {
                // Switch to manual
                select.style.display = 'none';
                inputGroup.style.display = 'flex';
                input.disabled = false;
                input.focus();
                contactMode = 'manual';
            } else {
                // Switch to select (only if options exist)
                if (select.options.length > 1) {
                    select.style.display = 'block';
                    inputGroup.style.display = 'none';
                    input.disabled = true; // Disable so it doesn't submit if we were using select (wait, we need to sync value)
                    contactMode = 'select';
                }
            }
        }

        function onContactSelect(select) {
            var val = select.value;
            var input = document.getElementById('atencion_a');
            
            if (val === '__manual__') {
                toggleContactMode();
                return;
            }
            
            // Update the text input (which is the one submitted, unless we change names)
            // Actually, if we use select, we should probably make the input hidden and hold the value.
            // But to keep it simple: When select changes, we update the input value.
            // AND we update the phone number.
            
            input.value = val;
            updateContactInfo(select); // Reuse existing logic but pass select
        }

        // Update fillClientInfo to populate select
        function fillClientInfo() {
            var selectClient = document.getElementById('clienteSelect');
            var clientId = selectClient.value;
            
            if (clientId) {
                fetch('/api/cliente/' + clientId)
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        window.currentClientData = data;
                        
                        document.getElementById('cliente_nombre').value = data.nombre || '';
                        document.getElementById('cliente_direccion').value = data.direccion || '';
                        document.getElementById('cliente_telefono').value = data.telefono || '';
                        document.getElementById('cliente_rfc').value = data.rfc || '';
                        
                        // Populate contacts select
                        var contactSelect = document.getElementById('atencion_select');
                        contactSelect.innerHTML = '<option value="">-- Seleccionar Contacto --</option>';
                        
                        var hasContacts = false;
                        
                        // Add main contact
                        if (data.contacto) {
                            var opt = document.createElement('option');
                            opt.value = data.contacto;
                            opt.textContent = data.contacto + ' (Principal)';
                            contactSelect.appendChild(opt);
                            hasContacts = true;
                        }
                        
                        // Add additional contacts
                        if (data.contactos && data.contactos.length > 0) {
                            data.contactos.forEach(function(c) {
                                var opt = document.createElement('option');
                                opt.value = c.nombre;
                                opt.textContent = c.nombre + (c.puesto ? ' - ' + c.puesto : '');
                                contactSelect.appendChild(opt);
                            });
                            hasContacts = true;
                        }
                        
                        // Add manual option
                        var manualOpt = document.createElement('option');
                        manualOpt.value = "__manual__";
                        manualOpt.textContent = "-- Escribir otro nombre --";
                        contactSelect.appendChild(manualOpt);
                        
                        // Logic to switch view
                        var input = document.getElementById('atencion_a');
                        var btn = document.getElementById('btn_toggle_contact');
                        
                        if (hasContacts) {
                            // Show select
                            contactSelect.style.display = 'block';
                            document.getElementById('atencion_input_group').style.display = 'none';
                            input.disabled = false; // Keep enabled to store value? No, if hidden it submits.
                            // Wait, if I hide the input div, the input is still there.
                            // I want the Select to drive the Input value.
                            // Submitting the form: we need `atencion_a` to have the value.
                            // If I use the Select, I should update the Input value.
                            
                            // Let's auto-select the first contact
                            if (contactSelect.options.length > 1) {
                                contactSelect.selectedIndex = 1;
                                input.value = contactSelect.value;
                                updateContactInfo(contactSelect);
                            }
                            
                            contactMode = 'select';
                            btn.style.display = 'block'; // Show toggle button in manual mode? No, toggle is inside input group.
                            // If we are in select mode, we need a way to go to manual.
                            // The "Manual" option in select does that.
                            
                        } else {
                            // No contacts, show input
                            contactSelect.style.display = 'none';
                            document.getElementById('atencion_input_group').style.display = 'flex';
                            btn.style.display = 'none';
                            contactMode = 'manual';
                        }
                    });
            } else {
                // Clear fields
                document.getElementById('cliente_nombre').value = '';
                document.getElementById('cliente_direccion').value = '';
                document.getElementById('cliente_telefono').value = '';
                document.getElementById('cliente_rfc').value = '';
                document.getElementById('atencion_a').value = '';
                
                document.getElementById('atencion_select').style.display = 'none';
                document.getElementById('atencion_input_group').style.display = 'flex';
                document.getElementById('btn_toggle_contact').style.display = 'none';
            }
        }
'''

# Replace the existing fillClientInfo function
# We can find it by its name
pattern_js = r'function fillClientInfo\(\) \{[\s\S]*?\}\s*// Search product'
# Actually, I added updateContactInfo after it, so the end marker might be different.
# Let's replace the whole block including updateContactInfo if possible, or just fillClientInfo.

# Find fillClientInfo start
start = content.find('function fillClientInfo() {')
if start != -1:
    # Find the end of it. It ends before function updateContactInfo
    end = content.find('function updateContactInfo(input) {')
    if end != -1:
        # Replace fillClientInfo
        content = content[:start] + js_code + '\n\n' + content[end:]
        print("Updated JS functions")
    else:
        print("Could not find updateContactInfo start")
else:
    print("Could not find fillClientInfo start")

# We also need to update updateContactInfo to handle the select element or input
# The existing updateContactInfo expects an input/element with .value
# My new onContactSelect calls it with the select element.
# The logic `var val = input.value;` works for select too.
# So updateContactInfo should be fine as is.

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
