# email_sender.py
import smtplib
import ssl
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import io
from database import get_cotizacion_by_id

def parse_email_list(email_string):
    """
    Parsea una cadena de emails separados por comas o punto y coma.
    Retorna una lista de emails válidos y limpios.
    IMPORTANTE: Preserva TODOS los emails, incluso si hay espacios o caracteres extra.
    """
    if not email_string or not email_string.strip():
        return []
    
    # Reemplazar punto y coma por comas
    email_string = email_string.replace(';', ',')
    
    # Separar por comas y limpiar
    emails = []
    for email in email_string.split(','):
        email = email.strip()
        # Limpiar espacios extra pero preservar el email completo
        email = ' '.join(email.split())  # Normalizar espacios múltiples a uno solo
        if email:
            emails.append(email)
    
    print(f"📧 DEBUG parse_email_list: Input='{email_string}' -> Output={emails}")
    return emails

def validate_email(email):
    """
    Valida que un email tenga un formato básico válido.
    Retorna True si es válido, False si no.
    """
    if not email or not email.strip():
        return False
    
    # Patrón básico de validación de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def validate_and_parse_emails(email_string, field_name="email"):
    """
    Valida y parsea una lista de emails.
    Retorna (emails_validos, emails_invalidos, error_message)
    """
    if not email_string or not email_string.strip():
        return [], [], None
    
    emails = parse_email_list(email_string)
    
    if not emails:
        return [], [], f"No se encontraron emails en el campo {field_name}"
    
    valid_emails = []
    invalid_emails = []
    
    for email in emails:
        if validate_email(email):
            valid_emails.append(email)
        else:
            invalid_emails.append(email)
    
    error_message = None
    if invalid_emails:
        error_message = f"Emails inválidos en {field_name}: {', '.join(invalid_emails)}"
    
    return valid_emails, invalid_emails, error_message

# Safety defaults to avoid NameError in legacy code paths
factura_id = None

# Email configuration - GoDaddy (Configuración SSL)
SMTP_SERVER = "smtpout.secureserver.net"
SMTP_PORT = 465
SMTP_USE_SSL = True  # Usar SSL directo (no STARTTLS)
SMTP_USER = "emoreno@inair.com.mx"
SMTP_PASSWORD = "52E841m16"
FROM_EMAIL = "emoreno@inair.com.mx"
FROM_NAME = "INGENIERÍA EN AIRE"

# Note: PDF generation function has been moved to app.py as generate_cotizacion_pdf_bytes()
# This ensures both web views and emails use the same PDF generation logic

