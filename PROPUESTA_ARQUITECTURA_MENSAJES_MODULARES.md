# 📋 PROPUESTA DE ARQUITECTURA: MENSAJES Y FIRMAS DINÁMICAS POR MÓDULO CRM

## 🎯 OBJETIVO
Implementar un sistema donde cada módulo CRM (Ventas, Finanzas, Compras, Servicios) tenga sus propios templates de mensaje y firma, con capacidad de personalización por trato, manteniendo compatibilidad con el sistema actual.

---

## 📊 ANÁLISIS DE LA SITUACIÓN ACTUAL

### Estado Actual:
- **Campos en `crm_deals`:**
  - `firma_vendedor` (TEXT) - Firma genérica
  - `mensaje_envio` (TEXT) - Mensaje genérico
  - `email` (TEXT) - Email del cliente

- **Problemas identificados:**
  1. Los campos `firma_vendedor` y `mensaje_envio` son genéricos, no están asociados a un módulo
  2. Cuando un trato pasa de Ventas a Finanzas, se sigue usando el mensaje de Ventas
  3. No hay templates por defecto por módulo
  4. Los correos pueden mezclarse si el filtrado no es estricto por `deal_id`

### Mapeo de Puestos → Módulos:
```python
PUESTO_TO_MODULE = {
    'Vendedor': 'ventas',
    'Gerente de Ventas': 'ventas',
    'Cotizador': 'cotizacion',
    'Contador': 'finanzas',
    'Compras': 'compras',
    'Gerente de Servicios Técnicos': 'servicios',
    'Director': 'direccion',
    'Administrador': 'administracion'
}
```

---

## 🏗️ ARQUITECTURA PROPUESTA

### 1️⃣ **TABLA DE TEMPLATES POR MÓDULO** (Nueva)

**Tabla: `email_templates`**
```sql
CREATE TABLE email_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module TEXT NOT NULL,  -- 'ventas', 'finanzas', 'compras', 'servicios'
    template_type TEXT NOT NULL,  -- 'mensaje' o 'firma'
    default_content TEXT NOT NULL,  -- Contenido por defecto del template
    description TEXT,  -- Descripción del template
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Propósito:**
- Almacenar templates por defecto para cada módulo
- Un template de mensaje y uno de firma por módulo
- Permite actualizar templates sin afectar mensajes ya guardados

**Ejemplos de contenido:**
- **Ventas (mensaje):** "Hola, buen día. Adjunto encontrará la cotización solicitada..."
- **Finanzas (mensaje):** "Estimado cliente. Adjunto encontrará la factura correspondiente..."
- **Compras (mensaje):** "Buen día. Adjunto encontrará la orden de compra..."
- **Servicios (mensaje):** "Estimado cliente. Adjunto encontrará el reporte de servicio..."

---

### 2️⃣ **TABLA DE MENSAJES PERSONALIZADOS POR TRATO + MÓDULO** (Nueva)

**Tabla: `deal_email_messages`**
```sql
CREATE TABLE deal_email_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id INTEGER NOT NULL,
    module TEXT NOT NULL,  -- 'ventas', 'finanzas', 'compras', 'servicios'
    mensaje TEXT,  -- Mensaje personalizado (NULL = usar template)
    firma TEXT,  -- Firma personalizada (NULL = usar template)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deal_id) REFERENCES crm_deals (id) ON DELETE CASCADE,
    UNIQUE(deal_id, module)  -- Un solo registro por trato + módulo
)
```

**Propósito:**
- Almacenar mensajes y firmas personalizados por trato y módulo
- Si un trato tiene mensaje personalizado en Ventas, se usa ese
- Si no tiene personalización, se usa el template del módulo
- Permite que el mismo trato tenga diferentes mensajes según el módulo desde el cual se envía

**Flujo de datos:**
```
Usuario abre trato en módulo "Finanzas"
  ↓
Sistema busca en deal_email_messages: deal_id=123, module='finanzas'
  ↓
Si existe → Usar mensaje/firma personalizados
Si NO existe → Usar template de email_templates (module='finanzas')
  ↓
Usuario puede editar y guardar → Se crea/actualiza registro en deal_email_messages
```

---

### 3️⃣ **MIGRACIÓN DE DATOS EXISTENTES**

**Estrategia de compatibilidad hacia atrás:**

1. **Crear templates por defecto** para cada módulo basados en los valores actuales
2. **Migrar datos existentes:**
   - Los `firma_vendedor` y `mensaje_envio` actuales en `crm_deals` se migran a `deal_email_messages` con `module='ventas'`
   - Esto mantiene el comportamiento actual para Ventas
3. **Mantener campos legacy** en `crm_deals` por un tiempo (deprecación gradual):
   - `firma_vendedor` → Se mantiene para compatibilidad
   - `mensaje_envio` → Se mantiene para compatibilidad
   - Se lee primero `deal_email_messages`, si no existe, se usa el campo legacy

**Script de migración:**
```python
# Pseudocódigo
def migrate_existing_messages():
    # 1. Crear templates por defecto
    create_default_templates()
    
    # 2. Migrar mensajes existentes a deal_email_messages
    deals = get_all_deals_with_messages()
    for deal in deals:
        if deal.get('firma_vendedor') or deal.get('mensaje_envio'):
            create_deal_email_message(
                deal_id=deal['id'],
                module='ventas',  # Asumir que los existentes son de Ventas
                mensaje=deal.get('mensaje_envio'),
                firma=deal.get('firma_vendedor')
            )
