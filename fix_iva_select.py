import re

file_path = 'templates/admin_cotizacion_form.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the IVA input with a select dropdown
old_iva = '''<tr>
                            <td>IVA (%):</td>
                            <td><input type="number" step="0.01" name="iva_porcentaje" id="iva_porcentaje"
                                    value="{{ cotizacion.iva_porcentaje if cotizacion else '0.08' }}"
                                    onchange="calculateTotals()"></td>
                        </tr>'''

new_iva = '''<tr>
                            <td>IVA:</td>
                            <td>
                                <select name="iva_porcentaje" id="iva_porcentaje" onchange="calculateTotals()" style="width:100%; padding:8px;">
                                    <option value="0.16" {% if cotizacion and cotizacion.iva_porcentaje|float == 0.16 %}selected{% elif not cotizacion %}selected{% endif %}>16% (General)</option>
                                    <option value="0.08" {% if cotizacion and cotizacion.iva_porcentaje|float == 0.08 %}selected{% endif %}>8% (Frontera)</option>
                                    <option value="0" {% if cotizacion and cotizacion.iva_porcentaje|float == 0 %}selected{% endif %}>0% (Exento)</option>
                                </select>
                            </td>
                        </tr>'''

if old_iva in content:
    content = content.replace(old_iva, new_iva)
    print("Replaced IVA input with select dropdown")
else:
    # Try to find with regex in case of whitespace differences
    pattern = r'<tr>\s*<td>IVA \(%\):</td>\s*<td><input[^>]*name="iva_porcentaje"[^>]*></td>\s*</tr>'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_iva, content, flags=re.DOTALL)
        print("Replaced IVA input with select dropdown (via regex)")
    else:
        print("Could not find IVA input to replace")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
