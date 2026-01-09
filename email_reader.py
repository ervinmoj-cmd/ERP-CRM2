# email_reader.py - FASE 3: IMAP Integration for reading client responses
import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
import os
import uuid
import json

# IMAP Configuration
IMAP_SERVER = "imap.secureserver.net"  # GoDaddy IMAP
IMAP_PORT = 993
IMAP_USE_SSL = True
ATTACHMENTS_DIR = os.path.join("static", "uploads", "email_attachments")

def ensure_attachments_dir():
    """Ensure attachments directory exists"""
    if not os.path.exists(ATTACHMENTS_DIR):
        os.makedirs(ATTACHMENTS_DIR)

def connect_imap(email_account, password):
    """Connect to IMAP server - Auto-detect Gmail vs GoDaddy"""
    try:
        # Detectar si es Gmail
        is_gmail = '@gmail.com' in email_account.lower()
        
        if is_gmail:
            imap_server = "imap.gmail.com"
            imap_port = 993
            print(f"📧 Detectado Gmail, usando imap.gmail.com:993")
        else:
            imap_server = IMAP_SERVER
            imap_port = IMAP_PORT
            print(f"📧 Usando servidor GoDaddy: {imap_server}:{imap_port}")
        
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        print(f"📧 Intentando autenticación con {email_account}...")
        mail.login(email_account, password)
        print(f"✅ Autenticación IMAP exitosa")
        return mail
    except imaplib.IMAP4.error as e:
        error_str = str(e)
        if 'AUTHENTICATIONFAILED' in error_str:
            if is_gmail:
                print(f"❌ Error de autenticación Gmail: {error_str}")
                print(f"   NOTA: Gmail requiere una 'App Password' si tienes 2FA habilitado.")
                print(f"   Ve a: https://myaccount.google.com/apppasswords")
            else:
                print(f"❌ Error de autenticación GoDaddy: {error_str}")
                print(f"   Verifica que las credenciales sean correctas")
        else:
            print(f"❌ Error IMAP: {e}")
        return None
    except Exception as e:
        print(f"❌ Error conectando a IMAP: {e}")
        import traceback
        traceback.print_exc()
        return None

def decode_email_header(header_value):
    """Decode email header (handles encoded text)"""
    if not header_value:
        return ""
    
    decoded_parts = decode_header(header_value)
    result = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(encoding or 'utf-8', errors='ignore'))
        else:
            result.append(str(part))
    return ' '.join(result)

def extract_email_address(email_str):
    """Extract email address from 'Name <email@domain.com>' format"""
    match = re.search(r'<(.+?)>', email_str)
    if match:
        return match.group(1).lower()
    return email_str.lower().strip()

def get_email_body(msg):
    """Extract email body (prefer HTML, fallback to plain text) - LEGACY"""
    result = get_email_body_parts(msg)
    return result.get('body_html') or result.get('body_text') or ''

def get_email_body_parts(msg):
    """Extract email body parts: body_text, body_html, and generate snippet"""
    body_text = None
    body_html = None
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
                
            if content_type == "text/plain" and not body_text:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode('utf-8', errors='ignore')
                except:
                    pass
            elif content_type == "text/html" and not body_html:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_html = payload.decode('utf-8', errors='ignore')
                except:
                    pass
    else:
        # Single part message
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                decoded = payload.decode('utf-8', errors='ignore')
                if content_type == "text/plain":
                    body_text = decoded
                elif content_type == "text/html":
                    body_html = decoded
        except:
            pass
    
    # Generate snippet
    snippet = generate_snippet(body_text, body_html)
    
    return {
        'body_text': body_text,
        'body_html': body_html,
        'snippet': snippet
    }