def send_cotizacion_pdf(
    cotizacion_id,
    recipient_email,
    vendedor_email=None,
    vendedor_nombre=None,
    firma_vendedor=None,
    mensaje_personalizado=None,
    smtp_user=None,
    smtp_password=None,
    firma_imagen=None,
    deal_id=None,
    subject=None,  # Asunto personalizado del borrador
    cc=None,  # CC recipients (comma-separated string or list)
):
    """Envía la cotización (PDF) desde la cuenta del vendedor. Nunca busca factura."""

    from database import create_email_record, get_deal_message

    # Obtener cotización; si no existe, detener
    cotizacion = get_cotizacion_by_id(cotizacion_id)
    if not cotizacion:
        raise Exception("Cotización no encontrada")

    # Contexto: mensaje/firma según deal+module
    if deal_id:
        msg_data = get_deal_message(deal_id, "Ventas", "cotizacion")
        if not mensaje_personalizado:
            mensaje_personalizado = msg_data.get("body")
        if not firma_vendedor:
            firma_vendedor = msg_data.get("signature")

    # Generar PDF (misma función que usa la vista web)
    from app import generate_cotizacion_pdf_bytes

    pdf_bytes = generate_cotizacion_pdf_bytes(cotizacion_id)
    if not pdf_bytes:
        raise Exception("Error generando PDF")

    # Credenciales SMTP (priorizar email_smtp del usuario)
    use_smtp_user = smtp_user if smtp_user else SMTP_USER
    use_smtp_password = smtp_password if smtp_password else SMTP_PASSWORD

    sender_email = smtp_user if smtp_user else (vendedor_email if vendedor_email else use_smtp_user)
    sender_name = vendedor_nombre or FROM_NAME

    msg = MIMEMultipart()
    # Codificar correctamente el header "From" para evitar encoding MIME visible
    from email.header import Header
    from email.utils import formataddr
    # Usar formataddr que maneja correctamente caracteres especiales
    msg["From"] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
    
    # Validar y parsear emails de "Para"
    if isinstance(recipient_email, list):
        to_email_list = recipient_email
    else:
        print(f"📧 DEBUG send_cotizacion_pdf: recipient_email recibido = '{recipient_email}' (tipo: {type(recipient_email)})")
        to_email_list, to_invalid, to_error = validate_and_parse_emails(str(recipient_email), "Para")
        print(f"📧 DEBUG send_cotizacion_pdf: to_email_list = {to_email_list}, to_invalid = {to_invalid}, to_error = {to_error}")
        if to_error:
            raise Exception(to_error)
        if not to_email_list:
            raise Exception("No hay emails válidos en el campo 'Para'")
    
    to_emails = ', '.join(to_email_list)
    msg["To"] = to_emails
    print(f"📧 DEBUG send_cotizacion_pdf: msg['To'] = '{to_emails}'")
    
    # Validar y parsear emails de "CC" si se proporciona
    cc_email_list = []
    cc_emails = None
    if cc:
        if isinstance(cc, list):
            cc_email_list = cc
        else:
            cc_email_list, cc_invalid, cc_error = validate_and_parse_emails(str(cc), "CC")
            if cc_error:
                raise Exception(cc_error)
        
        if cc_email_list:
            cc_emails = ', '.join(cc_email_list)
            msg["Cc"] = cc_emails
    
    msg["Reply-To"] = sender_email

    # Asunto (prioridad: subject del borrador > msg_data > default)
    # IMPORTANTE: Agregar token [DEAL-id] al final si no existe
    deal_token = f"[DEAL-{deal_id}]" if deal_id else ""
    
    if subject:
        # Usar asunto del borrador directamente, pero agregar token si no existe
        if deal_token and deal_token not in subject:
            msg["Subject"] = f"{subject} {deal_token}"
        else:
            msg["Subject"] = subject
    else:
        subject_tpl = None
        if deal_id and "msg_data" in locals():
            subject_tpl = msg_data.get("subject")
        if subject_tpl:
            safe_subject = (
                subject_tpl.replace("{folio}", str(cotizacion["folio"]))
                .replace("{cliente}", str(cotizacion["cliente_nombre"]))
            )
            if deal_token and deal_token not in safe_subject:
                safe_subject = f"{safe_subject} {deal_token}"
            msg["Subject"] = safe_subject
        else:
            base_subject = f"Cotización {cotizacion['folio']} - {cotizacion['cliente_nombre']}"
            if deal_token:
                base_subject = f"{base_subject} {deal_token}"
            msg["Subject"] = base_subject

    # Cuerpo
    default_message = (
        "Hola, buen día\n\n"
        "Adjunto encontrará la cotización solicitada.\n\n"
        "Quedamos a sus órdenes para cualquier duda o aclaración."
    )
    mensaje_final = mensaje_personalizado if mensaje_personalizado else default_message
    
    # Convert to clean HTML (escape and convert \n to <br>)
    import html
    mensaje_escaped = html.escape(mensaje_final)
    mensaje_html = mensaje_escaped.replace("\n", "<br>")

    signature_html = "<p>Saludos cordiales,</p>"
    if firma_imagen:
        signature_html += (
            f'<p><img src="data:image/png;base64,{firma_imagen}" alt="Firma" '
            'style="max-width: 100px; max-height: 50px; width: auto; height: auto; display: block; margin: 10px 0;"></p>'
        )
    if firma_vendedor:
        import re
        firma_limpia = re.sub(r'\n\s*\n', '\n', firma_vendedor)  # Remove blank lines
        firma_text_html = firma_limpia.replace('\n', '<br>')
        signature_html += f'<div style="margin-top: 10px; line-height: 1.3;">{firma_text_html}</div></p>'
    else:
        # Generic signature (only if no custom signature)
        signature_html += "<p><b>INGENIERÍA EN AIRE SA DE CV</b><br>"
        signature_html += "Tel: (664) 250-0022<br>"
        signature_html += "ervin.moj@gmail.com<br>"
        signature_html += "www.inair.com.mx</p>"
    
    # Email body - Clean and simple, without amount
    # IMPORTANTE: Agregar token [DEAL-id] discretamente al final del body
    body = "<html>\n"
    body += '<body style="font-family: Arial, sans-serif; padding: 20px;">\n'
    body += f'<h2 style="color: #D20000;">Cotización {cotizacion["folio"]}</h2>\n'
    body += f'<p>Estimado(a) <b>{cotizacion["atencion_a"] or cotizacion["cliente_nombre"]}</b>,</p>\n\n'
    body += '<div style="margin: 20px 0; line-height: 1.6; color: #444;">\n'
    body += f'{mensaje_html}\n'
    body += '</div>\n\n'
    body += f'<p style="margin-top: 20px;"><strong>Vigencia:</strong> {cotizacion["vigencia"]}</p>\n\n'
    body += '<br>\n'
    body += f'{signature_html}\n'
    # Agregar token discretamente al final (también en texto plano)
    if deal_token:
        body += f'<p style="font-size: 0.8em; color: #999; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px;">Ref: {deal_token}</p>\n'
    body += '</body>\n'
    body += '</html>'
    
    # También agregar token al mensaje de texto plano (para búsqueda IMAP)
    if deal_token and deal_token not in mensaje_final:
        mensaje_final = f"{mensaje_final}\n\nRef: {deal_token}"
    msg.attach(MIMEText(body, 'html'))
    
    # Attach PDF
    pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
    pdf_attachment.add_header('Content-Disposition', 'attachment', filename=f'Cotizacion_{cotizacion["folio"]}.pdf')
    msg.attach(pdf_attachment)
    
    # Send email (use vendor's credentials if configured, otherwise use generic)
    try:
        # Connect using SSL or STARTTLS based on configuration
        if SMTP_USE_SSL:
            # SSL connection (port 465)
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        else:
            # STARTTLS connection (port 587)
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
        
        # Login with custom or default credentials
        server.login(use_smtp_user, use_smtp_password)
        
        # Construir lista completa de destinatarios (To + CC)
        # Ya están parseados y validados arriba
        recipients = to_email_list.copy()
        if cc_email_list:
            recipients.extend(cc_email_list)
        
        print(f"📧 DEBUG send_cotizacion_pdf: Lista final de destinatarios (to_addrs): {recipients}")
        print(f"📧 DEBUG send_cotizacion_pdf: Total destinatarios: {len(recipients)} (To: {len(to_email_list)}, CC: {len(cc_email_list)})")
        
        # Enviar a todos los destinatarios
        server.send_message(msg, to_addrs=recipients)
        server.quit()
        
        recipients_str = to_emails
        if cc_emails:
            recipients_str += f" (CC: {cc_emails})"
        
        if smtp_user and smtp_password:
            print(f"✅ Email enviado exitosamente a {recipients_str} desde {smtp_user} (credenciales propias)")
        else:
            print(f"✅ Email enviado exitosamente a {recipients_str} desde {SMTP_USER} (credenciales predeterminadas)")
        
        if smtp_user and smtp_password:
            # Try to append to Sent folder via IMAP
            try:
                append_to_sent_folder(use_smtp_user, use_smtp_password, msg)
            except Exception as e:
                print(f"⚠️ Could not save to Sent folder: {e}")
        
        # FASE 2: Guardar en historial de emails (no afecta el envío si falla)
        if deal_id:
            try:
                import json
                import re
                adjuntos_json = json.dumps([{
                    'nombre': f'Cotizacion_{cotizacion["folio"]}.pdf',
                    'tipo': 'application/pdf'
                }])
                
                # Extract Message-ID from sent email (if available)
                message_id = msg.get('Message-ID', '')
                if not message_id:
                    # Generate a Message-ID if not present
                    import uuid
                    domain = sender_email.split('@')[1] if '@' in sender_email else 'inair.com.mx'
                    message_id = f"<{uuid.uuid4()}@{domain}>"
                
                # Generate thread_id usando deal_id + cotizacion_id para garantizar agrupación
                # IMPORTANTE: Esto asegura que TODOS los emails de esta cotización se agrupen juntos
                asunto = f'Cotización {cotizacion["folio"]} - {cotizacion["cliente_nombre"]}'
                
                # Nuevo formato: deal_{deal_id}_cot_{cotizacion_id}
                thread_id = f"deal_{deal_id}_cot_{cotizacion_id}"
                print(f"   📎 Thread ID generado: {thread_id}")
                
                # Guardar destinatarios completos (To + CC)
                destinatario_completo = to_emails
                if cc_emails:
                    destinatario_completo += f" (CC: {cc_emails})"
                
                create_email_record(
                    deal_id=deal_id,
                    direccion='salida',
                    tipo='cotizacion',
                    asunto=asunto,
                    cuerpo=mensaje_final[:1000],  # Primeros 1000 chars
                    remitente=sender_email,
                    destinatario=destinatario_completo,
                    adjuntos=adjuntos_json,
                    cotizacion_id=cotizacion_id,
                    estado='enviado',
                    thread_id=thread_id,
                    message_id=message_id[:200] if message_id else None
                )
                print(f"📧 Email guardado en historial del trato #{deal_id} (thread_id: {thread_id[:50]}...)")
            except Exception as e:
                print(f"⚠️ No se pudo guardar en historial: {e}")
                # No lanzar error, el email ya se envió exitosamente
        
        return True
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        raise

