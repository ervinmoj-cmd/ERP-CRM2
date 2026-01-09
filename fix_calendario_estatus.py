with open('templates/calendario_mantenimiento.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add header
content = content.replace(
    '<th>Frecuencia</th>\n                                    </tr>',
    '<th>Frecuencia</th>\n                                        <th>Estatus</th>\n                                    </tr>'
)

# Add status cell
old_row_end = '''</td>
                            <td><span class="badge bg-secondary">${e.frecuencia_meses} meses</span></td>
                        </tr>'''

new_row_end = '''</td>
                            <td><span class="badge bg-secondary">${e.frecuencia_meses} meses</span></td>
                            <td>
                                ${e.estatus_servicio === 'REALIZADO' ? 
                                    (e.folio_servicio ? 
                                        `<a href="/ver_reporte/${e.folio_servicio}" class="badge bg-success text-decoration-none" target="_blank">✓ REALIZADO</a>` : 
                                        `<span class="badge bg-success">✓ REALIZADO</span>`) : 
                                    `<span class="badge bg-warning text-dark">⏳ PENDIENTE</span>`
                                }
                            </td>
                        </tr>'''

content = content.replace(old_row_end, new_row_end)

with open('templates/calendario_mantenimiento.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Calendario actualizado con columna de estatus")