def generate_snippet(body_text, body_html, max_length=250):
    """Generate a clean text snippet from body_text or body_html"""
    import re
    from html import unescape
    
    # Prefer body_text if available
    if body_text:
        # Clean up whitespace
        snippet = re.sub(r'\s+', ' ', body_text).strip()
        snippet = snippet.replace('\n', ' ').replace('\r', ' ')
        # Remove excessive spaces
        snippet = re.sub(r' {2,}', ' ', snippet)
    elif body_html:
        # Convert HTML to text
        # Remove script and style tags
        snippet = re.sub(r'<script[^>]*>.*?</script>', '', body_html, flags=re.DOTALL | re.IGNORECASE)
        snippet = re.sub(r'<style[^>]*>.*?</style>', '', snippet, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        snippet = re.sub(r'<[^>]+>', ' ', snippet)
        # Decode HTML entities
        snippet = unescape(snippet)
        # Clean up whitespace
        snippet = re.sub(r'\s+', ' ', snippet).strip()
    else:
        return ''
    
    # Truncate to max_length
    if len(snippet) > max_length:
        snippet = snippet[:max_length].rsplit(' ', 1)[0] + '...'
    
    return snippet

def extract_attachments(msg):
    """Extract and save attachments from email message"""
    attachments = []
    ensure_attachments_dir()
    
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
            
        # Relaxed check: Trust filename presence over Content-Disposition header
        filename = part.get_filename()
        
        if not filename:
            # If no filename, skip unless we want to try to guess ext from content-type
            # For now, safe to skip non-named parts
            continue

        filename = decode_email_header(filename)
        # Create unique filename to prevent overwrites
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(ATTACHMENTS_DIR, unique_name)
        
        try:
            with open(filepath, 'wb') as f:
                f.write(part.get_payload(decode=True))
            
            attachments.append({
                'nombre': filename,
                'tipo': part.get_content_type(),
                'url': f"/static/uploads/email_attachments/{unique_name}",
                'size': os.path.getsize(filepath)
            })
        except Exception as e:
            print(f"WARN Error guardando adjunto {filename}: {e}")
                
    return attachments

def fetch_new_emails(email_account, password, since_days=7, unseen_only=True):
    """Fetch new emails from inbox - Auto-detect Gmail vs GoDaddy"""
    # Detectar si es Gmail
    is_gmail = '@gmail.com' in email_account.lower()
    
    if is_gmail:
        imap_server = "imap.gmail.com"
        imap_port = 993
    else:
        imap_server = IMAP_SERVER
        imap_port = IMAP_PORT
    
    mail = connect_imap(email_account, password)
    if not mail:
        return []
    
    try:
        # Select inbox
        mail.select('INBOX')
        
        # Search for recent emails (last N days)
        from datetime import datetime, timedelta
        since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        
        # OPTIMIZACIÓN: Buscar solo correos NO LEÍDOS (UNSEEN) de los últimos días
        # Esto es mucho más rápido que leer todos los correos
        try:
            if unseen_only:
                # PRIORIDAD 1: Buscar solo UNSEEN (no leídos) - más rápido
                _, message_numbers = mail.search(None, f'(UNSEEN SINCE {since_date})')
                search_type = "UNSEEN"
            else:
                # Leer todos (incluye leídos) desde la fecha
                _, message_numbers = mail.search(None, f'(SINCE {since_date})')
                search_type = "ALL"
        except:
            # Fallback: buscar todos desde la fecha
            _, message_numbers = mail.search(None, f'(SINCE {since_date})')
            search_type = "ALL"
        
        # Get message numbers and limit to last 30 for speed
        msg_nums = message_numbers[0].split() if message_numbers[0] else []
        if len(msg_nums) > 30:
            msg_nums = msg_nums[-30:]  # Only last 30 emails
        
        print(f"   🔍 Búsqueda IMAP: {search_type}, encontrados {len(msg_nums)} emails")
        
        emails = []
        for num in msg_nums:
            try:
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)
                
                # Extract email data
                from_addr = decode_email_header(msg.get('From', ''))
                to_addr = decode_email_header(msg.get('To', ''))
                subject = decode_email_header(msg.get('Subject', ''))
                date_str = msg.get('Date', '')
                
                # Extract reply headers (important for thread detection)
                in_reply_to = msg.get('In-Reply-To', '')
                references = msg.get('References', '')
                
                # Parse date
                try:
                    date_tuple = email.utils.parsedate_tz(date_str)
                    if date_tuple:
                        timestamp = email.utils.mktime_tz(date_tuple)
                        date_obj = datetime.fromtimestamp(timestamp)
                    else:
                        date_obj = datetime.now()
                except:
                    date_obj = datetime.now()
                
                # Extract attachments
                attachments = extract_attachments(msg)
                
                emails.append({
                    'from': from_addr,
                    'to': to_addr,
                    'subject': subject,
                    'body': get_email_body(msg),
                    'date': date_obj,
                    'raw_message_id': msg.get('Message-ID', ''),
                    'in_reply_to': in_reply_to,
                    'references': references,
                    'attachments': attachments
                })
            except Exception as e:
                print(f"WARN Error procesando email: {e}")
        
        mail.close()
        mail.logout()
        return emails
        
    except Exception as e:
        print(f"X Error leyendo emails: {e}")
        try:
            mail.logout()
        except:
            pass
        return []