def send_generic_email(recipient_email, asunto, mensaje, sender_email=None, sender_name=None,
                       smtp_user=None, smtp_password=None, firma_vendedor=None, firma_imagen=None, 
                       cc=None, attachments=None, parent_message_id=None, references_chain=None):
    # Send a generic email (replies, follow-ups, etc.)
    # Args: recipient_email, asunto, mensaje, etc.
    # parent_message_id: Message-ID del email padre para threading (opcional)
    # references_chain: Cadena completa de References con todos los message_ids del thread (opcional)
    # Use defaults if not provided
    use_smtp_user = smtp_user if smtp_user and smtp_password else SMTP_USER
    use_smtp_password = smtp_password if smtp_user and smtp_password else SMTP_PASSWORD
    sender_email = sender_email or SMTP_USER
    sender_name = sender_name or FROM_NAME
    
    # Create email
    msg = MIMEMultipart()
    
    # CRÍTICO: Generar Message-ID ANTES de agregar otros headers
    # Esto asegura que el Message-ID esté disponible para threading
    import uuid
    domain = sender_email.split('@')[1] if '@' in sender_email else 'inair.com.mx'
    message_id = f"<{uuid.uuid4()}@{domain}>"
    msg['Message-ID'] = message_id
    
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = recipient_email
    msg['Reply-To'] = sender_email
    msg['Subject'] = asunto
    
    # Add threading headers if this is a reply (CRÍTICO para que se agrupe en bandeja personal)
    if parent_message_id:
        # Limpiar parent_message_id si viene con < > o sin ellos
        clean_parent_id = parent_message_id.strip()
        if not clean_parent_id.startswith('<'):
            clean_parent_id = f'<{clean_parent_id}>'
        msg['In-Reply-To'] = clean_parent_id
        
        # References debe incluir TODA la cadena del thread, no solo el padre directo
        # Esto es CRÍTICO para que Gmail/Outlook agrupen correctamente
        if references_chain:
            # Si ya tenemos la cadena completa, usarla y agregar el padre al final si no está
            refs = references_chain.strip()
            if clean_parent_id not in refs:
                refs = f"{refs} {clean_parent_id}"
            msg['References'] = refs
        else:
            # Fallback: solo el padre (menos ideal pero mejor que nada)
            msg['References'] = clean_parent_id
    
    # Add CC if provided
    if cc:
        msg['Cc'] = cc
    
    # Convert line breaks to HTML
    mensaje_html = mensaje.replace('\n', '<br>')
    
    # Build signature section
    signature_html = "<br><br><p>Saludos cordiales,</p>"
    
    # If there's a signature image, use it
    if firma_imagen:
        signature_html += (f'<p><img src="data:image/png;base64,{firma_imagen}" alt="Firma" '
                           'style="max-width: 100px; max-height: 50px; width: auto; height: auto; display: block; margin: 10px 0;"></p>')
    
    # Add text signature
    if firma_vendedor:
        import re
        firma_limpia = re.sub(r'\n\s*\n', '\n', firma_vendedor)
        firma_text_html = firma_limpia.replace('\n', '<br>')
        signature_html += f'<div style="margin-top: 10px; line-height: 1.3;">{firma_text_html}</div></p>'
    else:
        signature_html += "<p><b>INGENIERÍA EN AIRE SA DE CV</b><br>"
        signature_html += "Tel: (664) 250-0022<br>"
        signature_html += f"{sender_email}<br>"
        signature_html += "www.inair.com.mx</p>"
    
    # Email body
    body = "<html>\n"
    body += '<body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">\n'
    body += '<div style="color: #444;">\n'
    body += f'{mensaje_html}\n'
    body += '</div>\n'
    body += f'{signature_html}\n'
    body += '</body>\n'
    body += '</html>'
    
    # CRÍTICO: Adjuntar el cuerpo HTML PRIMERO
    msg.attach(MIMEText(body, 'html'))
    
    # CRÍTICO: Adjuntar archivos DESPUÉS del cuerpo HTML
    # Attach files if provided
    if attachments:
        print(f"\n{'='*60}")
        print(f"📎 PROCESANDO {len(attachments)} ADJUNTO(S) PARA ENVÍO")
        print(f"{'='*60}")
        for idx, att in enumerate(attachments, 1):
            try:
                # PRIORIDAD 1: absolute_path (path completo en disco) - VERIFICAR EXISTENCIA
                # PRIORIDAD 2: path (path relativo con static/uploads)
                file_path = att.get('absolute_path')
                if not file_path or (file_path and not os.path.exists(file_path)):
                    file_path = att.get('path')
                original_name = att.get('filename') or att.get('original_name', 'attachment')
                
                print(f"\n📎 Adjunto #{idx}/{len(attachments)}: {original_name}")
                print(f"   absolute_path: {att.get('absolute_path', 'NO DISPONIBLE')}")
                print(f"   path: {att.get('path', 'NO DISPONIBLE')}")
                print(f"   file_path seleccionado: {file_path}")
                
                if not file_path:
                    print(f"   ❌ ERROR: No se encontró ningún path para el adjunto")
                    print(f"   Keys disponibles en att: {list(att.keys())}")
                    continue
                
                # Verificar existencia del archivo
                if not os.path.exists(file_path):
                    print(f"   ⚠️ Archivo no existe en: {file_path}")
                    # Intentar múltiples paths alternativos
                    alt_paths = []
                    
                    # Opción 1: Si tenemos absolute_path pero no existe, intentar construir desde file_path
                    if att.get('file_path'):
                        alt_paths.append(os.path.join('static', 'uploads', att.get('file_path')))
                    
                    # Opción 2: Si tenemos absolute_path, intentar path relativo
                    if att.get('absolute_path'):
                        # Extraer solo el nombre del archivo y construir path relativo
                        abs_path = att.get('absolute_path')
                        if 'attachments' in abs_path:
                            rel_part = abs_path.split('attachments')[1].lstrip(os.sep).replace(os.sep, '/')
                            alt_paths.append(os.path.join('static', 'uploads', 'attachments', rel_part))
                    
                    # Opción 3: Path relativo directo
                    if 'static/uploads' not in str(file_path):
                        alt_paths.append(os.path.join('static', 'uploads', str(file_path)))
                    
                    # Intentar cada path alternativo
                    found = False
                    for alt_path in alt_paths:
                        print(f"   Intentando path alternativo: {alt_path}")
                        if os.path.exists(alt_path):
                            file_path = alt_path
                            print(f"   ✅ Encontrado en path alternativo")
                            found = True
                            break
                    
                    if not found:
                        print(f"   ❌ No se pudo encontrar el archivo en ningún path")
                        print(f"   Paths intentados: {[file_path] + alt_paths}")
                        continue
                
                # Leer y adjuntar archivo
                print(f"   📖 Leyendo archivo...")
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    file_size = len(file_data)
                    print(f"   ✅ Archivo leído: {file_size} bytes")
                    
                    # Crear adjunto MIME con Content-Type correcto
                    mime_type = att.get('mime_type') or att.get('tipo') or 'application/octet-stream'
                    
                    # Usar MIMEApplication para todos los archivos (más robusto)
                    # MIMEText ya está importado al inicio del archivo, pero usamos MIMEApplication
                    # para evitar problemas de encoding con archivos de texto
                    attachment = MIMEApplication(file_data)
                    
                    # CRÍTICO: Agregar headers en el orden correcto
                    attachment.add_header('Content-Disposition', 'attachment', filename=original_name)
                    attachment.add_header('Content-Type', mime_type)
                    
                    # Adjuntar al mensaje MIME
                    msg.attach(attachment)
                    print(f"   ✅ Adjunto agregado exitosamente al email ({file_size} bytes, tipo: {mime_type})")
            except Exception as e:
                print(f"   ❌ ERROR adjuntando archivo {att.get('filename', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()
        print(f"{'='*60}\n")
    
    # Verificar que los adjuntos estén en el mensaje antes de enviar
    if attachments:
        attached_parts = []
        for part in msg.walk():
            content_disp = str(part.get_content_disposition() or '')
            if 'attachment' in content_disp.lower():
                attached_parts.append(part)
        print(f"\n📎 VERIFICACIÓN FINAL: {len(attached_parts)} adjunto(s) en el mensaje antes de enviar")
        if len(attached_parts) == 0:
            print(f"   ⚠️ ADVERTENCIA CRÍTICA: Se esperaban {len(attachments)} adjunto(s) pero NO se encontraron!")
            print(f"   Revisando estructura completa del mensaje MIME...")
            all_parts = list(msg.walk())
            print(f"   Total de partes en mensaje: {len(all_parts)}")
            for idx, part in enumerate(all_parts):
                ct = part.get_content_type()
                cd = str(part.get_content_disposition() or 'N/A')
                fn = part.get_filename() or 'N/A'
                print(f"   Parte #{idx}: Type={ct}, Disposition={cd}, Filename={fn}")
        else:
            for idx, part in enumerate(attached_parts, 1):
                filename = part.get_filename() or 'sin nombre'
                try:
                    payload = part.get_payload(decode=True)
                    size = len(payload) if payload else 0
                except:
                    size = 0
                print(f"   ✅ Adjunto #{idx} verificado: {filename} ({size} bytes)")
    
    # Send email
    try:
        if SMTP_USE_SSL:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
        
        server.login(use_smtp_user, use_smtp_password)
        server.send_message(msg)
        server.quit()
        
        if smtp_user and smtp_password:
            # Try to append to Sent folder via IMAP
            try:
                append_to_sent_folder(use_smtp_user, use_smtp_password, msg)
            except Exception as e:
                print(f"⚠️ Could not save to Sent folder: {e}")

        # Message-ID ya fue generado antes de enviar
        # Usar el que ya está en el mensaje
        message_id = msg.get('Message-ID', '')
        
        # Log para debugging - CRÍTICO para diagnosticar threading
        print(f"\n{'='*60}")
        print(f"📧 EMAIL ENVIADO - Threading Debug")
        print(f"{'='*60}")
        print(f"   To: {recipient_email}")
        print(f"   Subject: {asunto}")
        print(f"   Message-ID: {message_id}")
        if parent_message_id:
            print(f"   ✅ Parent message_id: {parent_message_id[:80]}")
            print(f"   ✅ In-Reply-To: {msg.get('In-Reply-To', 'NO AGREGADO')}")
            print(f"   ✅ References: {msg.get('References', 'NO AGREGADO')[:150]}")
        else:
            print(f"   ⚠️ NO hay parent_message_id - threading NO configurado")
        if references_chain:
            print(f"   ✅ References chain length: {len(references_chain)} chars")
        print(f"{'='*60}\n")
        
        print(f"✅ Respuesta enviada exitosamente a {recipient_email}")
        return {'success': True, 'message_id': message_id}
    except Exception as e:
        print(f"❌ Error enviando respuesta: {e}")
        raise

def send_factura_pdf(factura_id, recipient_email, contador_email=None, contador_nombre=None, 
                     firma_contador=None, mensaje_personalizado=None, smtp_user=None, smtp_password=None, 
                     firma_imagen=None, deal_id=None, subject=None):
    """Send invoice PDF via email from accountant's account."""
    
    from database import get_factura_by_id, create_email_record
    
    # Get invoice details
    factura = get_factura_by_id(factura_id)
    if not factura:
        raise Exception("Factura no encontrada")

    # Context-aware defaults
    if deal_id:
        # Use 'envio_factura' context
        msg_data = get_deal_message(deal_id, 'Finanzas', 'envio_factura')
        if not mensaje_personalizado:
            mensaje_personalizado = msg_data.get('body')
        if not firma_contador:
            firma_contador = msg_data.get('signature')
    
    # Generate PDF using shared function from app.py
    from app import generate_factura_pdf_bytes
    pdf_bytes = generate_factura_pdf_bytes(factura_id)
    if not pdf_bytes:
        raise Exception("Error generando PDF")
    
    # Determine SMTP credentials (use user's own or fallback to default)
    # IMPORTANTE: Si el email SMTP es Gmail, usar configuración de Gmail, no GoDaddy
    # CRÍTICO: Para guardar el remitente correcto, SIEMPRE usar email_smtp si está disponible
    # incluso si no tiene password (la password se puede configurar después)
    use_smtp_user = smtp_user if smtp_user else SMTP_USER
    use_smtp_password = smtp_password if smtp_password else SMTP_PASSWORD
    
    # Detectar si es Gmail y ajustar configuración SMTP
    is_gmail = use_smtp_user and '@gmail.com' in use_smtp_user.lower()
    if is_gmail:
        # Gmail requiere configuración diferente
        smtp_server_actual = "smtp.gmail.com"
        smtp_port_actual = 587
        smtp_use_ssl_actual = False  # Gmail usa STARTTLS en puerto 587
        print(f"📧 Detectado Gmail, usando smtp.gmail.com:587 con STARTTLS")
    else:
        # GoDaddy u otros
        smtp_server_actual = SMTP_SERVER
        smtp_port_actual = SMTP_PORT
        smtp_use_ssl_actual = SMTP_USE_SSL
        print(f"📧 Usando servidor GoDaddy: {smtp_server_actual}:{smtp_port_actual}")
    
    # Determine sender email
    # CRÍTICO: SIEMPRE usar email_smtp como remitente si está disponible
    # Esto es esencial para que la sincronización pueda encontrar al usuario correcto
    print(f"\n🔍 DEBUG send_factura_pdf - Determinando sender_email:")
    print(f"   smtp_user (email_smtp del contador): '{smtp_user}'")
    print(f"   contador_email (email regular): '{contador_email}'")
    print(f"   use_smtp_user (para enviar): '{use_smtp_user}'")
    print(f"   SMTP_USER (default): '{SMTP_USER}'")
    
    # PRIORIDAD: 1) email_smtp del contador, 2) email regular del contador, 3) default
    # Esto asegura que el remitente guardado sea el email_smtp para sincronización
    sender_email = smtp_user if smtp_user else (contador_email if contador_email else use_smtp_user)
    sender_name = contador_nombre or FROM_NAME
    
    print(f"   ✅ sender_email final (se guardará como remitente): '{sender_email}'")
    print(f"   ✅ sender_name final: '{sender_name}'")
    print(f"   ⚠️  NOTA: Si sender_email != use_smtp_user, el email se enviará desde use_smtp_user pero se guardará sender_email como remitente")
    
    # Create email
    msg = MIMEMultipart()
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = recipient_email
    msg['Reply-To'] = sender_email  # Replies go to accountant
    
    # Subject Logic (prioridad: subject del borrador > msg_data > default)
    if subject:
        # Usar asunto del borrador directamente
        msg['Subject'] = subject
    else:
        subject_tpl = None
        if deal_id and 'msg_data' in locals():
            subject_tpl = msg_data.get('subject')
            
        if subject_tpl:
            # Simple placeholder replacement
            safe_subject = (subject_tpl.replace('{folio}', str(factura['numero_factura']))
                                       .replace('{cliente}', str(factura['cliente_nombre'])))
            msg['Subject'] = safe_subject
        else:
            msg['Subject'] = f"Factura {factura['numero_factura']} - {factura['cliente_nombre']}"
    
    # Default message if not provided
    # Default message if not provided
    default_message = "Hola, buen día\n\n"
    default_message += "Adjunto encontrará la factura correspondiente.\n\n"
    default_message += "Quedamos a sus órdenes para cualquier duda o aclaración."
    
    # Use custom message or default
    mensaje_final = mensaje_personalizado if mensaje_personalizado else default_message
    
    # Convert line breaks to HTML
    mensaje_html = mensaje_final.replace('\n', '<br>')
    
    # Build signature section
    signature_html = "<p>Saludos cordiales,</p>"
    
    # If there's a signature image, use it (MUCH smaller size)
    if firma_imagen:
        signature_html += (f'<p><img src="data:image/png;base64,{firma_imagen}" alt="Firma" '
                           'style="max-width: 100px; max-height: 50px; width: auto; height: auto; display: block; margin: 10px 0;"></p>')
    
    # Add text signature
    if firma_contador:
        # If custom signature exists, use ONLY that (no extra info)
        import re
        firma_limpia = re.sub(r'\n\s*\n', '\n', firma_contador)  # Remove blank lines
        firma_text_html = firma_limpia.replace('\n', '<br>')
        signature_html += f'<div style="margin-top: 10px; line-height: 1.3;">{firma_text_html}</div></p>'
    else:
        # Generic signature (only if no custom signature)
        signature_html += "<p><b>INGENIERÍA EN AIRE SA DE CV</b><br>"
        signature_html += "Tel: (664) 250-0022<br>"
        signature_html += "ervin.moj@gmail.com<br>"
        signature_html += "www.inair.com.mx</p>"
    
    # Email body - Clean and simple
    body = "<html>\n"
    body += '<body style="font-family: Arial, sans-serif; padding: 20px;">\n'
    body += f'<h2 style="color: #D20000;">Factura {factura["numero_factura"]}</h2>\n'
    body += f'<p>Estimado(a) <b>{factura["cliente_nombre"]}</b>,</p>\n\n'
    body += '<div style="margin: 20px 0; line-height: 1.6; color: #444;">\n'
    body += f'{mensaje_html}\n'
    body += '</div>\n\n'
    body += f'<p style="margin-top: 20px;"><strong>Fecha de vencimiento:</strong> {factura.get("fecha_vencimiento") or "N/A"}</p>\n'
    body += f'<p><strong>Total:</strong> ${factura["total"]:,.2f} {factura.get("moneda", "MXN")}</p>\n\n'
    body += '<br>\n'
    body += f'{signature_html}\n'
    body += '</body>\n'
    body += '</html>'
    msg.attach(MIMEText(body, 'html'))
    
    # Attach PDF
    pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
    pdf_attachment.add_header('Content-Disposition', 'attachment', filename=f'Factura_{factura["numero_factura"]}.pdf')
    msg.attach(pdf_attachment)
    
    # Send email (use accountant's credentials if configured, otherwise use generic)
    try:
        print(f"📧 Conectando a SMTP {smtp_server_actual}:{smtp_port_actual}...")
        # Connect using SSL or STARTTLS based on configuration
        if smtp_use_ssl_actual:
            # SSL connection (port 465) - GoDaddy
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_server_actual, smtp_port_actual, context=context, timeout=30)
        else:
            # STARTTLS connection (port 587) - Gmail u otros
            server = smtplib.SMTP(smtp_server_actual, smtp_port_actual, timeout=30)
            server.starttls()
        
        print(f"📧 Iniciando sesión con {use_smtp_user}...")
        # Login with custom or default credentials
        try:
            server.login(use_smtp_user, use_smtp_password)
        except smtplib.SMTPAuthenticationError as auth_err:
            if is_gmail:
                error_msg = f"❌ Error de autenticación Gmail: {auth_err}\n"
                error_msg += "   NOTA: Gmail requiere una 'App Password' si tienes 2FA habilitado.\n"
                error_msg += "   Ve a: https://myaccount.google.com/apppasswords"
                print(error_msg)
            raise
        except smtplib.SMTPServerDisconnected as conn_err:
            if is_gmail:
                error_msg = f"❌ Gmail cerró la conexión: {conn_err}\n"
                error_msg += "   Posibles causas:\n"
                error_msg += "   1. La contraseña no es una 'App Password' (necesaria con 2FA)\n"
                error_msg += "   2. 'Acceso de aplicaciones menos seguras' no está habilitado\n"
                error_msg += "   3. Las credenciales son incorrectas"
                print(error_msg)
            raise
        print(f"📧 Enviando mensaje a {recipient_email}...")
        server.send_message(msg)
        print(f"📧 Mensaje enviado, cerrando conexión...")
        server.quit()
        
        if smtp_user and smtp_password:
            print(f"✅ Email enviado exitosamente a {recipient_email} desde {smtp_user} (credenciales propias)")
        else:
            print(f"✅ Email enviado exitosamente a {recipient_email} desde {SMTP_USER} (credenciales predeterminadas)")
        
        if smtp_user and smtp_password:
            # Try to append to Sent folder via IMAP
            try:
                append_to_sent_folder(use_smtp_user, use_smtp_password, msg)
            except Exception as e:
                print(f"⚠️ Could not save to Sent folder: {e}")
        
        # Guardar en historial de emails (no afecta el envío si falla)
        if deal_id:
            try:
                import json
                import re
                adjuntos_json = json.dumps([{
                    'nombre': f'Factura_{factura["numero_factura"]}.pdf',
                    'tipo': 'application/pdf'
                }])
                
                # Extract Message-ID from sent email (if available)
                message_id = msg.get('Message-ID', '')
                if not message_id:
                    # Generate a Message-ID if not present
                    import uuid
                    domain = sender_email.split('@')[1] if '@' in sender_email else 'inair.com.mx'
                    message_id = f"<{uuid.uuid4()}@{domain}>"
                
                # Generate normalized thread_id from subject
                asunto = f'Factura {factura["numero_factura"]} - {factura["cliente_nombre"]}'
                base_subject = re.sub(r'^((?:Re|Fwd|Rv|Fw|Aw|Resend)(?:\[\d+\])?:\s*)+', '', asunto, flags=re.IGNORECASE).strip()
                thread_id = base_subject[:100]  # First 100 chars as thread identifier
                
                print(f"📝 Guardando email en historial: deal_id={deal_id}, asunto='{asunto[:50]}...', thread_id='{thread_id[:50]}...'")
                print(f"🔍 DEBUG: sender_email que se guardará como remitente: '{sender_email}'")
                print(f"🔍 DEBUG: use_smtp_user usado para enviar: '{use_smtp_user}'")
                print(f"🔍 DEBUG: contador_email recibido: '{contador_email}'")
                
                create_email_record(
                    deal_id=deal_id,
                    direccion='salida',
                    tipo='factura',
                    asunto=asunto,
                    cuerpo=mensaje_final[:1000],  # Primeros 1000 chars
                    remitente=sender_email,
                    destinatario=recipient_email,
                    adjuntos=adjuntos_json,
                    cotizacion_id=None,
                    estado='enviado',
                    thread_id=thread_id,
                    message_id=message_id[:200] if message_id else None
                )
                print(f"✅ Email guardado exitosamente en historial del trato #{deal_id}")
                print(f"   Remitente guardado: '{sender_email}'")
                print(f"   Thread ID: {thread_id[:50]}...")
                print(f"   Message ID: {message_id[:50] if message_id else 'N/A'}...")
            except Exception as e:
                print(f"❌ ERROR al guardar en historial: {e}")
                import traceback
                traceback.print_exc()
                # No lanzar error, el email ya se envió exitosamente
        
        return True
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        raise

