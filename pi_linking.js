
// --- Client and Quote Linking Logic ---
function onClientChange() {
    var input = document.getElementById('solicitadoInput');
    var list = document.getElementById('clients_list');
    var val = input.value;
    var clientId = null;

    // Find client ID from datalist
    for (var i = 0; i < list.options.length; i++) {
        if (list.options[i].value === val) {
            clientId = list.options[i].getAttribute('data-id');
            break;
        }
    }

    document.getElementById('client_id_hidden').value = clientId || '';
    var cotSelect = document.getElementById('cotizacionSelect');

    if (clientId) {
        // Fetch Quotes for this client
        fetch('/api/finanzas/cotizaciones/' + clientId)
            .then(r => r.json())
            .then(data => {
                cotSelect.innerHTML = '<option value="">-- Seleccionar --</option>';
                if (data.success && data.cotizaciones) {
                    data.cotizaciones.forEach(c => {
                        var opt = document.createElement('option');
                        opt.value = c.id;
                        opt.innerText = c.folio + " - " + (c.referencia || "Sin Ref");
                        cotSelect.appendChild(opt);
                    });
                }
            })
            .catch(e => console.error(e));
    } else {
        cotSelect.innerHTML = '<option value="">-- Seleccionar Cliente Primero --</option>';
    }
}

function fillFromCotizacion() {
    var select = document.getElementById('cotizacionSelect');
    var val = select.value;

    if (!val) return;

    fetch('/api/cotizaciones/detalle/' + val)
        .then(r => r.json())
        .then(cot => {
            if (cot.error) return;

            // Fill Items
            var tbody = document.querySelector('#itemsTable tbody');
            tbody.innerHTML = ''; // Clear current

            if (cot.items && cot.items.length > 0) {
                cot.items.forEach((item, index) => {
                    var newRow = document.createElement('tr');
                    var lineNum = index + 1;
                    newRow.innerHTML = `
                                <td><input type="number" name="item_linea[]" value="${lineNum}" readonly style="background:#f5f5f5;"></td>
                                <td><input type="number" step="0.01" name="item_cantidad[]" value="${item.cantidad}" oninput="calculateRow(this)"></td>
                                <td><input type="text" name="item_unidad[]" value="${item.unidad || 'PZA'}"></td>
                                <td class="autocomplete-container">
                                    <input type="text" name="item_numero_parte[]" value="${item.numero_parte || ''}" class="parte-input" oninput="searchProducto(this)">
                                    <div class="autocomplete-results"></div>
                                </td>
                                <td><input type="text" name="item_descripcion[]" value="${item.descripcion || ''}"></td>
                                <td>
                                    <select name="item_estatus[]">
                                        <option value="Pendiente">Pendiente</option>
                                        <option value="Recibido">Recibido</option>
                                        <option value="Cancelado">Cancelado</option>
                                        <option value="En Tránsito">En Tránsito</option>
                                    </select>
                                </td>
                                <td><input type="text" name="item_tiempo_entrega[]" value="${item.tiempo_entrega_item || '1-2 semanas'}"></td>
                                <td><input type="number" step="0.01" name="item_precio_unitario[]" value="${item.precio_unitario || 0}" oninput="calculateRow(this)"></td>
                                <td><input type="number" step="0.01" name="item_importe[]" value="${item.importe || 0}" readonly style="background:#f5f5f5;"></td>
                                <td><button type="button" class="btn-remove" onclick="removeRow(this)">&times;</button></td>
                            `;
                    tbody.appendChild(newRow);
                });
                calculateTotals();
            }

            // Optionally set Currency if available in PI form
            if (cot.moneda) {
                document.getElementById('monedaSelect').value = cot.moneda;
            }
        });
}