def fetch_all_emails(email_account, password, folder='INBOX', limit=50, since_days=30):
    """
    Fetch all emails from a specific folder (INBOX, SENT, etc.)
    Returns a list of email dictionaries with full details
    """
    is_gmail = '@gmail.com' in email_account.lower()
    
    if is_gmail:
        imap_server = "imap.gmail.com"
        imap_port = 993
    else:
        imap_server = IMAP_SERVER
        imap_port = IMAP_PORT
    
    mail = connect_imap(email_account, password)
    if not mail:
        return []
    
    try:
        # Select folder (INBOX, Sent, etc.)
        # Gmail uses [Gmail]/Sent Mail, others use Sent
        if folder == 'SENT':
            if is_gmail:
                try:
                    mail.select('"[Gmail]/Sent Mail"')
                except:
                    mail.select('"Sent"')
            else:
                try:
                    mail.select('"Sent"')
                except:
                    mail.select('"Sent Messages"')
        else:
            mail.select(folder)
        
        # Search for recent emails
        from datetime import datetime, timedelta
        since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        
        # Get all emails from the last N days
        _, message_numbers = mail.search(None, f'(SINCE {since_date})')
        
        msg_nums = message_numbers[0].split() if message_numbers[0] else []
        
        # Reverse to get newest first, then limit
        msg_nums.reverse()
        if len(msg_nums) > limit:
            msg_nums = msg_nums[:limit]
        
        print(f"   📬 Obteniendo {len(msg_nums)} correos de {folder}")
        
        emails = []
        for num in msg_nums:
            try:
                # Fetch full email
                _, msg_data = mail.fetch(num, '(RFC822 FLAGS)')
                email_body = msg_data[0][1]
                flags = msg_data[0][0].decode() if len(msg_data) > 0 else ''
                
                msg = email.message_from_bytes(email_body)
                
                # Extract email data
                from_addr = decode_email_header(msg.get('From', ''))
                to_addr = decode_email_header(msg.get('To', ''))
                cc_addr = decode_email_header(msg.get('Cc', ''))
                subject = decode_email_header(msg.get('Subject', ''))
                date_str = msg.get('Date', '')
                message_id = msg.get('Message-ID', '')
                in_reply_to = msg.get('In-Reply-To', '')
                references = msg.get('References', '')
                
                # Parse date
                try:
                    date_tuple = email.utils.parsedate_tz(date_str)
                    if date_tuple:
                        timestamp = email.utils.mktime_tz(date_tuple)
                        date_obj = datetime.fromtimestamp(timestamp)
                    else:
                        date_obj = datetime.now()
                except:
                    date_obj = datetime.now()
                
                # Check if read (SEEN flag)
                is_read = '\\Seen' in flags
                
                # Extract body parts (text, html, snippet)
                body_parts = get_email_body_parts(msg)
                
                # Extract attachments
                attachments = extract_attachments(msg)
                
                # Extract email addresses
                from_email = extract_email_address(from_addr)
                to_email = extract_email_address(to_addr)
                
                emails.append({
                    'uid': str(num.decode() if isinstance(num, bytes) else num),
                    'from': from_addr,
                    'from_email': from_email,
                    'to': to_addr,
                    'to_email': to_email,
                    'cc': cc_addr,
                    'subject': subject,
                    'body': body_parts.get('body_html') or body_parts.get('body_text') or '',  # Legacy field
                    'body_text': body_parts.get('body_text'),
                    'body_html': body_parts.get('body_html'),
                    'snippet': body_parts.get('snippet', ''),
                    'date': date_obj,
                    'date_str': date_obj.strftime('%Y-%m-%d %H:%M:%S'),
                    'message_id': message_id,
                    'in_reply_to': in_reply_to,
                    'references': references,
                    'attachments': attachments,
                    'is_read': is_read,
                    'folder': folder,
                    'has_attachments': len(attachments) > 0
                })
            except Exception as e:
                print(f"⚠️ Error procesando email {num}: {e}")
                continue
        
        mail.close()
        mail.logout()
        return emails
        
    except Exception as e:
        print(f"❌ Error leyendo emails de {folder}: {e}")
        import traceback
        traceback.print_exc()
        try:
            mail.logout()
        except:
            pass
        return []

