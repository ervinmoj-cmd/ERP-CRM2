import re

# Read the file
with open(r"c:\Users\INAIR 005\OneDrive\Escritorio\PYTHON\p9\p6\inair_reportes\templates\formulario.html", "r", encoding="utf-8") as f:
    content = f.read()

# Pattern to find and replace "Tipo de equipo" field
tipo_equipo_old = r'(<div class="col-12 col-md-6">[\s\S]*?<label class="form-label">Tipo de equipo</label>[\s\S]*?)<select class="form-select" name="tipo_equipo" id="tipo_equipo">([\s\S]*?)</select>([\s\S]*?</div>)'

tipo_equipo_new = r'''\1<div class="input-group">
              <select class="form-select" id="tipo_equipo_select">\2</select>
              <input class="form-control" name="tipo_equipo" id="tipo_equipo_input" style="display:none;" placeholder="Escriba el tipo de equipo" disabled>
              <button class="btn btn-outline-secondary" type="button" id="toggle_tipo_equipo" title="Entrada Manual">
                ✏️
              </button>
            </div>\3'''

content = re.sub(tipo_equipo_old, tipo_equipo_new, content, count=1)

# Pattern to find and replace "Modelo" field
modelo_old = r'(<div class="col-12 col-md-3">[\s\S]*?<label class="form-label">Modelo</label>[\s\S]*?)<select class="form-select" name="modelo" id="modelo">([\s\S]*?)</select>([\s\S]*?</div>)'

modelo_new = r'''\1<div class="input-group">
              <select class="form-select" id="modelo_select">\2</select>
              <input class="form-control" name="modelo" id="modelo_input" style="display:none;" placeholder="Escriba el modelo" disabled>
              <button class="btn btn-outline-secondary" type="button" id="toggle_modelo" title="Entrada Manual">
                ✏️
              </button>
            </div>\3'''

content = re.sub(modelo_old, modelo_new, content, count=1)

# Write modified content
with open(r"c:\Users\INAIR 005\OneDrive\Escritorio\PYTHON\p9\p6\inair_reportes\templates\formulario.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Archivo modificado exitosamente")