```

---

### 4️⃣ **LÓGICA DE OBTENCIÓN DE MENSAJE/FIRMA**

**Función: `get_deal_email_content(deal_id, module, content_type='mensaje')`**

**Algoritmo:**
```
1. Buscar en deal_email_messages:
   SELECT mensaje/firma FROM deal_email_messages 
   WHERE deal_id = ? AND module = ?
   
2. Si existe y no es NULL:
   → Retornar contenido personalizado
   
3. Si NO existe o es NULL:
   → Buscar template por defecto:
   SELECT default_content FROM email_templates 
   WHERE module = ? AND template_type = ? AND is_active = 1
   
4. Si template existe:
   → Retornar template
   
5. Si NO existe template:
   → Retornar contenido legacy de crm_deals (compatibilidad)
   → O retornar mensaje genérico por defecto
```

**Ejemplo de uso:**
```python
# Usuario en módulo Finanzas abre trato #123
mensaje = get_deal_email_content(deal_id=123, module='finanzas', content_type='mensaje')
firma = get_deal_email_content(deal_id=123, module='finanzas', content_type='firma')

# Si el trato tiene mensaje personalizado en Finanzas → usa ese
# Si NO tiene → usa template de Finanzas
# Si NO hay template → usa mensaje genérico
```

---

### 5️⃣ **FILTRADO ESTRICTO DE CORREOS POR TRATO**

**Problema actual:**
- `get_deal_emails(deal_id)` ya filtra por `deal_id`, pero puede haber problemas si:
  - Se filtran correos por `cliente_id` en algún lugar
  - Se mezclan correos de diferentes tratos del mismo cliente

**Solución:**
- **NUNCA filtrar solo por `cliente_id`** en el historial de correos
- **SIEMPRE filtrar por `deal_id`** primero
- Opcionalmente, permitir filtro adicional por `module` o `tipo` de documento

**Función mejorada: `get_deal_emails(deal_id, module=None, tipo_documento=None)`**

```python
def get_deal_emails(deal_id, module=None, tipo_documento=None):
    """
    Obtener correos de un trato específico.
    
    REGLA OBLIGATORIA: SIEMPRE filtrar por deal_id primero.
    Los filtros adicionales (module, tipo_documento) son opcionales.
    """
    query = """
        SELECT * FROM email_history 
        WHERE deal_id = ?  -- FILTRO OBLIGATORIO
    """
    params = [deal_id]
    
    # Filtros opcionales (solo si se proporcionan)
    if module:
        query += " AND module = ?"
        params.append(module)
    
    if tipo_documento:
        query += " AND tipo_documento = ?"
        params.append(tipo_documento)
    
    query += " ORDER BY created_at DESC"
    
    return execute_query(query, params)
```

**Verificación adicional:**
- En el frontend, verificar que todos los correos mostrados tengan `deal_id` correcto
- Logs de advertencia si se detectan correos con `deal_id` incorrecto

---

### 6️⃣ **IDENTIFICACIÓN DEL MÓDULO ACTUAL**

**Función: `get_current_module(puesto)`**

```python
def get_current_module(puesto):
    """Mapear puesto del usuario al módulo CRM correspondiente"""
    PUESTO_TO_MODULE = {
        'Vendedor': 'ventas',
        'Gerente de Ventas': 'ventas',
        'Cotizador': 'cotizacion',
        'Contador': 'finanzas',
        'Compras': 'compras',
        'Gerente de Servicios Técnicos': 'servicios',
        'Director': 'direccion',
        'Administrador': 'administracion'
    }
    return PUESTO_TO_MODULE.get(puesto, 'ventas')  # Default: ventas
```

**Uso en endpoints:**
```python
@app.route("/admin/crm/editar/<int:id>")
def admin_crm_editar(id):
    puesto = session.get('puesto')
    current_module = get_current_module(puesto)
    
    # Obtener mensaje/firma para este módulo
    mensaje = get_deal_email_content(id, current_module, 'mensaje')
    firma = get_deal_email_content(id, current_module, 'firma')
    
    # Pasar al template
    return render_template(..., mensaje=mensaje, firma=firma, module=current_module)