def sync_client_responses(deal_id, user_email, user_password):
    """Sync client responses for a specific deal's email thread"""
    from database import (get_deal_by_id, get_deal_emails, create_email_record, 
                         get_deal_thread_subjects, email_exists_by_message_id, get_client_by_id,
                         create_attachment)
    
    print(f"\n{'='*60}")
    print(f"🔄 INICIANDO SINCRONIZACIÓN - Deal #{deal_id}")
    print(f"{'='*60}")
    
    # Get deal info
    deal = get_deal_by_id(deal_id)
    if not deal:
        print(f"❌ Deal {deal_id} no encontrado")
        return 0
    
    # Get client email if available
    client_email = None
    if deal.get('cliente_id'):
        client = get_client_by_id(deal['cliente_id'])
        if client:
            client_email = client.get('email', '').lower().strip() if client.get('email') else None
            print(f"📧 Email del cliente: {client_email or 'NO CONFIGURADO'}")
    
    # Also check deal.email field (direct email on deal)
    deal_email = deal.get('email', '').lower().strip() if deal.get('email') else None
    if deal_email and deal_email != client_email:
        print(f"📧 Email del trato: {deal_email}")
    
    # Get all possible client emails
    client_emails = set()
    if client_email:
        client_emails.add(client_email)
    if deal_email:
        client_emails.add(deal_email)
    
    # Obtener correos existentes del trato (CRÍTICO: debe estar antes de usarlo)
    existing_emails = get_deal_emails(deal_id)
    print(f"📧 Total emails en historial del trato: {len(existing_emails)}")
    
    # Obtener folios de cotizaciones vinculadas al deal (CRÍTICO para validación)
    from database import get_deal_by_id
    deal_info = get_deal_by_id(deal_id)
    deal_folios = set()
    if deal_info and deal_info.get('cotizaciones'):
        for cot in deal_info['cotizaciones']:
            if cot.get('folio'):
                deal_folios.add(cot['folio'])
                print(f"📋 Folio de cotización vinculada a este trato: {cot['folio']}")
    
    # Obtener asuntos de correos ENVIADOS desde este trato (normalizados, sin Re:/Fwd:)
    import re
    sent_subjects = []
    for e in existing_emails:
        if e.get('direccion') == 'salida' and e.get('asunto'):
            subject = e.get('asunto', '')
            # Normalizar: eliminar todos los Re:/Fwd:
            normalized = subject
            while True:
                new = re.sub(r'^((?:Re|Fwd|Rv|Fw|Aw|Resend)(?:\[\d+\])?:\s*)+', '', normalized, flags=re.IGNORECASE).strip()
                if new == normalized:
                    break
                normalized = new
            if normalized and normalized not in sent_subjects:
                sent_subjects.append(normalized.lower())
    
    print(f"📋 Folios válidos para este trato: {list(deal_folios)}")
    print(f"📋 Asuntos de correos enviados desde este trato: {len(sent_subjects)}")
    if sent_subjects:
        print(f"   Ejemplos: {sent_subjects[:2]}")
    
    # Obtener Message-IDs de correos ENVIADOS desde este trato (para verificar In-Reply-To/References)
    sent_message_ids = set()
    existing_thread_by_msgid = {}
    for e in existing_emails:
        if e.get('direccion') == 'salida' and e.get('message_id'):
            msg_id = e.get('message_id').strip('<>').lower()
            sent_message_ids.add(msg_id)
            # Guardar thread_id asociado para reutilizar
            if e.get('thread_id'):
                existing_thread_by_msgid[msg_id] = e.get('thread_id')
    
    print(f"📨 Message-IDs de correos enviados desde este trato: {len(sent_message_ids)}")
    
    # Si no hay correos enviados desde este trato, no hay nada que sincronizar
    if not sent_message_ids and not sent_subjects:
        print(f"⚠️ No hay correos enviados desde este trato aún, nada que sincronizar")
        return 0
    
    # Get existing emails to avoid duplicates - SOLO por Message-ID (método confiable)
    existing_message_ids = set()
    for e in existing_emails:
        msg_id = e.get('message_id')
        if msg_id:
            existing_message_ids.add(msg_id.lower().strip())
    
    # Hash fallback solo para emails sin Message-ID (usando subject normalizado)
    existing_hashes = set()
    for e in existing_emails:
        if not e.get('message_id'):  # Solo para emails sin Message-ID
            # Normalizar subject del email existente
            import re
            existing_subject = e.get('asunto', '')
            normalized_existing = existing_subject
            while True:
                new = re.sub(r'^((?:Re|Fwd|Rv|Fw|Aw|Resend)(?:\[\d+\])?:\s*)+', '', normalized_existing, flags=re.IGNORECASE).strip()
                if new == normalized_existing:
                    break
                normalized_existing = new
            remitente_existing = e.get('remitente', '').lower()
            hash_key = f"{normalized_existing.lower()}_{remitente_existing}_{str(e['created_at'])[:10]}"
            existing_hashes.add(hash_key)
    
    print(f"📊 Emails ya registrados: {len(existing_emails)}")
    
    # OPTIMIZACIÓN: Fetch new emails con timestamp para medir performance
    import time
    sync_start_time = time.time()
    
    is_gmail = '@gmail.com' in user_email.lower()
    imap_server_name = "imap.gmail.com" if is_gmail else IMAP_SERVER
    print(f"🔌 Conectando a {imap_server_name}...")
    
    fetch_start = time.time()
    # Intento 1: UNSEEN (rápido)
    new_emails = fetch_new_emails(user_email, user_password, since_days=7)
    # Si no hay nuevos (0 encontrados), intentar segundo pase incluyendo leídos recientes
    if not new_emails:
        print("⚠️ No se encontraron UNSEEN, intentando últimos 7 días (incluye leídos)...")
        new_emails = fetch_new_emails(user_email, user_password, since_days=7, unseen_only=False)
    fetch_time = time.time() - fetch_start
    print(f"📬 Se encontraron {len(new_emails)} emails en bandeja de entrada (tiempo: {fetch_time:.2f}s)")
    
    synced_count = 0
    skipped_duplicate = 0
    skipped_not_related = 0
    
    print(f"\n{'='*60}")
    print(f"🔍 PROCESANDO {len(new_emails)} EMAILS ENCONTRADOS")
    print(f"{'='*60}")
    
    for idx, email_data in enumerate(new_emails, 1):
        subject = email_data['subject']
        message_id = email_data.get('raw_message_id', '').lower() if email_data.get('raw_message_id') else ''
        from_email = extract_email_address(email_data['from']).lower()
        to_email = extract_email_address(email_data.get('to', '')).lower()
        
        print(f"\n📧 Email #{idx}/{len(new_emails)}")
        print(f"   Asunto: {subject[:60]}")
        print(f"   De: {from_email}")
        print(f"   Para: {to_email}")
        print(f"   Message-ID: {message_id[:50] if message_id else 'SIN Message-ID'}")
        
        # Normalize subject PRIMERO (remove ALL Re:/Fwd: prefixes, even multiple ones)
        import re
        # Eliminar TODOS los prefijos Re:/Fwd: repetidos (ej: "Re: Re: Re: Subject" -> "Subject")
        base_subject = subject
        while True:
            new_subject = re.sub(r'^((?:Re|Fwd|Rv|Fw|Aw|Resend)(?:\[\d+\])?:\s*)+', '', base_subject, flags=re.IGNORECASE).strip()
            if new_subject == base_subject:
                break
            base_subject = new_subject
        base_subject = base_subject.strip()
        # Extraer folio del subject entrante (ej. T-00035)
        folio_match = re.search(r'T-\d+', base_subject)
        incoming_folio = folio_match.group(0) if folio_match else None
        
        print(f"   📝 Subject original: '{subject[:60]}'")
        print(f"   📝 Subject normalizado: '{base_subject[:60]}'")
        
        # DEDUPLICACIÓN: Solo por Message-ID (NO por subject+fecha para evitar problemas con múltiples Re:)
        if message_id:
            if message_id in existing_message_ids:
                print(f"   ⏭️  DESCARTADO: Ya existe en BD (Message-ID duplicado: {message_id[:50]})")
                skipped_duplicate += 1
                continue
        else:
            # Si no hay Message-ID, usar hash más robusto (subject normalizado + from + date)
            # Pero solo como fallback, no como método principal
            fallback_hash = f"{base_subject.lower()}_{from_email}_{str(email_data['date'])[:10]}"
            if fallback_hash in existing_hashes:
                print(f"   ⏭️  DESCARTADO: Ya existe en BD (hash fallback duplicado)")
                skipped_duplicate += 1
                continue
        
        # LÓGICA SIMPLIFICADA: Un correo pertenece a este trato si cumple AL MENOS UNA de estas condiciones:
        # 1. Es respuesta directa (In-Reply-To/References) a un correo enviado desde este trato
        # 2. Viene del cliente del trato Y el asunto contiene el folio de la cotización vinculada
        # 3. Viene del cliente del trato Y el asunto coincide con correos enviados desde este trato
        
        is_related = False
        matched_reason = ""
        
        # Extraer In-Reply-To y References
        in_reply_to = email_data.get('in_reply_to', '').lower() if email_data.get('in_reply_to') else ''
        references = email_data.get('references', '').lower() if email_data.get('references') else ''
        
        print(f"   🔗 In-Reply-To: {in_reply_to[:50] if in_reply_to else 'N/A'}")
        print(f"   🔗 References: {references[:100] if references else 'N/A'}")
        
        # CONDICIÓN 1 (PRIORIDAD ALTA): Es respuesta directa a un correo enviado desde este trato
        if not is_related and (in_reply_to or references) and sent_message_ids:
            print(f"   🔍 Verificando si es respuesta directa (In-Reply-To/References)...")
            for sent_msg_id in sent_message_ids:
                sent_msg_clean = sent_msg_id.strip('<>').lower()
                in_reply_clean = in_reply_to.strip('<>').lower() if in_reply_to else ''
                refs_clean = references.lower() if references else ''
                
                if sent_msg_clean in in_reply_clean or sent_msg_clean in refs_clean:
                    is_related = True
                    matched_reason = f"RESPUESTA DIRECTA - In-Reply-To/References coincide con correo enviado desde este trato"
                    print(f"      ✅ MATCH: Es respuesta directa a correo enviado desde este trato")
                    break
            if not is_related:
                print(f"      ❌ No es respuesta directa a correos enviados desde este trato")
        
        # CONDICIÓN 2: Viene del cliente del trato Y el asunto contiene el folio de la cotización vinculada
        if not is_related and client_emails and from_email in client_emails and deal_folios:
            print(f"   🔍 Verificando si viene del cliente Y tiene folio de cotización del trato...")
            print(f"      Email del cliente: {from_email}")
            print(f"      Folio encontrado en asunto: {incoming_folio or 'NINGUNO'}")
            print(f"      Folios válidos del trato: {list(deal_folios)}")
            
            if incoming_folio and incoming_folio in deal_folios:
                is_related = True
                matched_reason = f"CLIENTE + FOLIO - Viene del cliente del trato y contiene folio de cotización vinculada ({incoming_folio})"
                print(f"      ✅ MATCH: Viene del cliente y contiene folio válido del trato")
            else:
                print(f"      ❌ No contiene folio válido del trato o no viene del cliente")
        
        # CONDICIÓN 3: Viene del cliente del trato Y el asunto coincide con correos enviados desde este trato
        if not is_related and client_emails and from_email in client_emails and sent_subjects:
            print(f"   🔍 Verificando si viene del cliente Y el asunto coincide con correos enviados...")
            print(f"      Email del cliente: {from_email}")
            print(f"      Subject normalizado: '{base_subject[:60]}'")
            print(f"      Asuntos de correos enviados: {len(sent_subjects)}")
            
            base_email_subj = base_subject.lower().strip()
            for sent_subj in sent_subjects:
                # Comparación exacta o contenido
                if base_email_subj == sent_subj or sent_subj in base_email_subj or base_email_subj in sent_subj:
                    is_related = True
                    matched_reason = f"CLIENTE + ASUNTO - Viene del cliente y asunto coincide con correo enviado desde este trato"
                    print(f"      ✅ MATCH: Viene del cliente y asunto coincide")
                    break
            
            if not is_related:
                print(f"      ❌ Asunto no coincide con correos enviados desde este trato")
        
        # Si no cumple ninguna condición, descartar
        if not is_related:
            print(f"   ⏭️  DESCARTADO: No cumple ninguna condición para pertenecer a este trato")
            print(f"      Razones:")
            print(f"      - From email: {from_email}")
            print(f"      - Email del cliente configurado: {list(client_emails) if client_emails else 'NO CONFIGURADO'}")
            print(f"      - In-Reply-To: {in_reply_to[:50] if in_reply_to else 'N/A'}")
            print(f"      - Subject normalizado: '{base_subject[:60]}'")
            print(f"      - Folio encontrado: {incoming_folio or 'NINGUNO'}")
            print(f"      - Folios válidos del trato: {list(deal_folios) if deal_folios else 'NINGUNO'}")
            skipped_not_related += 1
            continue
        
        print(f"   ✅ Email relacionado encontrado: {matched_reason}")
        
        # Determine direction based on who sent it
        direccion = 'entrada' if from_email != user_email.lower() else 'salida'
        
        # Prepare attachments JSON
        adjuntos_json = None
        if email_data.get('attachments'):
            adjuntos_json = json.dumps(email_data['attachments'])
            print(f"   📎 Adjuntos: {len(email_data['attachments'])}")
        
        # Calcular thread_id: usar el folio de la cotización si está disponible, o el asunto normalizado
        thread_id_final = None
        
        # Prioridad 1: Si hay folio de cotización, usarlo como thread_id base
        if incoming_folio and incoming_folio in deal_folios:
            thread_id_final = f"deal_{deal_id}_cot_{incoming_folio}"
            print(f"   🔗 Thread ID usando folio: '{thread_id_final}'")
        else:
            # Prioridad 2: Si hay In-Reply-To, intentar obtener thread_id del email padre
            if in_reply_to:
                parent_key = in_reply_to.strip('<>').lower()
                if parent_key in existing_thread_by_msgid and existing_thread_by_msgid[parent_key]:
                    thread_id_final = existing_thread_by_msgid[parent_key]
                    print(f"   🔗 Thread ID del email padre (In-Reply-To): '{thread_id_final[:50]}'")
                else:
                    # Buscar coincidencia parcial en References
                    refs_clean = references.lower() if references else ''
                    for msgid_key, t_id in existing_thread_by_msgid.items():
                        if msgid_key and msgid_key in refs_clean and t_id:
                            thread_id_final = t_id
                            print(f"   🔗 Thread ID por References: '{thread_id_final[:50]}'")
                            break
            
            # Prioridad 3: Si no encontramos, usar asunto normalizado
            if not thread_id_final:
                thread_id_final = base_subject[:100] if base_subject else f"deal_{deal_id}_thread"
                print(f"   🔗 Thread ID usando asunto normalizado: '{thread_id_final[:50]}'")
        
        # Save email
        print(f"   💾 Intentando guardar en BD...")
        print(f"      - deal_id: {deal_id} (ASOCIADO POR: {matched_reason})")
        print(f"      - direccion: {direccion}")
        print(f"      - thread_id: {thread_id_final[:50]}")
        print(f"      - message_id: {message_id[:50] if message_id else 'N/A'}")
        print(f"      - fecha: {email_data['date']}")
        
        # Calcular thread_root_id según RFC (prioridad: references > in_reply_to > subject_norm)
        from database import normalize_subject
        subject_norm = normalize_subject(subject)
        thread_root_id = None
        
        references = email_data.get('references', '').strip() if email_data.get('references') else ''
        in_reply_to = email_data.get('in_reply_to', '').strip() if email_data.get('in_reply_to') else ''
        
        if references:
            # thread_root_id = primer Message-ID de references
            refs_list = references.split()
            if refs_list:
                # Limpiar < > del primer Message-ID
                first_ref = refs_list[0].strip('<>').strip()
                if first_ref:
                    thread_root_id = first_ref
                    print(f"   🔗 thread_root_id desde References: {thread_root_id[:50]}")
        elif in_reply_to:
            # thread_root_id = in_reply_to
            thread_root_id = in_reply_to.strip('<>').strip()
            print(f"   🔗 thread_root_id desde In-Reply-To: {thread_root_id[:50]}")
        else:
            # thread_root_id = subject_norm (fallback)
            thread_root_id = subject_norm[:100]
            print(f"   🔗 thread_root_id desde subject_norm: {thread_root_id[:50]}")
        
        try:
            email_id = create_email_record(
                deal_id=deal_id,
                direccion=direccion,
                tipo='respuesta',
                asunto=subject,  # Guardar subject original (con Re: si tiene)
                cuerpo=email_data['body'][:5000],
                remitente=email_data['from'],
                destinatario=email_data['to'],
                adjuntos=adjuntos_json,
                cotizacion_id=None,
                estado='recibido' if direccion == 'entrada' else 'enviado',
                thread_id=thread_id_final,  # Usar thread_id normalizado
                message_id=email_data.get('raw_message_id', '')[:200] if email_data.get('raw_message_id') else None,
                in_reply_to=in_reply_to if in_reply_to else None,
                references=references if references else None,
                subject_raw=subject,
                subject_norm=subject_norm,
                thread_root_id=thread_root_id,
                direction='inbound' if direccion == 'entrada' else 'outbound',
                provider='outlook_imap'
            )
            synced_count += 1
            print(f"   ✅ GUARDADO EXITOSAMENTE (ID: {email_id})")
            print(f"      Asunto: {subject[:60]}")
            print(f"      Thread ID: {thread_id_final[:50]}")
            
            # Guardar adjuntos en la tabla attachments para que aparezcan en el chat
            if email_data.get('attachments') and len(email_data['attachments']) > 0:
                print(f"   📎 Guardando {len(email_data['attachments'])} adjunto(s) en BD...")
                from database import create_attachment
                for att_data in email_data['attachments']:
                    try:
                        # att_data viene de extract_attachments con: nombre, tipo, url, size
                        # Necesitamos construir el file_path relativo desde la url
                        url = att_data.get('url', '')
                        if url.startswith('/static/uploads/'):
                            file_path = url.replace('/static/uploads/', '')
                        elif url.startswith('static/uploads/'):
                            file_path = url.replace('static/uploads/', '')
                        else:
                            file_path = url
                        
                        create_attachment(
                            owner_type='email',
                            owner_id=email_id,
                            filename=os.path.basename(file_path),
                            original_name=att_data.get('nombre', 'adjunto'),
                            mime_type=att_data.get('tipo', 'application/octet-stream'),
                            size=att_data.get('size', 0),
                            file_path=file_path,
                            created_by=None  # Email recibido, no tiene created_by
                        )
                        print(f"      ✅ Adjunto guardado: {att_data.get('nombre', 'adjunto')}")
                    except Exception as e:
                        print(f"      ⚠️ Error guardando adjunto {att_data.get('nombre', 'unknown')}: {e}")
        except Exception as e:
            print(f"   ❌ ERROR AL GUARDAR: {e}")
            import traceback
            traceback.print_exc()
    
    sync_total_time = time.time() - sync_start_time
    
    print(f"\n{'='*60}")
    print(f"✅ SINCRONIZACIÓN COMPLETADA")
    print(f"   ⏱️  Tiempo total: {sync_total_time:.2f}s")
    print(f"      - Conexión y búsqueda: {fetch_time:.2f}s")
    print(f"      - Procesamiento: {sync_total_time - fetch_time:.2f}s")
    print(f"   📬 Emails encontrados en bandeja: {len(new_emails)}")
    print(f"   ⏭️  Descartados (duplicados): {skipped_duplicate}")
    print(f"   ⏭️  Descartados (no relacionados): {skipped_not_related}")
    print(f"   ✅ Emails nuevos guardados: {synced_count}")
    print(f"{'='*60}\n")
    
    # Verificación post-sincronización: confirmar que los emails guardados aparecen en la consulta
    if synced_count > 0:
        print(f"🔍 VERIFICACIÓN POST-SINCRONIZACIÓN")
        print(f"{'='*60}")
        updated_emails = get_deal_emails(deal_id)
        entrada_count = len([e for e in updated_emails if e.get('direccion') == 'entrada'])
        salida_count = len([e for e in updated_emails if e.get('direccion') == 'salida'])
        print(f"📊 Total emails en historial después de sync: {len(updated_emails)}")
        print(f"   - Entrada: {entrada_count}")
        print(f"   - Salida: {salida_count}")
        print(f"{'='*60}\n")
    
    return synced_count



