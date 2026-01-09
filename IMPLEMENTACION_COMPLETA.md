# ✅ IMPLEMENTACIÓN COMPLETA: MENSAJES Y FIRMAS DINÁMICAS POR MÓDULO

## 📋 RESUMEN DE CAMBIOS

### ✅ Backend (Completado)

1. **Nuevas tablas creadas:**
   - `email_templates`: Templates por defecto por módulo
   - `deal_email_messages`: Mensajes personalizados por trato + módulo
   - Columnas `module` y `tipo_documento` agregadas a `email_history`

2. **Nuevas funciones en `database.py`:**
   - `get_email_template(module, template_type)`
   - `get_all_email_templates(module=None)`
   - `create_or_update_email_template(module, template_type, default_content, description)`
   - `get_deal_email_message(deal_id, module)`
   - `create_or_update_deal_email_message(deal_id, module, mensaje, firma)`
   - `delete_deal_email_message(deal_id, module)`
   - `get_deal_email_content(deal_id, module, content_type='mensaje')` - **Función principal**

3. **Nueva función helper en `app.py`:**
   - `get_current_module(puesto)` - Mapea puesto a módulo

4. **Endpoints modificados:**
   - `admin_crm_nuevo`: Carga templates del módulo actual
   - `admin_crm_editar`: Carga mensaje/firma del módulo actual
   - `admin_crm_view`: Carga mensaje/firma del módulo actual
   - `api_crm_deal_etapa`: Usa mensaje/firma del módulo correcto al enviar
   - **Nuevo:** `api_save_deal_email_content`: Guarda mensaje/firma personalizado

5. **Migración automática:**
   - Los mensajes existentes en `crm_deals` se migran automáticamente a `deal_email_messages` con `module='ventas'`
   - Templates por defecto se crean automáticamente para todos los módulos

### ⏳ Frontend (Pendiente)

Los templates frontend necesitan ser modificados para:
1. Mostrar el mensaje/firma del módulo actual
2. Permitir editar y guardar mensaje/firma
3. Llamar al endpoint `api_save_deal_email_content` al guardar

**Archivos a modificar:**
- `templates/admin_crm_form.html`
- `templates/admin_crm_view.html`

---

## 🔄 FLUJO DE FUNCIONAMIENTO

### 1. Usuario abre trato en módulo "Ventas":
```
GET /admin/crm/editar/123
  ↓
Sistema detecta puesto = "Vendedor"
  ↓
get_current_module("Vendedor") → "ventas"
  ↓
get_deal_email_content(123, "ventas", "mensaje")
  ↓
Priority 1: Busca en deal_email_messages(deal_id=123, module='ventas')
  ↓
Si existe → Usa mensaje personalizado
Si NO existe → Priority 2: Usa template de email_templates(module='ventas')
  ↓
Template renderizado con mensaje/firma correctos
```

### 2. Usuario edita y guarda mensaje:
```
POST /api/crm/deal/123/save-email-content
{
  "mensaje": "Mensaje personalizado...",
  "firma": "Firma personalizada..."
}
  ↓
Sistema detecta puesto = "Vendedor" → module = "ventas"
  ↓
create_or_update_deal_email_message(123, "ventas", mensaje, firma)
  ↓
Se guarda en deal_email_messages(deal_id=123, module='ventas')
```

### 3. Trato pasa a módulo "Finanzas":
```
GET /admin/crm/editar/123 (usuario Contador)
  ↓
Sistema detecta puesto = "Contador"
  ↓
get_current_module("Contador") → "finanzas"
  ↓
get_deal_email_content(123, "finanzas", "mensaje")
  ↓
Priority 1: Busca en deal_email_messages(deal_id=123, module='finanzas')
  ↓
NO existe (porque solo se personalizó en Ventas)
  ↓
Priority 2: Usa template de email_templates(module='finanzas')
  ↓
Template renderizado con mensaje/firma de Finanzas (diferente a Ventas)
```

### 4. Envío automático de email:
```
POST /api/crm/deal/123/etapa (mover a "Cotización enviada")
  ↓
Sistema detecta puesto = "Vendedor" → module = "ventas"
  ↓
get_deal_email_content(123, "ventas", "mensaje")
get_deal_email_content(123, "ventas", "firma")
  ↓
Usa mensaje/firma de Ventas
  ↓
Envía email con PDF de cotización
```