```

---

### 7️⃣ **ENVÍO INTELIGENTE SEGÚN CONTEXTO**

**Función: `send_email_by_context(deal_id, documento_tipo, documento_id)`**

**Algoritmo:**
```
1. Determinar módulo desde el puesto del usuario actual
2. Obtener mensaje y firma para ese módulo (usar get_deal_email_content)
3. Determinar tipo de documento:
   - 'cotizacion' → Adjuntar PDF de cotización
   - 'factura' → Adjuntar PDF de factura
   - 'pi' → Adjuntar PDF de PI
   - 'orden_compra' → Adjuntar PDF de orden de compra
4. Enviar email con:
   - Mensaje del módulo correcto
   - Firma del módulo correcto
   - PDF del documento correspondiente
5. Guardar en email_history con:
   - deal_id (obligatorio)
   - module (opcional, para filtrado)
   - tipo_documento (opcional, para filtrado)
```

**Ejemplo:**
```python
# Usuario Contador envía factura
send_email_by_context(
    deal_id=123,
    documento_tipo='factura',
    documento_id=456
)
# → Usa mensaje/firma de módulo 'finanzas'
# → Adjunta PDF de factura
# → Guarda en email_history con module='finanzas', tipo_documento='factura'
```

---

## 📝 RESUMEN DE CAMBIOS NECESARIOS

### Backend:

1. **Nuevas tablas:**
   - `email_templates` (templates por módulo)
   - `deal_email_messages` (mensajes personalizados por trato + módulo)

2. **Nuevas funciones:**
   - `get_current_module(puesto)` - Mapear puesto a módulo
   - `get_deal_email_content(deal_id, module, content_type)` - Obtener mensaje/firma
   - `create_or_update_deal_email_message(deal_id, module, mensaje, firma)` - Guardar personalización
   - `get_email_template(module, template_type)` - Obtener template por defecto
   - `migrate_existing_messages()` - Migrar datos existentes

3. **Funciones modificadas:**
   - `get_deal_emails(deal_id, module=None)` - Agregar filtro opcional por módulo
   - `api_crm_deal_etapa` - Usar mensaje/firma del módulo correcto
   - `admin_crm_editar` - Cargar mensaje/firma del módulo actual
   - `admin_crm_nuevo` - Cargar template del módulo actual

4. **Migración de datos:**
   - Script para crear templates por defecto
   - Script para migrar `firma_vendedor` y `mensaje_envio` existentes

### Frontend:

1. **Templates modificados:**
   - `admin_crm_form.html` - Cargar mensaje/firma del módulo actual
   - `admin_crm_view.html` - Mostrar mensaje/firma del módulo actual

2. **JavaScript:**
   - Función para guardar mensaje/firma con `module` actual
   - Función para cargar template si no hay personalización

---

## ✅ VENTAJAS DE ESTA ARQUITECTURA

1. **Modularidad:** Cada módulo tiene sus propios templates
2. **Flexibilidad:** Permite personalización por trato sin perder templates
3. **Compatibilidad:** Mantiene funcionamiento actual de Ventas
4. **Escalabilidad:** Fácil agregar nuevos módulos
5. **Mantenibilidad:** Templates centralizados, fáciles de actualizar
6. **Filtrado estricto:** Garantiza que correos no se mezclen entre tratos

---

## 🔄 FLUJO COMPLETO DE EJEMPLO

### Escenario: Trato pasa de Ventas → Finanzas

**1. Usuario Vendedor (Ventas):**
   - Abre trato #123
   - Sistema carga: `get_deal_email_content(123, 'ventas', 'mensaje')`
   - Si no existe personalización → usa template de Ventas
   - Usuario edita y guarda → Se crea registro en `deal_email_messages(deal_id=123, module='ventas', ...)`
   - Envía cotización → Usa mensaje/firma de Ventas

**2. Trato se mueve a Finanzas:**
   - Usuario Contador abre trato #123
   - Sistema carga: `get_deal_email_content(123, 'finanzas', 'mensaje')`
   - NO existe personalización para Finanzas → usa template de Finanzas
   - Usuario ve mensaje diferente (de Finanzas, no de Ventas)
   - Usuario puede editar y guardar → Se crea registro en `deal_email_messages(deal_id=123, module='finanzas', ...)`
   - Envía factura → Usa mensaje/firma de Finanzas

**3. Historial de correos:**
   - Muestra SOLO correos con `deal_id=123`
   - Opcionalmente filtra por `module='finanzas'` si se desea
   - NUNCA muestra correos de otros tratos, aunque sean del mismo cliente

---

## 🎯 PRÓXIMOS PASOS

1. ✅ **Aprobación de arquitectura** (este documento)
2. ⏳ **Implementación de tablas** (database.py)
3. ⏳ **Implementación de funciones** (database.py, app.py)
4. ⏳ **Migración de datos** (script de migración)
5. ⏳ **Modificación de endpoints** (app.py)
6. ⏳ **Modificación de templates** (admin_crm_form.html, admin_crm_view.html)
7. ⏳ **Pruebas** (Ventas → Finanzas → Compras)

---

**¿Proceder con la implementación?**

