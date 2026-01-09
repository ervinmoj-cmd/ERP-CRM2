import re

# Read file
with open('templates/admin_clientes.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add fields to Add Client modal (after Direccion textarea, before submit button)
add_client_insert = '''                <div class="form-group">
                    <label>RFC</label>
                    <input type="text" name="rfc" placeholder="RFC del cliente">
                </div>
                <hr style="margin: 15px 0;">
                <h4 style="margin-bottom: 10px; color: #666;">Datos del Vendedor</h4>
                <div class="form-group">
                    <label>Nombre del Vendedor</label>
                    <input type="text" name="vendedor_nombre" placeholder="Quien dio de alta al cliente">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Email Vendedor</label>
                        <input type="email" name="vendedor_email">
                    </div>
                    <div class="form-group">
                        <label>Teléfono Vendedor</label>
                        <input type="text" name="vendedor_telefono">
                    </div>
                </div>
'''

# Insert before the first "Guardar Cliente" button in Add modal
old_add = '</textarea>\n                </div>\n                <button type="submit" class="btn btn-primary">Guardar Cliente</button>'
new_add = '</textarea>\n                </div>\n' + add_client_insert + '                <button type="submit" class="btn btn-primary">Guardar Cliente</button>'

if old_add in content:
    content = content.replace(old_add, new_add, 1)  # Only replace first occurrence
    print("Added fields to Add Client modal")
else:
    print("Add Client pattern not found")

# Add fields to Edit Client modal
edit_client_insert = '''                <div class="form-group">
                    <label>RFC</label>
                    <input type="text" name="rfc" id="edit_rfc" placeholder="RFC del cliente">
                </div>
                <hr style="margin: 15px 0;">
                <h4 style="margin-bottom: 10px; color: #666;">Datos del Vendedor</h4>
                <div class="form-group">
                    <label>Nombre del Vendedor</label>
                    <input type="text" name="vendedor_nombre" id="edit_vendedor_nombre">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Email Vendedor</label>
                        <input type="email" name="vendedor_email" id="edit_vendedor_email">
                    </div>
                    <div class="form-group">
                        <label>Teléfono Vendedor</label>
                        <input type="text" name="vendedor_telefono" id="edit_vendedor_telefono">
                    </div>
                </div>
'''

old_edit = 'id="edit_direccion"></textarea>\n                </div>\n                <button type="submit" class="btn btn-primary">Actualizar Cliente</button>'
new_edit = 'id="edit_direccion"></textarea>\n                </div>\n' + edit_client_insert + '                <button type="submit" class="btn btn-primary">Actualizar Cliente</button>'

if old_edit in content:
    content = content.replace(old_edit, new_edit)
    print("Added fields to Edit Client modal")
else:
    print("Edit Client pattern not found")

# Update editClient function to include new fields  
old_func = '''function editClient(id, nombre, contacto, telefono, email, direccion) {
            document.getElementById('edit_nombre').value = nombre;
            document.getElementById('edit_contacto').value = contacto || '';
            document.getElementById('edit_telefono').value = telefono || '';
            document.getElementById('edit_email').value = email || '';
            document.getElementById('edit_direccion').value = direccion || '';
            document.getElementById('editClientForm').action = `/admin/clientes/editar/${id}`;
            openModal('editClientModal');
        }'''

new_func = '''function editClient(id, nombre, contacto, telefono, email, direccion, rfc, vendedor_nombre, vendedor_email, vendedor_telefono) {
            document.getElementById('edit_nombre').value = nombre;
            document.getElementById('edit_contacto').value = contacto || '';
            document.getElementById('edit_telefono').value = telefono || '';
            document.getElementById('edit_email').value = email || '';
            document.getElementById('edit_direccion').value = direccion || '';
            document.getElementById('edit_rfc').value = rfc || '';
            document.getElementById('edit_vendedor_nombre').value = vendedor_nombre || '';
            document.getElementById('edit_vendedor_email').value = vendedor_email || '';
            document.getElementById('edit_vendedor_telefono').value = vendedor_telefono || '';
            document.getElementById('editClientForm').action = `/admin/clientes/editar/${id}`;
            openModal('editClientModal');
        }'''

if old_func in content:
    content = content.replace(old_func, new_func)
    print("Updated editClient function")
else:
    print("editClient function not found exactly")

# Write back
with open('templates/admin_clientes.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
