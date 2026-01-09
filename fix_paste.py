import re

# Read the file
with open('templates/equipos.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the button section and add paste button
pattern1 = r'(<button type="button" class="btn btn-sm btn-success mt-4" onclick="addPartRow\(\)">\s*<i class="bi bi-plus"></i> Agregar Refacci[oó]n\s*</button>\s*</div>\s*</div>)'

replacement1 = r'''<button type="button" class="btn btn-sm btn-success mt-4" onclick="addPartRow()">
                                <i class="bi bi-plus"></i> Agregar Refacción
                            </button>
                            <button type="button" class="btn btn-sm btn-info mt-4 ms-2" onclick="togglePasteArea()">
                                <i class="bi bi-clipboard"></i> Pegar Excel
                            </button>
                        </div>
                    </div>
                    
                    <div id="paste-area-container" style="display: none;" class="mb-3">
                        <label class="form-label">Pega desde Excel (Descripción | No. Parte | Cantidad):</label>
                        <textarea id="paste-area" class="form-control" rows="5" placeholder="Pega aquí desde Excel..."></textarea>
                        <button type="button" class="btn btn-sm btn-primary mt-2" onclick="processPastedData()">Importar</button>
                        <button type="button" class="btn btn-sm btn-secondary mt-2" onclick="togglePasteArea()">Cancelar</button>
                    </div>'''

content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE | re.DOTALL)

# Add the JavaScript functions before saveKits function
pattern2 = r'(async function saveKits\(equipoId\))'

replacement2 = r'''function togglePasteArea() {
            const pasteContainer = document.getElementById('paste-area-container');
            const pasteArea = document.getElementById('paste-area');
            if (pasteContainer.style.display === 'none') {
                pasteContainer.style.display = 'block';
                pasteArea.value = '';
                pasteArea.focus();
            } else {
                pasteContainer.style.display = 'none';
            }
        }

        function processPastedData() {
            const pasteArea = document.getElementById('paste-area');
            const pastedData = pasteArea.value.trim();
            
            if (!pastedData) {
                alert('No hay datos para importar');
                return;
            }
            
            const rows = pastedData.split('\n').filter(row => row.trim());
            const serviceType = document.getElementById('kit_service_selector').value;
            
            if (!currentKits[serviceType]) currentKits[serviceType] = [];
            
            let imported = 0;
            rows.forEach(row => {
                const cols = row.split('\t');
                if (cols.length >= 2) {
                    const description = cols[0] ? cols[0].trim() : '';
                    const partNumber = cols[1] ? cols[1].trim() : '';
                    const quantity = cols[2] && !isNaN(parseInt(cols[2])) ? parseInt(cols[2]) : 1;
                    
                    if (description || partNumber) {
                        currentKits[serviceType].push({
                            description: description,
                            part_number: partNumber,
                            quantity: quantity
                        });
                        imported++;
                    }
                }
            });
            
            renderCurrentKit();
            togglePasteArea();
            alert(`Se importaron ${imported} refacciones`);
        }

        \1'''

content = re.sub(pattern2, replacement2, content)

# Write back
with open('templates/equipos.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo actualizado correctamente")