def append_to_sent_folder(username, password, msg):
    """Append sent email to IMAP Sent folder"""
    import imaplib
    import time
    
    # Auto-detect Gmail vs GoDaddy
    is_gmail = '@gmail.com' in username.lower()
    
    if is_gmail:
        IMAP_SERVER = "imap.gmail.com"
        IMAP_PORT = 993
    else:
        IMAP_SERVER = "imap.secureserver.net"
        IMAP_PORT = 993
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(username, password)
        
        # Try common names for Sent folder
        sent_folders = ['Sent', 'Sent Items', 'Enviados', 'Elementos Enviados', '[Gmail]/Sent Mail']
        target_folder = None
        
        # List folders to check what exists
        # typ, folders = mail.list()
        
        for folder in sent_folders:
            try:
                typ, data = mail.select(folder)
                if typ == 'OK':
                    target_folder = folder
                    break
            except:
                continue
        
        if target_folder:
            # Append message
            # msg.as_bytes() or str(msg).encode('utf-8')
            mail.append(target_folder, '\\Seen', imaplib.Time2Internaldate(time.time()), msg.as_bytes())
            print(f"✅ Email guardado en carpeta '{target_folder}'")
        else:
            print("⚠️ No se encontró carpeta de Enviados")
            
        mail.logout()
    except Exception as e:
        print(f"⚠️ No se pudo guardar en carpeta Enviados (no crítico): {e}")
        # No lanzar error, esto no es crítico para el envío


