with open('templates/equipos.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add the field in HTML after tipo_servicio_inicial
old_field = '''                <div class="form-group">
                    <label>Notas</label>
                    <textarea class="form-control" id="notas" rows="3"></textarea>
                </div>'''

new_field = '''                <div class="form-group">
                    <label>Ciclo de Servicio</label>
                    <div class="row">
                        <div class="col-md-6">
                            <select class="form-control" id="tipo_ciclo" onchange="toggleReinicioHoras()">
                                <option value="continuo">Continuar aumentando (8000→10000→12000...)</option>
                                <option value="reinicia">Reiniciar después de cierta cantidad</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" id="reiniciar_en_horas" disabled>
                                <option value="">-</option>
                                <option value="8000">Reiniciar en 8000 Horas</option>
                                <option value="16000">Reiniciar en 16000 Horas</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="form-group">
                    <label>Notas</label>
                    <textarea class="form-control" id="notas" rows="3"></textarea>
                </div>'''

content = content.replace(old_field, new_field)

# Add toggleReinicioHoras function
toggle_func = '''
        function toggleReinicioHoras() {
            const tipoCiclo = document.getElementById('tipo_ciclo').value;
            const reinicioSelect = document.getElementById('reiniciar_en_horas');
            if (tipoCiclo === 'reinicia') {
                reinicioSelect.disabled = false;
                if (!reinicioSelect.value) reinicioSelect.value = '8000';
            } else {
                reinicioSelect.disabled = true;
                reinicioSelect.value = '';
            }
        }

        function toggleClienteRequirement() {'''

content = content.replace('        function toggleClienteRequirement() {', toggle_func)

# Update abrirModalNuevo to reset these fields
content = content.replace(
    "document.getElementById('tipo_servicio_inicial').value = '2000 Horas';",
    "document.getElementById('tipo_servicio_inicial').value = '2000 Horas';\n            document.getElementById('tipo_ciclo').value = 'continuo';\n            document.getElementById('reiniciar_en_horas').value = '';\n            toggleReinicioHoras();"
)

# Update editarEquipo to load these fields
content = content.replace(
    "document.getElementById('tipo_servicio_inicial').value = equipo.tipo_servicio_inicial || '2000 Horas';",
    '''document.getElementById('tipo_servicio_inicial').value = equipo.tipo_servicio_inicial || '2000 Horas';
                if (equipo.reiniciar_en_horas) {
                    document.getElementById('tipo_ciclo').value = 'reinicia';
                    document.getElementById('reiniciar_en_horas').value = equipo.reiniciar_en_horas;
                } else {
                    document.getElementById('tipo_ciclo').value = 'continuo';
                    document.getElementById('reiniciar_en_horas').value = '';
                }
                toggleReinicioHoras();'''
)

# Update guardarEquipo to send this field
content = content.replace(
    "tipo_servicio_inicial: document.getElementById('tipo_servicio_inicial').value,",
    '''tipo_servicio_inicial: document.getElementById('tipo_servicio_inicial').value,
                    reiniciar_en_horas: document.getElementById('reiniciar_en_horas').value || null,'''
)

with open('templates/equipos.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("UI actualizada correctamente")
