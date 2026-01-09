import re

# Read the file
with open(r"c:\Users\INAIR 005\OneDrive\Escritorio\PYTHON\p9\p6\inair_reportes\templates\formulario.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix Contacto - wrap in input-group with toggle (READ-ONLY toggle)
contacto_old = r'(<div class="col-12 col-md-6">[\s\S]*?<label class="form-label">Contacto</label>[\s\S]*?)<input class="form-control" name="contacto" id="contacto">([\s\S]*?</div>)'
contacto_new = r'''\1<div class="input-group">
              <input class="form-control" name="contacto" id="contacto" readonly>
              <button class="btn btn-outline-secondary" type="button" id="toggle_contacto" onClick="toggleReadOnly('contacto')" title="Editar">
                🔒
              </button>
            </div>\2'''
content = re.sub(contacto_old, contacto_new, content, count=1)

# 2. Fix Teléfono
telefono_old = r'(<div class="col-12 col-md-4">[\s\S]*?<label class="form-label">Teléfono</label>[\s\S]*?)<input class="form-control" name="telefono" id="telefono">([\s\S]*?</div>)'
telefono_new = r'''\1<div class="input-group">
              <input class="form-control" name="telefono" id="telefono" readonly>
              <button class="btn btn-outline-secondary" type="button" id="toggle_telefono" onClick="toggleReadOnly('telefono')" title="Editar">
                🔒
              </button>
            </div>\2'''
content = re.sub(telefono_old, telefono_new, content, count=1)

# 3. Fix Email
email_old = r'(<div class="col-12 col-md-8">[\s\S]*?<label class="form-label">Email</label>[\s\S]*?)<input class="form-control" name="email" id="email">([\s\S]*?</div>)'
email_new = r'''\1<div class="input-group">
              <input class="form-control" name="email" id="email" readonly>
              <button class="btn btn-outline-secondary" type="button" id="toggle_email" onClick="toggleReadOnly('email')" title="Editar">
                🔒
              </button>
            </div>\2'''
content = re.sub(email_old, email_new, content, count=1)

# 4. Fix Dirección
direccion_old = r'(<div class="col-12">[\s\S]*?<label class="form-label">Dirección</label>[\s\S]*?)<input class="form-control" name="direccion" id="direccion">([\s\S]*?</div>)'
direccion_new = r'''\1<div class="input-group">
              <input class="form-control" name="direccion" id="direccion" readonly>
              <button class="btn btn-outline-secondary" type="button" id="toggle_direccion" onClick="toggleReadOnly('direccion')" title="Editar">
                🔒
              </button>
            </div>\2'''
content = re.sub(direccion_old, direccion_new, content, count=1)

# Write modified content back
with open(r"c:\Users\INAIR 005\OneDrive\Escritorio\PYTHON\p9\p6\inair_reportes\templates\formulario.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Archivo HTML modificado exitosamente - Agregados toggles a Contacto, Teléfono, Email y Dirección")
