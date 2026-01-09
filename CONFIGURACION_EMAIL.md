# 📧 Configuración del Envío Automático de Cotizaciones

## ✅ Características Implementadas

### 1. **Link Directo al PDF**
- Cuando se vincula una cotización a un trato, ahora aparece con el icono 📄
- Al hacer clic, se abre la **vista previa del PDF** (no el formulario de edición)
- El vendedor puede revisar la cotización antes de enviarla

### 2. **Campos Personalizados en el Trato**
Cuando un trato tiene cotizaciones vinculadas, aparece una sección especial:

**📧 Preparar Envío de Cotización**
- **Email del Cliente**: Se puede capturar directamente en el trato
- **✍️ Firma del Vendedor**: Cómo aparecerá el nombre del vendedor en el email
  - Ejemplo: "Ing. Juan Pérez - Gerente de Ventas"
- **💬 Mensaje Personalizado**: Texto adicional que se incluirá en el email
  - Ejemplo: "Quedamos atentos a sus comentarios y disponibles para cualquier aclaración"

### 3. **Flujo Automatizado**

```
COTIZADOR                          VENDEDOR                         CLIENTE
   │                                  │                                 │
   ├─ Genera cotización               │                                 │
   ├─ Vincula a trato                 │                                 │
   ├─ Mueve a "Cotizado" ────────────►│                                │
   │                           (Se mueve automáticamente)              │
   │                           a "Cotización Lista para Enviar"        │
   │                                  │                                 │
   │                           ✍️ Agrega firma y mensaje               │
   │                           📝 Verifica email del cliente           │
   │                           📄 Ve vista previa del PDF              │
   │                                  │                                 │
   │                           Mueve a "Cotización Enviada" ───────────► 📧 Recibe PDF
   │                           (Sistema envía email automático)           con mensaje
   │                                  │                                   personalizado
```

---

## 🔧 Configuración Requerida

### Paso 1: Configurar Credenciales de Email

Edita el archivo `email_sender.py` (líneas 10-14):

```python
# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "pedidos@inair.com.mx"     # ← CAMBIAR por el email real
SMTP_PASSWORD = "tu_contraseña_aqui"   # ← CAMBIAR por la contraseña
FROM_EMAIL = "pedidos@inair.com.mx"
FROM_NAME = "INGENIERÍA EN AIRE"
```

---

### Paso 2: Obtener Contraseña de Aplicación (Gmail)

Si usas Gmail, **NO** uses tu contraseña normal. Necesitas una **Contraseña de Aplicación**:

1. **Ve a tu cuenta de Gmail**: https://myaccount.google.com
2. **Activa la verificación en 2 pasos** (si no la tienes)
3. **Genera una Contraseña de Aplicación**:
   - Ve a: https://myaccount.google.com/apppasswords
   - Selecciona "Correo" como aplicación
   - Selecciona "Windows" como dispositivo
   - Haz clic en "Generar"
   - Copia la contraseña de 16 caracteres (ej: `abcd efgh ijkl mnop`)
4. **Pégala en `email_sender.py`**:
   ```python
   SMTP_PASSWORD = "abcd efgh ijkl mnop"
   ```

---

### Paso 3: Configurar Emails de los Vendedores

Para que el email se envíe **desde el correo del vendedor**:

1. Ve a **Usuarios** en el panel de administración
2. Edita cada vendedor
3. Agrega su **email corporativo** en el campo correspondiente
4. Guarda los cambios

**Ejemplo:**
- Vendedor: Juan Pérez
- Email: juan.perez@inair.com.mx

Cuando Juan envíe una cotización, el cliente recibirá el email **desde** `juan.perez@inair.com.mx` y las respuestas irán a ese correo.

---

## 🎯 Cómo Usar el Sistema

### Para el COTIZADOR:

1. Crear la cotización normalmente
2. Vincularla al trato correspondiente
3. Mover el trato a **"Cotizado"**
4. ✅ El sistema automáticamente lo moverá al CRM del vendedor

### Para el VENDEDOR:

1. Abrir el trato (que ya está en "Cotización Lista para Enviar")
2. **Verificar/agregar**:
   - ✉️ Email del cliente
   - ✍️ Tu firma (ej: "Ing. Juan Pérez - Ventas")
   - 💬 Mensaje personalizado (opcional)
3. **Guardar el trato**
4. Hacer clic en **📄 [Folio]** para ver vista previa del PDF
5. Mover el trato a **"Cotización Enviada"**
6. ✅ El sistema envía el email automáticamente

---

## 📧 Ejemplo de Email que Recibe el Cliente

```
De: Juan Pérez <juan.perez@inair.com.mx>
Para: cliente@empresa.com
Asunto: Cotización T-00008 - MONTECITOS MANUFACTURING

Cotización T-00008
─────────────────────────────────

Estimado(a) Audiel López,

Adjunto encontrará la cotización T-00008 por un monto de USD $25,879.00

Vigencia: 30 días naturales

┌──────────────────────────────────────────────┐
│ Quedamos atentos a sus comentarios y         │
│ disponibles para cualquier aclaración        │
└──────────────────────────────────────────────┘

Quedamos a sus órdenes para cualquier duda o aclaración.

Saludos cordiales,
Ing. Juan Pérez - Gerente de Ventas
INGENIERÍA EN AIRE
Tel: (664) 250-0022
juan.perez@inair.com.mx
www.inair.com.mx

📎 Adjunto: Cotizacion_T-00008.pdf
```

---

## ⚠️ Notas Importantes

1. **Sin email configurado**: El sistema mostrará un error en la consola pero NO detendrá el flujo del CRM
2. **Sin email del cliente**: El email no se enviará (se muestra aviso en consola)
3. **Sin cotización vinculada**: No se envía nada
4. **Logs**: Revisa la consola del servidor para confirmar envíos:
   ```
   ✅ PDF de cotización T-00008 enviado a cliente@email.com desde vendedor@inair.com.mx
   ```

---

## 🔒 Seguridad

- Las contraseñas de aplicación son **más seguras** que usar tu contraseña real
- Puedes revocar el acceso en cualquier momento desde tu cuenta de Google
- El sistema usa **TLS/STARTTLS** para encriptar la conexión

---

## 🆘 Solución de Problemas

### Error: "535 Authentication failed"
**Solución**: Verifica que la contraseña de aplicación sea correcta. Genera una nueva si es necesario.

### Error: "535 Username and Password not accepted"
**Solución**: Asegúrate de que la verificación en 2 pasos esté activada en Gmail.

### El email no se envía
**Solución**: 
1. Verifica que el trato tenga un email válido del cliente
2. Revisa la consola del servidor para ver el error específico
3. Verifica que el vendedor tenga email configurado en su perfil

### El cliente no recibe el email
**Solución**:
1. Revisa la carpeta de SPAM del cliente
2. Pide al cliente que agregue `@inair.com.mx` a sus contactos seguros

---

## 📊 Ventajas del Sistema

| Antes | Ahora |
|-------|-------|
| Vendedor descarga PDF | Solo mueve el trato |
| Vendedor envía email manualmente | Automático al mover trato |
| Sin personalización | Firma y mensaje personalizados |
| Sin registro | Todo queda en el CRM |
| Posible error u olvido | 100% confiable |
| Cliente espera | Recibe al instante |

---

## 🎉 ¡Listo!

Una vez configurado el email, el sistema funcionará completamente automático. Los vendedores solo necesitan:

1. ✅ Agregar email del cliente
2. ✅ Personalizar firma y mensaje
3. ✅ Mover el trato

¡Y el cliente recibe su cotización profesional al instante!