---

## 📊 ESTRUCTURA DE DATOS

### Tabla: `email_templates`
```sql
id | module    | template_type | default_content              | description
1  | ventas    | mensaje       | "Hola, buen día..."         | Mensaje por defecto para Ventas
2  | ventas    | firma         | "Saludos cordiales,"        | Firma por defecto para Ventas
3  | finanzas  | mensaje       | "Estimado cliente..."       | Mensaje por defecto para Finanzas
4  | finanzas  | firma         | "Saludos cordiales,\n..."    | Firma por defecto para Finanzas
```

### Tabla: `deal_email_messages`
```sql
id | deal_id | module   | mensaje              | firma
1  | 123     | ventas   | "Mensaje personal..." | "Firma personal..."
2  | 123     | finanzas | NULL                  | NULL
```

**Interpretación:**
- Trato #123 tiene mensaje personalizado en Ventas
- Trato #123 NO tiene mensaje personalizado en Finanzas (usa template)

---

## ✅ COMPATIBILIDAD HACIA ATRÁS

1. **Campos legacy mantenidos:**
   - `crm_deals.firma_vendedor` - Se mantiene (no se elimina)
   - `crm_deals.mensaje_envio` - Se mantiene (no se elimina)

2. **Prioridad de lectura:**
   - Si existe personalización en `deal_email_messages` → usa esa
   - Si NO existe → usa template de `email_templates`
   - Si NO hay template → usa campos legacy de `crm_deals` (solo para module='ventas')
   - Si NO hay nada → usa mensaje genérico por defecto

3. **Migración automática:**
   - Al inicializar la base de datos, los mensajes existentes se migran automáticamente
   - No se pierden datos existentes

---

## 🎯 PRÓXIMOS PASOS (Frontend)

1. Modificar `admin_crm_form.html`:
   - Mostrar `mensaje` y `firma` del módulo actual
   - Agregar botón/acción para guardar cambios
   - Llamar a `api_save_deal_email_content` al guardar

2. Modificar `admin_crm_view.html`:
   - Mostrar `mensaje` y `firma` del módulo actual
   - Permitir edición inline
   - Guardar cambios automáticamente o con botón

3. Agregar indicador visual:
   - Mostrar si el mensaje es personalizado o template
   - Permitir "resetear" a template por defecto

---

## 🧪 PRUEBAS RECOMENDADAS

1. **Prueba de migración:**
   - Verificar que mensajes existentes se migraron correctamente
   - Verificar que templates se crearon para todos los módulos

2. **Prueba de módulos:**
   - Abrir trato en Ventas → ver mensaje de Ventas
   - Abrir mismo trato en Finanzas → ver mensaje de Finanzas (diferente)
   - Personalizar mensaje en Ventas → verificar que se guarda
   - Personalizar mensaje en Finanzas → verificar que es independiente

3. **Prueba de envío:**
   - Enviar cotización desde Ventas → verificar que usa mensaje de Ventas
   - Enviar factura desde Finanzas → verificar que usa mensaje de Finanzas

4. **Prueba de filtrado:**
   - Verificar que historial de correos solo muestra correos del trato actual
   - Verificar que no se mezclan correos de otros tratos

---

## 📝 NOTAS IMPORTANTES

1. **Filtrado estricto:**
   - `get_deal_emails(deal_id)` siempre filtra por `deal_id` primero
   - Nunca filtrar solo por `cliente_id` en el historial

2. **Módulos soportados:**
   - `ventas` (Vendedor, Gerente de Ventas)
   - `finanzas` (Contador)
   - `compras` (Compras)
   - `servicios` (Gerente de Servicios Técnicos)
   - `cotizacion` (Cotizador)
   - `direccion` (Director)
   - `administracion` (Administrador)

3. **Templates por defecto:**
   - Se crean automáticamente al inicializar la base de datos
   - Pueden modificarse desde la base de datos o agregando función de administración

---

**Estado:** ✅ Backend completo, ⏳ Frontend pendiente

