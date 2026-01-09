import re

file_path = 'templates/admin_clientes.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# HTML for contacts section
contacts_html = '''
                <hr style="margin: 15px 0;">
                <h4 style="margin-bottom: 10px; color: #666;">Contactos Adicionales</h4>
                <div id="contacts_container_PREFIX"></div>
                <button type="button" class="btn btn-sm btn-secondary" onclick="addContactRow(\'contacts_container_PREFIX\')">+ Agregar Contacto</button>
'''

# Insert into Add Client modal (before submit button)
# We look for the vendedor fields we added earlier
add_marker = '<input type="text" name="vendedor_telefono">\n                    </div>\n                </div>'
if add_marker in content:
    content = content.replace(add_marker, add_marker + contacts_html.replace('PREFIX', 'add'))
    print("Added contacts section to Add Client modal")

# Insert into Edit Client modal
edit_marker = '<input type="text" name="vendedor_telefono" id="edit_vendedor_telefono">\n                    </div>\n                </div>'
if edit_marker in content:
    content = content.replace(edit_marker, edit_marker + contacts_html.replace('PREFIX', 'edit'))
    print("Added contacts section to Edit Client modal")

# JavaScript for adding contact rows
js_func = '''
        function addContactRow(containerId, data = {}) {
            const container = document.getElementById(containerId);
            const div = document.createElement('div');
            div.className = 'contact-row';
            div.style.marginBottom = '10px';
            div.style.padding = '10px';
            div.style.background = '#f9f9f9';
            div.style.border = '1px solid #eee';
            div.style.borderRadius = '4px';
            
            div.innerHTML = `
                <div class="form-row" style="margin-bottom: 5px;">
                    <div class="form-group" style="margin-bottom: 0;">
                        <input type="text" name="contact_nombre[]" placeholder="Nombre" value="${data.nombre || ''}" required style="font-size: 12px;">
                    </div>
                    <div class="form-group" style="margin-bottom: 0;">
                        <input type="text" name="contact_puesto[]" placeholder="Puesto" value="${data.puesto || ''}" style="font-size: 12px;">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group" style="margin-bottom: 0;">
                        <input type="email" name="contact_email[]" placeholder="Email" value="${data.email || ''}" style="font-size: 12px;">
                    </div>
                    <div class="form-group" style="margin-bottom: 0;">
                        <input type="text" name="contact_telefono[]" placeholder="Teléfono" value="${data.telefono || ''}" style="font-size: 12px;">
                    </div>
                    <button type="button" class="btn btn-sm btn-danger" onclick="this.parentElement.parentElement.remove()" style="margin-top: auto; padding: 2px 8px;">&times;</button>
                </div>
            `;
            container.appendChild(div);
        }
'''

# Insert JS function
if 'function openModal(modalId) {' in content:
    content = content.replace('function openModal(modalId) {', js_func + '\n        function openModal(modalId) {')
    print("Added addContactRow JS function")

# Update editClient function to load contacts
# We need to fetch contacts via API when editing, or pass them in (but passing list is messy in HTML)
# Better to fetch via API since we already have /api/cliente/<id>

# Find the editClient function and update it
# We'll append the fetch logic at the end of the function
fetch_logic = '''
            // Load contacts
            const contactsContainer = document.getElementById('contacts_container_edit');
            contactsContainer.innerHTML = '';
            fetch(`/api/cliente/${id}`)
                .then(r => r.json())
                .then(data => {
                    if (data.contactos && data.contactos.length > 0) {
                        data.contactos.forEach(c => addContactRow('contacts_container_edit', c));
                    }
                });
'''

# Insert before openModal('editClientModal');
if "openModal('editClientModal');" in content:
    content = content.replace("openModal('editClientModal');", fetch_logic + "\n            openModal('editClientModal');")
    print("Updated editClient to fetch contacts")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
