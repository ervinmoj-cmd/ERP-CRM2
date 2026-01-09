import re

file_path = 'templates/admin_cotizacion_form.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The issue: fillClientInfo() resets RFC and Atención a even in edit mode.
# Solution: Check if in edit mode (cotizacion exists) and preserve values.
# We need to wrap the "fill" logic so it doesn't overwrite when editing.

# Find the fillClientInfo function and update it to check edit mode.
# The key changes:
# 1. On page load in edit mode, populate the contacts dropdown but DON'T change the selected value.
# 2. In edit mode, RFC should come from the stored cotizacion, not from the client API.

# Since admin_cotizacion_form.html has access to {{ cotizacion }}, we can add a JS variable:
# var isEditMode = {{ 'true' if cotizacion else 'false' }};

# Insert this variable at the start of the script
script_start = '<script>'
script_insert = '''<script>
        var isEditMode = {{ 'true' if cotizacion else 'false' }};
        var savedAtencionA = {{ (cotizacion.atencion_a if cotizacion else '')|tojson }};
        var savedRFC = {{ (cotizacion.cliente_rfc if cotizacion else '')|tojson }};
'''
content = content.replace(script_start, script_insert, 1)  # Only replace first occurrence

# Now update fillClientInfo to check isEditMode
# We want to:
# - If isEditMode AND this is the initial load (not a user change), don't override RFC and atencion_a
# - If user changes client, THEN we update everything

# Add a flag to track if this is user-initiated or automatic load
# We can add a parameter to fillClientInfo: fillClientInfo(userInitiated)

# Find: function fillClientInfo() {
# Replace with: function fillClientInfo(userInitiated) {

content = content.replace('function fillClientInfo() {', 'function fillClientInfo(userInitiated) {')

# Find the onchange that calls fillClientInfo() and change to fillClientInfo(true)
content = content.replace('onchange="fillClientInfo()"', 'onchange="fillClientInfo(true)"')

# Now, inside fillClientInfo, after fetching data, check isEditMode and userInitiated
# If isEditMode && !userInitiated, don't overwrite RFC and atencion_a

# Find: document.getElementById('cliente_rfc').value = data.rfc || '';
# Insert check before it

old_rfc_line = "document.getElementById('cliente_rfc').value = data.rfc || '';"
new_rfc_line = """if (!isEditMode || userInitiated) {
                            document.getElementById('cliente_rfc').value = data.rfc || '';
                        } else {
                            // In edit mode on initial load, preserve the saved RFC
                            document.getElementById('cliente_rfc').value = savedRFC || data.rfc || '';
                        }"""

content = content.replace(old_rfc_line, new_rfc_line)

# For Atención a, we need to preserve the selected value in the select dropdown
# Find the part where it auto-selects the first contact and modify it

# Find: if (contactSelect.options.length > 1) {
#         contactSelect.selectedIndex = 1;
#         input.value = contactSelect.value;
# Replace with: check if savedAtencionA matches any option

old_autoselect = """if (contactSelect.options.length > 1) {
                                contactSelect.selectedIndex = 1;
                                input.value = contactSelect.value;
                                updateContactInfo(contactSelect);
                            }"""

new_autoselect = """if (contactSelect.options.length > 1) {
                                // In edit mode, try to select the saved contact
                                if (isEditMode && savedAtencionA) {
                                    var found = false;
                                    for (var i = 0; i < contactSelect.options.length; i++) {
                                        if (contactSelect.options[i].value === savedAtencionA) {
                                            contactSelect.selectedIndex = i;
                                            found = true;
                                            break;
                                        }
                                    }
                                    if (!found) {
                                        // Not in list, switch to manual mode
                                        document.getElementById('atencion_input_group').style.display = 'flex';
                                        contactSelect.style.display = 'none';
                                        input.value = savedAtencionA;
                                        contactMode = 'manual';
                                    } else {
                                        input.value = savedAtencionA;
                                    }
                                } else {
                                    contactSelect.selectedIndex = 1;
                                    input.value = contactSelect.value;
                                    updateContactInfo(contactSelect);
                                }
                            }"""

content = content.replace(old_autoselect, new_autoselect)

# Finally, we need to call fillClientInfo(false) on page load if in edit mode
# Find: {% if cotizacion %}
# Look for existing DOMContentLoaded or add one

# Add a DOMContentLoaded handler at the end of script section
# Find the closing </script> before the final </body>

# Actually, let's add it more directly: at the end of the script section, before </script>
# We add: document.addEventListener('DOMContentLoaded', function() { if (isEditMode) fillClientInfo(false); });

# Find: </script>
# Insert before it (but make sure we're at the end of the main script, not a sub-script)

# Let's append to the end of the script block
# Since we can have multiple </script> tags, we need to find the right one.
# The main script block ends before </body>

end_script = '</script>\n</body>'
init_load = '''
        // On page load, if editing, populate contacts dropdown
        document.addEventListener('DOMContentLoaded', function() {
            if (isEditMode) {
                var clientId = document.getElementById('clienteSelect').value;
                if (clientId) {
                    fillClientInfo(false);
                }
            }
        });
    </script>
</body>'''

content = content.replace(end_script, init_load)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
