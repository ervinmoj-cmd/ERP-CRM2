with open('templates/equipos.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add 6000 Horas in kit selector
content = content.replace(
    '<option value="8000 Horas">8000 Horas</option>',
    '<option value="6000 Horas">6000 Horas</option>\n                                <option value="8000 Horas">8000 Horas</option>'
)

# Add tipo_servicio_inicial field
notas_field = '''<div class="form-group">
                    <label>Notas</label>
                    <textarea class="form-control" id="notas" rows="3"></textarea>
                </div>'''

new_fields = '''<div class="form-group">
                    <label>Tipo de Servicio Inicial *</label>
                    <select class="form-control" id="tipo_servicio_inicial">
                        <option value="2000 Horas">2000 Horas</option>
                        <option value="4000 Horas">4000 Horas</option>
                        <option value="6000 Horas">6000 Horas</option>
                        <option value="8000 Horas">8000 Horas</option>
                        <option value="16000 Horas">16000 Horas</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Notas</label>
                    <textarea class="form-control" id="notas" rows="3"></textarea>
                </div>'''

content = content.replace(notas_field, new_fields)

# Update JavaScript - add tipo_servicioinicial to abrirModalNuevo
content = content.replace(
    "document.getElementById('clasificacion').value = 'General';",
    "document.getElementById('clasificacion').value = 'General';\n            document.getElementById('tipo_servicio_inicial').value = '2000 Horas';"
)

# Update JavaScript - editarEquipo
content = content.replace(
    "document.getElementById('clasificacion').value = equipo.clasificacion || 'General';",
    "document.getElementById('clasificacion').value = equipo.clasificacion || 'General';\n                document.getElementById('tipo_servicio_inicial').value = equipo.tipo_servicio_inicial || '2000 Horas';"
)

# Update JavaScript - guardarEquipo
content = content.replace(
    "notas: document.getElementById('notas').value,",
    "notas: document.getElementById('notas').value,\n                    tipo_servicio_inicial: document.getElementById('tipo_servicio_inicial').value,"
)

with open('templates/equipos.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo actualizado correctamente")
