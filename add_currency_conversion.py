import re

file_path = 'templates/admin_cotizacion_form.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add id and onchange to moneda select
old_moneda = '<select name="moneda">'
new_moneda = '<select name="moneda" id="monedaSelect" onchange="convertCurrency()">'
content = content.replace(old_moneda, new_moneda)

# 2. Add id and onchange to tipo_cambio input
old_tc = 'name="tipo_cambio"'
new_tc = 'name="tipo_cambio" id="tipoCambioInput"'
content = content.replace(old_tc, new_tc)

# 3. Add a hidden field to store the previous currency and a button to apply conversion
# Insert after tipo_cambio input
old_tc_full = '''<div class="form-group">
                        <label>Tipo de Cambio</label>
                        <input type="number" step="0.01" name="tipo_cambio" id="tipoCambioInput"
                            value="{{ cotizacion.tipo_cambio if cotizacion else '1.0' }}">
                    </div>'''

new_tc_full = '''<div class="form-group">
                        <label>Tipo de Cambio</label>
                        <input type="number" step="0.01" name="tipo_cambio" id="tipoCambioInput"
                            value="{{ cotizacion.tipo_cambio if cotizacion else '1.0' }}">
                    </div>
                    <div class="form-group" style="display:flex; align-items:flex-end;">
                        <button type="button" class="btn btn-secondary btn-sm" onclick="applyConversion()" 
                            title="Convertir todos los precios usando el tipo de cambio">💱 Convertir Precios</button>
                    </div>'''

content = content.replace(old_tc_full, new_tc_full)

# 4. Add the conversion JavaScript function
js_conversion = '''
        // Track previous currency for conversion
        var previousCurrency = document.getElementById('monedaSelect').value;
        
        function convertCurrency() {
            // Just update the tracked currency, don't auto-convert
            // User needs to click "Convertir Precios" button
        }
        
        function applyConversion() {
            var currentCurrency = document.getElementById('monedaSelect').value;
            var tipoCambio = parseFloat(document.getElementById('tipoCambioInput').value) || 1;
            
            if (tipoCambio <= 0) {
                alert('Por favor ingrese un tipo de cambio válido mayor a 0');
                return;
            }
            
            // Get all price inputs
            var precioInputs = document.querySelectorAll('input[name="item_precio[]"]');
            
            if (currentCurrency === 'MXN' && previousCurrency === 'USD') {
                // USD to MXN: multiply by exchange rate
                precioInputs.forEach(function(input) {
                    var precio = parseFloat(input.value) || 0;
                    input.value = (precio * tipoCambio).toFixed(2);
                });
                alert('Precios convertidos de USD a MXN (x' + tipoCambio + ')');
            } else if (currentCurrency === 'USD' && previousCurrency === 'MXN') {
                // MXN to USD: divide by exchange rate
                precioInputs.forEach(function(input) {
                    var precio = parseFloat(input.value) || 0;
                    input.value = (precio / tipoCambio).toFixed(2);
                });
                alert('Precios convertidos de MXN a USD (/' + tipoCambio + ')');
            } else {
                alert('No hay conversión necesaria. La moneda actual y anterior son iguales.');
                return;
            }
            
            // Update previous currency
            previousCurrency = currentCurrency;
            
            // Recalculate all rows and totals
            precioInputs.forEach(function(input) {
                calculateRow(input);
            });
            calculateTotals();
        }
'''

# Insert after the isEditMode variable declaration
insert_after = "var isEditMode = {{ 'true' if cotizacion else 'false' }};"
content = content.replace(insert_after, insert_after + js_conversion)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
