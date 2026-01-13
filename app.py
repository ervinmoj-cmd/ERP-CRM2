# app.py
import os, io, json, base64, math, sqlite3, re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, flash
from functools import wraps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader
from PIL import Image
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Trigger Reload

# Import config for path management (Railway + Local)
try:
    from config import (
        DATA_DIR, DATABASE_DIR, UPLOAD_DIR, FIRMAS_DIR, GENERADOS_DIR,
        DATABASE_MAIN, DATABASE_AUX, IS_RAILWAY, APP_ROOT as CONFIG_APP_ROOT
    )
    DATABASE = DATABASE_MAIN
except ImportError:
    # Fallback si config.py no existe (no debería pasar)
    DATABASE = "inair_reportes.db"


# Import database functions
from database import (
    init_db, get_all_users, get_user_by_username, get_user_by_id, create_user, delete_user, update_user,
    get_all_reports, get_report_by_folio, save_report, search_reports,
    get_next_folio, get_dashboard_stats,
    get_all_clients, get_client_by_id, create_client, update_client, delete_client,
    add_client_contact, get_client_contacts, delete_client_contacts,
    add_client_equipment, get_client_equipment, get_equipment_by_id,
    update_client_equipment, delete_client_equipment,
    get_equipment_types_by_client, get_models_by_client_and_type,
    # PI
    get_all_pis, get_pi_by_id, create_pi, update_pi, delete_pi, get_next_pi_folio,
    get_cotizaciones_by_client, update_pi_item_status, update_pi_items_bulk,



    # Draft report functions
    save_draft_report, get_draft_by_folio, get_all_drafts, delete_draft,
    mark_draft_as_sent, update_draft_pdf, get_pending_drafts_by_tecnico,
    # Almacen (Inventory) functions
    create_refaccion, update_refaccion, delete_refaccion, search_refacciones,
    get_all_refacciones, get_refaccion_by_id,
    create_reserva, get_reservas_by_refaccion, delete_reserva, fulfill_reserva,
    get_all_cotizaciones, get_cotizacion_by_id, create_cotizacion, update_cotizacion, delete_cotizacion,
    get_next_cotizacion_folio, get_cotizaciones_by_client,
    # CRM functions
    CRM_STAGES, create_deal, update_deal, update_deal_stage, update_deal_email_fields, delete_deal,
    get_all_deals, get_deal_by_id, get_deals_by_stage, get_deals_by_vendor,
    get_deals_by_client_id, get_next_deal_folio,
    get_deals_by_client_id, get_next_deal_folio,
    create_activity, get_deal_activities, get_pending_activities, get_pending_activities_by_vendor,
    mark_activity_complete, delete_activity,
    link_cotizacion_to_deal, unlink_cotizacion_from_deal, link_reporte_to_deal, unlink_reporte_from_deal,
    get_reports_by_deal,
    link_pi_to_deal, unlink_pi_from_deal, get_pis_for_deal,
    # CRM Puesto Stages functions
    get_stages_by_puesto, get_all_puesto_stages, add_puesto_stage, update_puesto_stage, 
    delete_puesto_stage, get_stage_triggers, get_trigger_for_stage, get_deals_by_puesto,
    # Service Deal functions (Equipment & Technicians)
    add_equipo_to_deal, get_equipos_by_deal, get_equipo_deal_by_id, update_equipo_deal, delete_equipo_deal,
    assign_tecnico_to_deal, remove_tecnico_from_deal, update_tecnico_puntos,
    get_tecnicos_by_deal, get_deals_by_tecnico, is_tecnico_assigned_to_deal,
    # Service Timer functions
    start_service_timer, stop_service_timer, get_service_timer, is_timer_active, can_user_control_timer,
    # Equipment Photos & Comments
    add_equipo_foto, get_equipo_fotos, delete_equipo_foto,
    add_equipo_comentario, get_equipo_comentarios, delete_equipo_comentario,
    # Puestos functions
    get_all_puestos, get_puesto_by_id, get_puesto_by_nombre, create_puesto, update_puesto, delete_puesto,
    # Proveedores (Suppliers) functions
    get_all_proveedores, get_proveedor_by_id, create_proveedor, update_proveedor, delete_proveedor,
    # Compras (Purchase Orders) functions
    get_all_compras, get_compra_by_id, get_next_compra_folio, create_compra, update_compra, delete_compra,
    # Finanzas functions
    create_factura, get_all_facturas, get_factura_by_id, update_factura_estado,
    create_pago, delete_pago, create_gasto, get_all_gastos, get_gastos_by_periodo,
    get_flujo_caja, get_cuentas_por_cobrar, get_dashboard_stats as get_finanzas_stats,
    get_next_factura_folio, preview_next_factura_folio, add_factura_partida, get_factura_partidas, delete_factura_partida,
    get_cotizaciones_disponibles,
    # Messages and Notifications functions (FASE 1)
    create_deal_message, get_deal_messages, delete_deal_message,
    get_user_notifications, get_unread_notification_count, mark_notification_read,
    mark_all_notifications_read, delete_notification, create_notification,
    # Email History functions (FASE 2)
    create_email_record, get_deal_emails, get_client_emails, get_email_by_id,
    update_email_status, delete_email_record,
    # Email Templates and Module Messages functions
    get_email_template, get_all_email_templates, create_or_update_email_template,
    get_deal_email_message, create_or_update_deal_email_message, delete_deal_email_message,
    get_deal_email_content,
    # Attachment functions
    create_attachment, get_attachments, get_attachment_by_id, delete_attachment,
    # Compras Module (FASE 3)
    get_all_proveedores, get_proveedor_by_id, create_proveedor, update_proveedor, delete_proveedor,
    get_all_compras, get_compra_by_id, get_next_compra_folio, create_compra, update_compra,
    # Gestion de PI functions
    get_all_pis, get_pi_by_id, create_pi, update_pi, delete_pi, get_next_pi_folio,
    # Inventory movements functions
    apply_invoice_inventory_salida, has_invoice_been_applied, get_inventory_movements_by_invoice,
    get_refaccion_by_numero_parte, get_refaccion_with_stock,
    get_cotizacion_by_id, get_cotizacion_items,
    # Remisiones functions
    get_next_remision_folio, create_remision, get_remision_by_id, get_all_remisiones,
    update_remision, add_remision_item, get_remision_items, delete_remision_item,
    has_remision_been_confirmed, has_factura_remision_confirmed,
    apply_remision_inventory_salida, get_inventory_movements_by_remision,
    create_reserva,
    # OCU
    create_oc_cliente, create_ocu, add_ocu_item, get_ocu_by_id, set_deal_ocu_id,
    create_purchase_requisition, create_finance_request,
    get_finance_requests, update_finance_request_status,
    get_purchase_requisitions, update_purchase_requisition_status
)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from file_utils import save_attachment, validate_attachments, is_allowed_file, get_file_icon, format_file_size

# ===== Helpers para módulos CRM =====
def get_current_module(puesto):
    """
    Mapear puesto del usuario al módulo CRM correspondiente.
    
    Args:
        puesto: Puesto del usuario (ej: 'Vendedor', 'Contador', 'Compras')
    
    Returns:
        String con el módulo ('ventas', 'finanzas', 'compras', 'servicios', etc.)
    """
    if not puesto:
        return 'ventas'  # Default
    
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

# ===== Helpers para unidades y tipos de equipo =====
def _is_oilfree(tipo_equipo: str) -> bool:
    """True si el tipo de equipo contiene 'libre de aceite'."""
    return "libre de aceite" in (tipo_equipo or "").lower()

def _is_secador(tipo_equipo: str) -> bool:
    return tipo_equipo and "secador" in tipo_equipo.lower()

def _is_alta_presion(tipo_equipo: str) -> bool:
    return tipo_equipo and ("alta presión" in tipo_equipo.lower() or "alta presion" in tipo_equipo.lower())
    """True si el tipo de equipo es un secador."""
    return "secador" in (tipo_equipo or "").lower()

def _join_val_unit(val: str, unit: str) -> str:
    """
    Une valor y unidad como 'valor (unidad)'. Usa N/A si faltan.
    Si tu HTML no envía unidades, esto seguirá mostrando algo válido.
    """
    v = (val or "").strip() or "N/A"
    u = (unit or "").strip() or "N/A"
    return f"{v} ({u})"

# ===== Helpers para comparaciones case-insensitive =====
def compare_ignore_case(str1, str2):
    """Compara dos strings ignorando mayúsculas/minúsculas y espacios"""
    if str1 is None or str2 is None:
        return str1 == str2
    return str1.lower().strip() == str2.lower().strip()

def in_list_ignore_case(item, list_items):
    """Verifica si un item está en una lista ignorando mayúsculas/minúsculas"""
    if item is None:
        return False
    item_lower = item.lower().strip()
    return any(compare_ignore_case(item, list_item) for list_item in list_items)

# Rutas ya definidas en config.py si existe, sino usar locales
if 'DATA_DIR' not in globals():
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(APP_ROOT, "data")
    UPLOAD_DIR = os.path.join(APP_ROOT, "static", "uploads")
    FIRMAS_DIR = os.path.join(APP_ROOT, "static", "firmas")
    GENERADOS_DIR = os.path.join(APP_ROOT, "static")
else:
    # Ya vienen de config.py
    APP_ROOT = CONFIG_APP_ROOT

app = Flask(__name__)
# Usar SECRET_KEY de variable de entorno (Railway) o fallback a valor actual
app.secret_key = os.environ.get('SECRET_KEY', 'inair_secret_key_change_me')

# Initialize database
init_db()

# Make datetime available in all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Refresh user data on each request to keep permissions up-to-date
@app.before_request
def refresh_user_session():
    """Refresh user session data from database on each request"""
    if 'user' in session and 'user_id' in session:
        try:
            user = get_user_by_id(session['user_id'])
            if user:
                # Update session with latest data
                session['puesto'] = user.get('puesto', '')
                session['role'] = user.get('role', 'technician')
                session['user_nombre'] = user.get('nombre', '')
        except:
            pass  # If database query fails, keep existing session

# ------------------ Role-based access control ------------------
def require_role(role):
    """Decorator to require specific role for route access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            if session.get('role') != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ------------------ Permissions by Puesto ------------------
PUESTO_PERMISSIONS = {
    'Administrador': ['clientes', 'usuarios', 'historial', 'equipos', 'formulario', 'almacen', 'cotizaciones', 'crm', 'finanzas', 'compras', 'pi', 'pi_edit'],
    'Técnico de Servicio': ['formulario', 'crm'],
    'Vendedor': ['clientes', 'cotizaciones', 'crm', 'pi'],
    'Gerente de Ventas': ['clientes', 'cotizaciones', 'crm', 'historial', 'pi'],
    'Gerente de Servicios Técnicos': ['equipos', 'historial', 'crm', 'pi', 'formulario', 'cotizaciones', 'almacen'],
    'Cotizador': ['cotizaciones', 'clientes', 'crm', 'pi'],
    'Almacenista': ['almacen', 'pi'],
    'Contador': ['cotizaciones', 'historial', 'finanzas', 'crm', 'pi'],
    'Compras': ['compras', 'crm', 'cotizaciones', 'pi', 'pi_edit'],
    'Recursos Humanos': ['usuarios', 'pi'],
    'Director': ['clientes', 'usuarios', 'historial', 'equipos', 'almacen', 'cotizaciones', 'crm', 'finanzas', 'pi'],
}

def get_user_permissions():
    """Get list of permitted modules for current user"""
    if session.get('role') == 'admin':
        return ['clientes', 'usuarios', 'historial', 'equipos', 'formulario', 'almacen', 'cotizaciones', 'crm', 'finanzas', 'compras', 'pi', 'pi_edit']
    
    puesto = session.get('puesto', '')
    
    # First check the static dictionary
    if puesto in PUESTO_PERMISSIONS:
        return PUESTO_PERMISSIONS[puesto]
    
    # If not in static dict, check database for custom puestos
    try:
        puesto_data = get_puesto_by_nombre(puesto)
        if puesto_data and puesto_data.get('permisos'):
            return [p.strip() for p in puesto_data['permisos'].split(',') if p.strip()]
    except:
        pass
    
    return ['formulario']  # Default to formulario for unknown puestos

def has_permission(module):
    """Check if current user has permission for a module"""
    return module in get_user_permissions()

def require_permission(module):
    """Decorator to require specific module permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            if not has_permission(module):
                return redirect(url_for('dashboard_redirect'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ------------------ helpers de estado ------------------
def _load_json(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def cargar_usuarios():
    return _load_json(os.path.join(DATA_DIR, "usuarios.json"), {
        "fernando": {"password": "fernando123", "nombre": "Fernando", "prefijo":"F"},
        "cesar": {"password": "cesar123", "nombre": "César", "prefijo":"C"},
        "hiorvard": {"password": "hiorvard123", "nombre": "Hiorvard", "prefijo":"H"},
    })

def cargar_folios():
    return _load_json(os.path.join(DATA_DIR, "folios.json"), {})

def guardar_folios(data):
    with open(os.path.join(DATA_DIR, "folios.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generar_siguiente_folio(prefijo):
    folios = cargar_folios()
    folios[prefijo] = folios.get(prefijo, 0) + 1
    guardar_folios(folios)
    return f"{prefijo}-{folios[prefijo]:04d}"

# ------------------ catálogos ------------------
LISTA_EQUIPOS = [
    "Alta presión",
    "Compresor tornillo lubricado capacidad variable",
    "Compresor tornillo lubricado velocidad variable",
    "Compresor tornillo libre de aceite velocidad fija",
    "Compresor tornillo libre de aceite velocidad variable",
    "Compresor booster pistón 1 etapa",
    "Compresor booster pistón 2 etapas",
    "Compresor booster pistón 3 etapa",
    "Compresor booster pistón 4 etapa",
    "Compresor booster pistón 5 etapa",
    "Compresor tornillo lubricado velocidad fija",
    "Compresor pistón 3 etapas",
    "Compresor tornillo lubricado velocidad fija x bandas",
    "Compresor tornillo lubricado velocidad fija 2 etapas",
    "Compresor tornillo lubricado velocidad variable 2 etapas",
    "Compresor pistón 2 etapas",
    "Compresor reciprocante",
    "Secador refrigerativo cíclico",
    "Secador refrigerativo no cíclico",
    "Secador regenerativo",
]

ACTIVIDADES_SENTENCE = [
    "Cambio de filtro de aire","Cambio de filtro de aceite","Cambio de elemento separador",
    "Cambio de filtro panel control","Recuperar nivel de aceite","Cambio de aceite",
    "Cambio de mangueras","Cambio válvula de desfogue","Cambio válvula check descarga",
    "Cambio kit válvula mpcv","Cambio kit, válvula admisión","Cambio válvula paro de aceite",
    "Cambio kit, val. termocontrol","Cambio de bandas","Reapretar conexiones mecánicas",
    "Reapretar conexiones eléctricas","Limpieza línea de barrido","Limpieza trampa de condensados",
    "Limpieza a enfriadores aire/aceite","Revisar funcionamiento de válvulas",
    "Limpieza a platinos de contactores","Lubricación rodamiento de motor",
    "Servicio a motor eléctrico","Limpieza general del equipo",
    "Toma de muestra de aceite para análisis",
]

# --- Lecturas de compresor (web + pdf) ---
DG_LABELS = [
    "Horas totales","Horas de carga","Presión objetivo/descarga","Presión de carga",
    "Presión descarga del paquete","Temperatura ambiente","Temp. descarga del paquete",
    "Temp. descarga del aire-end","Temp. inyección de refrigerante","Caída de presión separador"
]
OF_LABELS = [
    "Temp. entrada aire 1ra etapa","Temp. descarga aire 1ra etapa","Presión descarga 1ra etapa",
    "Temp. entrada 2da etapa","Temp. descarga 2da etapa","Presión descarga 2da etapa",
    "Temperatura del aceite","Presión de aceite","Vacío de entrada","(otro)"
]

# --- Lecturas de SECADOR (solo PDF; en el HTML ya tienes estos campos) ---
SEC_LABELS = [
    "Temperatura de aire de entrada",
    "Temperatura de aire de salida",
    "Temperatura del calentador",
    "Temperatura ambiente",
    "Punto de rocío",
    "Tiempo de ciclo",
    "Horas totales",
    "Condiciones de prefiltro",
    "Condiciones de pos filtro",
]

# --- Datos eléctricos estándar (compresores) ---
E3 = [
    ("Voltaje comp. en carga","v_carga"),
    ("Voltaje comp. en descarga","v_descarga"),
    ("Voltaje a tierra","v_tierra"),
    ("Corriente comp. en carga","i_carga"),
    ("Corriente comp. en descarga","i_descarga"),
    ("Corriente total del paquete","i_total"),
]
E1 = [
    ("Corriente de placa","i_placa"),
    ("Voltaje del bus DC","v_busdc"),
    ("RPM del motor (VFD)","rpm_vfd"),
    ("Temp. IGBT U=","t_igbt_u"),("Temp. IGBT V=","t_igbt_v"),("Temp. IGBT W=","t_igbt_w"),
    ("Temp. rectificador","t_rect"),
]

# --- Datos eléctricos especiales para SECADOR (solo 2 filas, con prefijo sec_) ---
SEC_E3 = [
    ("Corriente en carga", "sec_i_carga"),
    ("Voltaje en carga", "sec_v_carga"),  # esta usa L1-2 / L2-3 / L3-1
]
SEC_E1 = []  # sin filas individuales para secador

# --- Lecturas de ALTA PRESIÓN ---
AP_LABELS = [
    "Horas de operación",
    "Presión de descarga del compresor",
    "Presión de carga del compresor",
    "Temperatura de entrada 1ra etapa",
    "Temperatura de descarga 1ra etapa",
    "Presión de descarga 1ra etapa",
    "Temperatura de entrada 2da etapa",
    "Temperatura de descarga 2da etapa",
    "Presión de descarga 2da etapa",
    "Temperatura de entrada 3ra etapa",
    "Temperatura de descarga 3ra etapa",
    "Presión de descarga 3a etapa",
]

# --- Datos eléctricos especiales para ALTA PRESIÓN (2 filas) ---
AP_E3 = [
    ("Voltaje", "ap_v"),
    ("Corriente de motor", "ap_i_motor"),
]
AP_E1 = []  # sin filas individuales para alta presión

# ------------------ rutas ------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Redirect based on role/puesto
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    elif session.get("puesto"):
        return redirect(url_for("user_dashboard"))
    else:
        return redirect(url_for("user_dashboard"))

@app.route("/dashboard")
def dashboard_redirect():
    """Redirects to appropriate dashboard based on user role"""
    if "user" not in session:
        return redirect(url_for("login"))
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("user_dashboard"))

@app.route("/user/dashboard")
def user_dashboard():
    """Dashboard for non-admin users with permission-based modules"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Refresh user data from database to get latest puesto/role
    user = get_user_by_username(session.get("user"))
    if user:
        session["puesto"] = user.get("puesto", "")
        session["role"] = user.get("role", "technician")
        session["user_nombre"] = user.get("nombre", "")
    
    permissions = get_user_permissions()
    return render_template("user_dashboard.html", permissions=permissions)

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username","").strip().lower()
        pw = request.form.get("password","").strip()
        
        # Get user from database
        user = get_user_by_username(username)
        
        if user and user["password"] == pw:
            session["user"] = username
            session["user_id"] = user["id"]
            session["user_nombre"] = user["nombre"]
            session["prefijo"] = user["prefijo"]
            session["role"] = user["role"]
            session["puesto"] = user.get("puesto", "")
            
            # Redirect based on role/puesto
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user.get("puesto"):
                # Users with puesto (including Technicians) go to dashboard
                return redirect(url_for("user_dashboard"))
            else:
                # Fallback for users without puesto (shouldn't happen for new users)
                return redirect(url_for("user_dashboard"))
        
        error = "Usuario o contraseña incorrectos"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/refresh-permissions")
def refresh_permissions():
    """Force refresh user permissions from database"""
    if 'user' not in session or 'user_id' not in session:
        return redirect(url_for("login"))
    
    try:
        user = get_user_by_id(session['user_id'])
        if user:
            # Update session with latest data
            session['puesto'] = user.get('puesto', '')
            session['role'] = user.get('role', 'technician')
            session['user_nombre'] = user.get('nombre', '')
            session.modified = True
            return redirect(url_for("user_dashboard"))
    except Exception as e:
        print(f"Error refreshing permissions: {e}")
    
    return redirect(url_for("user_dashboard"))

@app.route("/formulario")
def formulario():
    if "user" not in session:
        return redirect(url_for("login"))

    # ⬇️ Si viene ?folio=... en la URL, úsalo (no incrementa el contador)
    folio_q = request.args.get("folio", "").strip()
    if folio_q:
        session["folio_actual"] = folio_q

    # Si no hay folio en sesión, genera uno nuevo
    if "folio_actual" not in session:
        session["folio_actual"] = get_next_folio(session["prefijo"])

    folio = session["folio_actual"]
    return render_template(
        "formulario.html",
        folio=folio,
        lista_equipos=LISTA_EQUIPOS,
        dg_labels=DG_LABELS, of_labels=OF_LABELS, e3=E3, e1=E1
    )

@app.route("/nuevo_folio", methods=["POST"])
def nuevo_folio():
    if "user" not in session:
        return redirect(url_for("login"))
    session["folio_actual"] = get_next_folio(session["prefijo"])
    return redirect(url_for("formulario"))


# ------------------ util texto/medidas ------------------
def _text_or_na(v):
    v = (v or "").strip()
    return v if v else "N/A"

def _join_val_unit(value, unit):
    """Join a value with its unit. Returns 'N/A' if value is empty."""
    value = (value or "").strip()
    unit = (unit or "").strip()
    if not value or value == "N/A":
        return "N/A"
    if unit:
        return f"{value} {unit}"
    return value


def _wrap_text_force(text, max_w, font="Helvetica", size=9):
    if not text: return [""] if text == "" else []
    words = text.split(" ")
    lines, line = [], ""
    def w(s): return stringWidth(s, font, size)
    for word in words:
        cand = (line + " " + word).strip()
        if w(cand) <= max_w:
            line = cand
        else:
            if line: lines.append(line); line = ""
            buf = ""
            for ch in word:
                if w(buf + ch) <= max_w:
                    buf += ch
                else:
                    lines.append(buf); buf = ch
            line = buf
    if line: lines.append(line)
    return lines

# ------------------ dibujo piezas comunes ------------------
def _draw_header_and_footer(c, folio, fecha, tecnico, localidad):
    try:
        logo_path = os.path.join(APP_ROOT, "static", "img", "logo_inair.png")
        if os.path.exists(logo_path):
            c.drawImage(ImageReader(logo_path), 1.5*cm, 27.6*cm, width=4.2*cm, height=1.6*cm,
                        preserveAspectRatio=True, anchor='sw')
    except Exception:
        pass
    c.setFont("Helvetica-Bold", 14); c.drawString(7.5*cm, 28.1*cm, "REPORTE TÉCNICO")
    c.setFont("Helvetica", 9)
    c.drawRightString(16.5*cm, 28.2*cm, "Folio:")
    c.setFillColorRGB(0.82,0,0); c.setFont("Helvetica-Bold", 10)
    c.drawRightString(19.0*cm, 28.2*cm, folio)
    c.setFillColorRGB(0,0,0); c.setFont("Helvetica", 9)
    c.drawRightString(19.0*cm, 27.7*cm, f"Fecha: {fecha}")
    c.drawRightString(19.0*cm, 27.2*cm, f"Técnico: {tecnico}")
    c.drawString(1.5*cm, 27.2*cm, f"Localidad: {localidad}")
    c.setStrokeColorRGB(0.82,0.82,0.82); c.line(1.5*cm, 26.9*cm, 19.5*cm, 26.9*cm)
    c.setStrokeColorRGB(0,0,0)

    # Pie con fondo suave
    base_y = 1.35*cm
    rect_h = 1.9*cm
    c.setFillColorRGB(0.95, 0.96, 0.99)
    c.roundRect(1.5*cm, base_y-0.2*cm, 18.0*cm, rect_h, 6, fill=1, stroke=0)
    c.setStrokeColorRGB(0.75,0.75,0.8); c.roundRect(1.5*cm, base_y-0.2*cm, 18.0*cm, rect_h, 6, fill=0, stroke=1)
    c.setFillColorRGB(0,0,0)

    col_w = 8.8*cm; gap = 0.4*cm
    x1 = 1.7*cm; x2 = 1.7*cm + col_w + gap
    def draw_col(x, title, lines):
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, base_y + rect_h - 0.55*cm, title)
        c.setFont("Helvetica", 7.6)
        maxw = col_w - 0.2*cm
        yy = base_y + rect_h - 1.0*cm
        for ln in lines:
            for piece in _wrap_text_force(ln, maxw, "Helvetica", 7.6):
                c.drawString(x, yy, piece); yy -= 0.34*cm
    draw_col(x1, "INGENIERIA EN AIRE SA DE CV        RFC: IAI1605258G6",
             ["Avenida Alfonso Vidal y Planas #445, Interior S/N, Colonia Nueva Tijuana,",
              "Tijuana, Baja California, México, CP: 22435, Lada 664 Tel(s) 250-0022"])
    draw_col(x2, "INGENIERIA EN AIRE SA DE CV        RFC: IAI1605258G6",
             ["Avenida del Carmen #3863, Fracc. Residencias, Mexicali, Baja California, México,",
              "CP: 21280, Lada 686 Tel(s) 962-9932"])

def _draw_section(c, title, y, box_h):
    c.setStrokeColorRGB(0.7,0.7,0.7); c.setLineWidth(1)
    c.roundRect(1.5*cm, y-box_h, 18.0*cm, box_h, 6, stroke=1, fill=0)
    c.setFillColorRGB(0.95,0.95,0.98); c.rect(1.5*cm, y-18, 18.0*cm, 18, fill=1, stroke=0)
    c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold", 10); c.drawString(1.7*cm, y-13, title)
    return y-22

def _ensure_space(c, y, need, folio, fecha, tecnico, localidad):
    _, height = A4
    if y - need < 2.3*cm:
        c.showPage()
        _draw_header_and_footer(c, folio, fecha, tecnico, localidad)
        return height - 3.2*cm
    return y

def _row_box_multi(c, y, total_w, cols, line_h, inner_x):
    widths = [total_w * col["ratio"] for col in cols]
    for w, col in zip(widths, cols):
        lab = col["label"] + ": "
        lab_w = stringWidth(lab, "Helvetica-Bold", 9)
        avail = max(10, w - 8 - lab_w)
        parts = _wrap_text_force(col["value"], avail, "Helvetica", 9)
        col["_parts"], col["_lab_w"] = parts, lab_w
    max_lines = max(len(col["_parts"]) for col in cols)
    rect_h = max_lines*line_h + 0.40*cm
    c.setStrokeColorRGB(0.85,0.85,0.85)
    c.rect(inner_x-0.3*cm, y-rect_h+0.2*cm, total_w, rect_h, fill=0, stroke=1)
    c.setStrokeColorRGB(0,0,0)
    x = inner_x
    for w, col in zip(widths, cols):
        c.setFont("Helvetica-Bold", 9); c.drawString(x, y-0.3*cm, col["label"] + ": ")
        c.setFont("Helvetica", 9)
        yy = y-0.3*cm
        for i, ln in enumerate(col["_parts"]):
            if i == 0: c.drawString(x + col["_lab_w"], yy, ln)
            else:      c.drawString(x, yy - i*line_h, ln)
        x += w
    return y - rect_h

def _save_signature_png(data_url, filename):
    if not data_url or not data_url.startswith("data:image"): return None
    header, b64 = data_url.split(",", 1)
    raw = base64.b64decode(b64)
    os.makedirs(FIRMAS_DIR, exist_ok=True)
    path = os.path.join(FIRMAS_DIR, filename)
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        bg = Image.new("RGBA", img.size, (255,255,255,255))
        bg.alpha_composite(img)
        bg.convert("RGB").save(path, format="PNG")
    except Exception:
        with open(path, "wb") as f: f.write(raw)
    return path

# ------------------ generación PDF ------------------
@app.route("/generar_pdf", methods=["POST"])
def generar_pdf():
    if "user" not in session:
        return redirect(url_for("login"))

    width, height = A4
    folio = request.form.get("folio") or session.get("folio_actual")
    fecha = _text_or_na(request.form.get("fecha"))
    tecnico = _text_or_na(request.form.get("tecnico"))
    localidad = _text_or_na(request.form.get("localidad"))

    tipo_servicio = _text_or_na(request.form.get("tipo_servicio"))
    desc_servicio = _text_or_na(request.form.get("descripcion_servicio"))

    cliente = _text_or_na(request.form.get("cliente"))
    contacto = _text_or_na(request.form.get("contacto"))
    direccion = _text_or_na(request.form.get("direccion"))
    telefono = _text_or_na(request.form.get("telefono"))
    email = _text_or_na(request.form.get("email"))

    tipo_equipo = _text_or_na(request.form.get("tipo_equipo"))
    modelo = _text_or_na(request.form.get("modelo"))
    serie = _text_or_na(request.form.get("serie"))
    marca_sel = request.form.get("marca") or ""
    # Acepta "Otros" en cualquier capitalización
    if marca_sel.strip().lower() == "otros":
        marca = _text_or_na(request.form.get("otra_marca"))
    else:
        marca = _text_or_na(marca_sel)
    if marca and marca != "N/A":
        marca = marca.title()

    # Potencia: HP normal / CFM para secador
    potencia_num = (request.form.get("potencia", "") or "").strip()
    if potencia_num:
        if _is_secador(tipo_equipo):
            potencia = f"{potencia_num} CFM"
        else:
            potencia = f"{potencia_num} HP"
    else:
        potencia = "N/A"

    observaciones = _text_or_na(request.form.get("observaciones"))

    # fotos
    fotos = []
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    for i in range(1,5):
        ffile = request.files.get(f"foto{i}")
        desc = _text_or_na(request.form.get(f"foto{i}_desc"))
        path = os.path.join(UPLOAD_DIR, f"{folio}_foto{i}.png")
        
        if ffile and ffile.filename:
            # New file uploaded
            ffile.save(path)
            fotos.append((path, desc))
        else:
            # Check for auto-saved base64 data (foto#_data)
            foto_data = request.form.get(f"foto{i}_data")
            if not foto_data:
                # Fallback: check old field name
                foto_data = request.form.get(f"foto{i}_existing")
            
            if foto_data:
                try:
                    # Remove header if present (data:image/png;base64,...)
                    if "," in foto_data:
                        foto_data = foto_data.split(",")[1]
                    
                    with open(path, "wb") as f:
                        f.write(base64.b64decode(foto_data))
                    fotos.append((path, desc))
                except Exception as e:
                    print(f"Error decoding existing photo {i}: {e}")

    # firmas
    firma_tecnico_nombre = _text_or_na(request.form.get("firma_tecnico_nombre"))
    firma_cliente_nombre = _text_or_na(request.form.get("firma_cliente_nombre"))
    firma_tecnico_path = _save_signature_png(request.form.get("firma_tecnico_data"), f"{folio}_firma_tecnico.png")
    firma_cliente_path = _save_signature_png(request.form.get("firma_cliente_data"), f"{folio}_firma_cliente.png")

    # Bandera: ¿estamos en Preventivo/Bitácora + Secador o Alta Presión?
    ts = (tipo_servicio or "").lower()
    es_secador_preventivo = (_is_secador(tipo_equipo) and (ts == "preventivo" or ts in ("bitácora", "bitacora")))
    es_alta_presion_preventivo = (_is_alta_presion(tipo_equipo) and (ts == "preventivo" or ts in ("bitácora", "bitacora")))
    
    # actividades (para compresor estándar; en secador se usan otras actividades)
    analisis_ruido_marcado = request.form.get("act_analisis_ruido") == "1" or bool(request.form.get("act_analisis_ruido"))
    actividades = []
    
    # Si es secador preventivo, usar actividades específicas del secador
    if es_secador_preventivo:
        sec_actividades_map = [
            ("Revisión general del equipo", "act_sec_rev_general"),
            ("Reapriete de conexiones eléctricas", "act_sec_reapriete_electrico"),
            ("Reapriete de conexiones mecánicas", "act_sec_reapriete_mecanico"),
            ("Limpieza general del equipo", "act_sec_limpieza_general"),
            ("Cambio de prefiltro", "act_sec_cambio_prefiltro"),
            ("Cambio de pos filtro", "act_sec_cambio_posfiltro"),
            ("Cambio de válvulas", "act_sec_cambio_valvulas"),
        ]
        for nombre, campo in sec_actividades_map:
            val = request.form.get(campo)
            marcado = val == "1" or val == "on"
            actividades.append((nombre, "Realizado" if marcado else "N/A"))
        act_otras = _text_or_na(request.form.get("otras_actividades_secador"))
    else:
        # Actividades estándar para compresores
        for idx, nombre in enumerate(ACTIVIDADES_SENTENCE, start=1):
            # Check if checkbox is marked: value should be "1" or "on"
            val = request.form.get(f"act_{idx}")
            marcado = val == "1" or val == "on"
            actividades.append((nombre, "Realizado" if marcado else "N/A"))
        actividades.append(("Análisis de ruidos en rodamientos (R30)", "Realizado" if analisis_ruido_marcado else "N/A"))
        act_otras = _text_or_na(request.form.get("act_otras"))

    # ruido R30/SPM
    ruido_tipo = _text_or_na(request.form.get("ruido_tipo")) if analisis_ruido_marcado else "N/A"
    ruido_resultado = _text_or_na(request.form.get("ruido_resultado")) if analisis_ruido_marcado else "N/A"
    ruido_obs = _text_or_na(request.form.get("ruido_observaciones")) if analisis_ruido_marcado else "N/A"

    spm_vals = {}
    if analisis_ruido_marcado and ruido_tipo == "SPM":
        rows = [("carga_dbm","CARGA dBm"),("carga_dbc","CARGA dBc"),("carga_dbi","CARGA dBi"),
                ("descarga_dbm","DESCARGA dbm"),("descarga_dbc","DESCARGA dBc"),("descarga_dbi","DESCARGA dBi")]
        cols = ["mbrg","bg","lpmi_mri","lpm2_mr2","hpm1","hpm2","hpf1","hpf2","lpf1","lpf2"]
        for rk,_ in rows:
            for ck in cols:
                spm_vals[f"{rk}_{ck}"] = _text_or_na(request.form.get(f"{rk}_{ck}"))

    # Lecturas (compresor; para secador usaremos otros campos)
    dg_vals = []
    for i in range(len(DG_LABELS)):
        val = request.form.get(f"dg_{i+1}", "")
        unit = request.form.get(f"dg_{i+1}_unit", "")
        dg_vals.append(_join_val_unit(val, unit))

    # Oil-free
    of_vals = []
    for i in range(len(OF_LABELS)):
        val = request.form.get(f"of_{i+1}", "")
        unit = request.form.get(f"of_{i+1}_unit", "")
        of_vals.append(_join_val_unit(val, unit))

    # --- Datos eléctricos: E3 (trifásicos) y E1 (individuales) ---
    # Guardamos valores SIN unir con unidades aquí, se unirán en draw_electric
    e3_vals = {}
    e3_units = {}  # Guardamos también las unidades por separado
    for _, key in E3:
        fases = ("l12", "l23", "l31") if key in ("v_carga", "v_descarga") else ("l1", "l2", "l3")
        for ph in fases:
            val = request.form.get(f"{key}_{ph}", "").strip()
            unit = request.form.get(f"{key}_{ph}_u", "").strip()
            # Guardamos solo el valor, sin la unidad (vacío si no hay valor)
            e3_vals[f"{key}_{ph}"] = val if val else ""
            e3_units[f"{key}_{ph}"] = unit

    e1_vals = {}
    for _, key in E1:
        val = request.form.get(key)
        unit = request.form.get(f"{key}_u", "")
        e1_vals[key] = _join_val_unit(val, unit)

    # Bandera: ¿estamos en Preventivo/Bitácora + Secador o Alta Presión?
    ts = (tipo_servicio or "").lower()
    es_secador_preventivo = (_is_secador(tipo_equipo) and (ts == "preventivo" or ts in ("bitácora", "bitacora")))
    es_alta_presion_preventivo = (_is_alta_presion(tipo_equipo) and (ts == "preventivo" or ts in ("bitácora", "bitacora")))
    
    # --- Datos eléctricos para ALTA PRESIÓN ---
    ap_e3_vals = {}
    if es_alta_presion_preventivo:
        # Voltaje: l12, l23, l31 (sin unir con unidad aquí, se hará en draw_electric)
        for ph in ("l12", "l23", "l31"):
            val = request.form.get(f"ap_v_{ph}", "")
            ap_e3_vals[f"ap_v_{ph}"] = val
        # Corriente de motor: l1, l2, l3
        for ph in ("l1", "l2", "l3"):
            val = request.form.get(f"ap_i_motor_{ph}", "")
            ap_e3_vals[f"ap_i_motor_{ph}"] = val
    
    # --- Datos eléctricos para SECADOR (con prefijo sec_ para evitar conflicto con compresor) ---
    sec_e3_vals = {}
    if es_secador_preventivo:
        # Corriente comp. en carga: l1, l2, l3 (con prefijo sec_)
        for ph in ("l1", "l2", "l3"):
            val = request.form.get(f"sec_i_carga_{ph}", "").strip()
            sec_e3_vals[f"sec_i_carga_{ph}"] = val if val else ""
        # Voltaje comp. en carga: l12, l23, l31 (con prefijo sec_)
        for ph in ("l12", "l23", "l31"):
            val = request.form.get(f"sec_v_carga_{ph}", "").strip()
            sec_e3_vals[f"sec_v_carga_{ph}"] = val if val else ""
        # DEBUG: Verificar que se están capturando los datos
        print(f"[DEBUG SECADOR] sec_e3_vals: {sec_e3_vals}")

    # === PDF ===
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _draw_header_and_footer(c, folio, fecha, tecnico, localidad)
    y = height - 3.2*cm
    inner_x = 1.8*cm
    inner_w = 17.6*cm
    line_h = 0.52*cm

    # DATOS DEL CLIENTE
    need = 18 + (1*line_h) + 0.8*cm
    y = _ensure_space(c, y, need, folio, fecha, tecnico, localidad)
    yc = _draw_section(c, "Datos del cliente", y, need + (2*line_h))
    yc = _row_box_multi(c, yc, inner_w, [{"label":"Cliente","value":cliente,"ratio":1.0}], line_h, inner_x)
    cols = [
        {"label":"Contacto","value":contacto,"ratio":0.45},
        {"label":"Teléfono","value":telefono,"ratio":0.22},
        {"label":"Email","value":email,"ratio":0.33},
    ]
    yc = _row_box_multi(c, yc, inner_w, cols, line_h, inner_x)
    yc = _row_box_multi(c, yc, inner_w, [{"label":"Dirección","value":direccion,"ratio":1.0}], line_h, inner_x)
    y = yc - 0.2*cm

    # SERVICIO (si el tipo es Bitácora, aseguramos la descripción)
    if ts in ("bitácora", "bitacora"):
        desc_servicio = "Bitácora"

    cols = [{"label":"Tipo","value":tipo_servicio,"ratio":0.30},{"label":"Descripción","value":desc_servicio,"ratio":0.70}]
    max_lines = 0
    for col in cols:
        w = inner_w*col["ratio"]; lab_w = stringWidth(col["label"]+": ", "Helvetica-Bold", 9)
        avail = max(10, w - lab_w - 8)
        parts = _wrap_text_force(col["value"], avail, "Helvetica", 9)
        max_lines = max(max_lines, len(parts))
    need_serv = 18 + max_lines*line_h + 0.8*cm
    y = _ensure_space(c, y, need_serv, folio, fecha, tecnico, localidad)
    ys = _draw_section(c, "Servicio", y, need_serv)
    ys = _row_box_multi(c, ys, inner_w, cols, line_h, inner_x)
    y = ys - 0.2*cm

    # EQUIPO
    need_eq = 18 + 1*line_h + 0.8*cm
    y = _ensure_space(c, y, need_eq + 2*line_h, folio, fecha, tecnico, localidad)
    ye = _draw_section(c, "Datos del equipo", y, need_eq + 2*line_h)
    ye = _row_box_multi(c, ye, inner_w, [{"label":"Tipo","value":tipo_equipo,"ratio":1.0}], line_h, inner_x)
    cols = [
        {"label":"Modelo","value":modelo,"ratio":0.25},
        {"label":"Serie","value":serie,"ratio":0.25},
        {"label":"Marca","value":marca,"ratio":0.25},
        {"label":"Potencia","value":potencia,"ratio":0.25},
    ]
    ye = _row_box_multi(c, ye, inner_w, cols, line_h, inner_x)
    y = ye - 0.2*cm

    # ===== Flujo por tipo de servicio =====
    if ts == "preventivo":
        # OJO: aquí sigues viendo la tabla de actividades estándar solo para compresores.
        # Para secadores tú ya tienes el bloque de actividades específico en el formulario
        # y podríamos hacer una tabla aparte si lo necesitas después.
        
        # Filter out activities where estado is "N/A" (not performed)
        filtered_actividades = [(act, est) for act, est in actividades if est and est.strip() and est.strip() != "N/A"]
        
        if not filtered_actividades:
            # Skip this section if no activities were performed
            pass
        else:
            rows = filtered_actividades[:]
            n = len(rows); left_rows = math.ceil(n/2); right_rows = n - left_rows
            row_h = 0.52*cm; gutter = 0.6*cm; col_w_act = 5.9*cm; col_w_estado = 2.0*cm
            need_h = 18 + (1 + max(left_rows, right_rows))*row_h + 1.2*cm
            otras_text = "" if act_otras == "N/A" else act_otras
            if otras_text:
                lab = "OTRAS ACTIVIDADES: "; labw = stringWidth(lab, "Helvetica-Bold", 9)
                otras_lines = _wrap_text_force(otras_text, inner_w-0.6*cm-labw-6, "Helvetica", 9)
                need_h += (len(otras_lines)*line_h + 0.8*cm + 16)
            y = _ensure_space(c, y, need_h, folio, fecha, tecnico, localidad)
            ya = _draw_section(c, "Actividades de mantenimiento preventivo", y, need_h)
            left_x = inner_x; right_x = left_x + (col_w_act + col_w_estado) + gutter
            c.setFont("Helvetica-Bold", 8.4)
            for base_x in (left_x, right_x):
                c.rect(base_x, ya-row_h, col_w_act, row_h, fill=0, stroke=1)
                c.rect(base_x+col_w_act, ya-row_h, col_w_estado, row_h, fill=0, stroke=1)
                c.drawString(base_x+3, ya-row_h+3, "Actividad")
                c.drawString(base_x+col_w_act+3, ya-row_h+3, "Estado")
            c.setFont("Helvetica", 7.8)
            yline_l = ya - row_h
            for i in range(left_rows):
                # Check space before each row (except first)
                if i > 0:
                    temp_y = yline_l
                    temp_y = _ensure_space(c, temp_y, row_h + 0.1*cm, folio, fecha, tecnico, localidad)
                    if temp_y > yline_l:
                        yline_l = temp_y
                
                act, est = rows[i]
                c.rect(left_x, yline_l-row_h, col_w_act, row_h, fill=0, stroke=1)
                c.rect(left_x+col_w_act, yline_l-row_h, col_w_estado, row_h, fill=0, stroke=1)
                maxw = col_w_act - 6; txt = act
                while stringWidth(txt, "Helvetica", 7.8) > maxw and len(txt) > 3:
                    txt = txt[:-4] + "…"
                c.drawString(left_x+3, yline_l-row_h+3, txt)
                c.drawString(left_x+col_w_act+3, yline_l-row_h+3, est)
                yline_l -= row_h
            yline_r = ya - row_h
            for j in range(right_rows):
                # Check space before each row (except first)
                if j > 0:
                    temp_y = yline_r
                    temp_y = _ensure_space(c, temp_y, row_h + 0.1*cm, folio, fecha, tecnico, localidad)
                    if temp_y > yline_r:
                        yline_r = temp_y
                
                act, est = rows[left_rows + j]
                c.rect(right_x, yline_r-row_h, col_w_act, row_h, fill=0, stroke=1)
                c.rect(right_x+col_w_act, yline_r-row_h, col_w_estado, row_h, fill=0, stroke=1)
                maxw = col_w_act - 6; txt = act
                while stringWidth(txt, "Helvetica", 7.8) > maxw and len(txt) > 3:
                    txt = txt[:-4] + "…"
                c.drawString(right_x+3, yline_r-row_h+3, txt)
                c.drawString(right_x+col_w_act+3, yline_r-row_h+3, est)
                yline_r -= row_h
            y_after = min(yline_l, yline_r) - 0.3*cm
            if otras_text:
                c.setFont("Helvetica-Bold", 9); lab = "OTRAS ACTIVIDADES: "
                labw = stringWidth(lab, "Helvetica-Bold", 9)
                parts = _wrap_text_force(otras_text, inner_w-0.6*cm-labw-6, "Helvetica", 9)
                rect_h = len(parts)*line_h + 0.8*cm
                c.setStrokeColorRGB(0.85,0.85,0.85)
                c.rect(inner_x-0.3*cm, y_after-rect_h+0.2*cm, inner_w, rect_h, fill=0, stroke=1)
                c.setStrokeColorRGB(0,0,0)
                yy = y_after - 0.3*cm; c.drawString(inner_x, yy, lab)
                c.setFont("Helvetica", 9)
                for i, ln in enumerate(parts):
                    c.drawString(inner_x + labw + 6, yy - i*line_h, ln)
                y = y_after - rect_h - 0.2*cm
            else:
                y = y_after

        # análisis de ruido
        if analisis_ruido_marcado:
            if ruido_tipo == "SPM":
                need_spm = 7.6*cm
                y = _ensure_space(c, y, need_spm, folio, fecha, tecnico, localidad)
                yr = _draw_section(c, "Análisis de ruido", y, need_spm)
                headers = ["", "MBRG","BG","LPMI-MRI","LPM2-MR2","HPM1","HPM2","HPF1","HPF2","LPF1","LPF2"]
                row_defs = [("CARGA dBm","carga_dbm"),("CARGA dBc","carga_dbc"),("CARGA dBi","carga_dbi"),
                            ("DESCARGA dbm","descarga_dbm"),("DESCARGA dBc","descarga_dbc"),("DESCARGA dBi","descarga_dbi")]
                
                # Filter out rows where all values are N/A or empty
                cols = ["mbrg","bg","lpmi_mri","lpm2_mr2","hpm1","hpm2","hpf1","hpf2","lpf1","lpf2"]
                filtered_row_defs = []
                for lbl, key in row_defs:
                    row_vals = [spm_vals.get(f"{key}_{col}", "N/A") for col in cols]
                    # Keep row if at least one value is not N/A and not empty
                    if any(v and v.strip() and v.strip() != "N/A" for v in row_vals):
                        filtered_row_defs.append((lbl, key))
                
                if filtered_row_defs:
                    # Only draw table if there are rows with data
                    left_x2 = inner_x; colw0 = 3.4*cm; colw = 1.45*cm; rh = 0.68*cm
                    c.setFont("Helvetica-Bold", 8); c.setStrokeColorRGB(0.7,0.7,0.7)
                    c.rect(left_x2, yr-rh, colw0 + 10*colw, rh, fill=0, stroke=1)
                    c.drawString(left_x2+2, yr-rh+3, "ANÁLISIS DE RUIDO EN RODAMIENTOS (SPM)")
                    yline = yr - rh; x = left_x2 + colw0
                    c.setFont("Helvetica-Bold", 7.2)
                    for h in headers[1:]:
                        c.rect(x, yline-rh, colw, rh, fill=0, stroke=1); c.drawString(x+2, yline-rh+3, h); x += colw
                    yy2 = yline - rh; c.setFont("Helvetica", 7.0)
                    for idx, (lbl, key) in enumerate(filtered_row_defs):
                        # Check space before each row (except first, already checked for header)
                        if idx > 0:
                            temp_y = yy2
                            temp_y = _ensure_space(c, temp_y, rh + 0.1*cm, folio, fecha, tecnico, localidad)
                            if temp_y > yy2:
                                yy2 = temp_y
                        
                        c.rect(left_x2, yy2-rh, colw0, rh, fill=0, stroke=1)
                        c.setFont("Helvetica-Bold", 8); c.drawString(left_x2+2, yy2-rh+3, lbl)
                        x = left_x2 + colw0; c.setFont("Helvetica", 7.0)
                        for col in cols:
                            val = spm_vals.get(f"{key}_{col}", "N/A")
                            c.rect(x, yy2-rh, colw, rh, fill=0, stroke=1); c.drawString(x+2, yy2-rh+3, val[:8]); x += colw
                        yy2 -= rh
                    c.setStrokeColorRGB(0,0,0); y = yy2 - 0.3*cm
            else:
                need_r30 = 2.6*cm
                y = _ensure_space(c, y, need_r30, folio, fecha, tecnico, localidad)
                yr = _draw_section(c, "Análisis de ruido", y, need_r30)
                c.setFont("Helvetica-Bold", 9); c.drawString(inner_x, yr-0.7*cm, "Tipo:")
                c.setFont("Helvetica", 9); c.drawString(inner_x + stringWidth("Tipo:", "Helvetica-Bold", 9) + 6, yr-0.7*cm, ruido_tipo)
                c.setFont("Helvetica-Bold", 9); c.drawString(inner_x, yr-1.3*cm, "Resultado:")
                c.setFont("Helvetica", 9); c.drawString(inner_x + stringWidth("Resultado:", "Helvetica-Bold", 9) + 6, yr-1.3*cm, ruido_resultado)
                c.setFont("Helvetica-Bold", 9); c.drawString(inner_x, yr-1.9*cm, "Observaciones:")
                c.setFont("Helvetica", 9); c.drawString(inner_x + stringWidth("Observaciones:", "Helvetica-Bold", 9) + 6, yr-1.9*cm, ruido_obs)
                y = yr - 2.2*cm

    elif ts in ("correctivo", "diagnóstico", "diagnostico", "revisión", "revision"):
        blocks = [
            ("Diagnóstico del problema", _text_or_na(request.form.get("diag_problema"))),
            ("Causa raíz", _text_or_na(request.form.get("causa_raiz"))),
            ("Actividades realizadas", _text_or_na(request.form.get("actividades_realizadas"))),
            ("Refacciones utilizadas", _text_or_na(request.form.get("refacciones"))),
            ("Condiciones en que se encontró el equipo", _text_or_na(request.form.get("cond_encontro"))),
            ("Condiciones en que se entrega el equipo", _text_or_na(request.form.get("cond_entrega"))),
        ]
        for title, content in blocks:
            lines = _wrap_text_force(content, inner_w-0.6*cm)
            need = 18 + len(lines)*line_h + 0.8*cm
            y = _ensure_space(c, y, need, folio, fecha, tecnico, localidad)
            yb = _draw_section(c, title, y, need)
            c.setFont("Helvetica", 9)
            yy = yb - 0.5*cm
            for i, ln in enumerate(lines):
                c.drawString(inner_x, yy - i*line_h, ln)
            y = yy - len(lines)*line_h - 0.4*cm

    elif ts in ("bitácora", "bitacora"):
        # Bitácora: no pintamos preventivo/correctivo aquí
        pass

    # ===== LECTURAS DEL EQUIPO =====
    def draw_kv_table(title, labels, values):
        nonlocal y
        # Filter out rows where value is empty or "N/A"
        filtered_rows = [(lab, val) for lab, val in zip(labels, values) if val and val.strip() and val.strip() != "N/A"]
        
        if not filtered_rows:
            return  # Don't draw the table if no data
        
        row_h = 0.52*cm
        need = 18 + len(filtered_rows)*row_h + 0.7*cm
        y = _ensure_space(c, y, need, folio, fecha, tecnico, localidad)
        yt = _draw_section(c, title, y, need)
        c.setFont("Helvetica-Bold", 8.7)
        lab_w = 10.8*cm
        val_w = inner_w - lab_w
        yline = yt - 0.25*cm
        c.setFont("Helvetica", 8.7)
        for i,(lab,val) in enumerate(filtered_rows):
            # Check space before drawing each row (except first, already checked)
            if i > 0:
                # Check if we need to move to a new page
                temp_y = yline
                temp_y = _ensure_space(c, temp_y, row_h + 0.15*cm, folio, fecha, tecnico, localidad)
                # If new page was created, update yline to new page position
                if temp_y > yline:
                    yline = temp_y
            
            c.setStrokeColorRGB(0.85,0.85,0.85)
            c.rect(inner_x-0.3*cm, yline-row_h, lab_w+val_w, row_h, fill=0, stroke=1)
            c.setStrokeColorRGB(0,0,0)
            c.setFont("Helvetica", 8.6)
            c.drawString(inner_x, yline-row_h+3, lab)
            c.setFont("Helvetica-Bold", 8.6)
            c.drawString(inner_x + lab_w, yline-row_h+3, val)
            yline -= row_h
        y = yline - 0.2*cm

    if es_alta_presion_preventivo:
        # Leemos campos específicos de ALTA PRESIÓN
        ap_vals = []
        ap_fields = [
            "ap_horas_operacion", "ap_presion_descarga_compresor", "ap_presion_carga_compresor",
            "ap_temp_entrada_1ra", "ap_temp_descarga_1ra", "ap_presion_descarga_1ra",
            "ap_temp_entrada_2da", "ap_temp_descarga_2da", "ap_presion_descarga_2da",
            "ap_temp_entrada_3ra", "ap_temp_descarga_3ra", "ap_presion_descarga_3a"
        ]
        for field in ap_fields:
            val = request.form.get(field, "")
            unit = request.form.get(f"{field}_unit", "")
            ap_vals.append(_join_val_unit(val, unit))
        
        draw_kv_table("Lecturas del equipo (Alta presión)", AP_LABELS, ap_vals)
    elif es_secador_preventivo:
        # Leemos campos específicos del SECADOR (los nombres deben coincidir con tu HTML)
        sec_vals = []
        # 1. Temperatura de aire de entrada
        val = request.form.get("sec_temp_aire_entrada", "")
        unit = request.form.get("sec_temp_aire_entrada_u", "")
        sec_vals.append(_join_val_unit(val, unit))
        # 2. Temperatura de aire de salida
        val = request.form.get("sec_temp_aire_salida", "")
        unit = request.form.get("sec_temp_aire_salida_u", "")
        sec_vals.append(_join_val_unit(val, unit))
        # 3. Temperatura del calentador
        val = request.form.get("sec_temp_calentador", "")
        unit = request.form.get("sec_temp_calentador_u", "")
        sec_vals.append(_join_val_unit(val, unit))
        # 4. Temperatura ambiente
        val = request.form.get("sec_temp_ambiente", "")
        unit = request.form.get("sec_temp_ambiente_u", "")
        sec_vals.append(_join_val_unit(val, unit))
        # 5. Punto de rocío
        val = request.form.get("sec_punto_rocio", "")
        unit = request.form.get("sec_punto_rocio_u", "")
        sec_vals.append(_join_val_unit(val, unit))
        # 6. Tiempo de ciclo (sin unidad)
        val = request.form.get("sec_tiempo_ciclo", "")
        sec_vals.append(val if val else "N/A")
        # 7. Horas totales
        val = request.form.get("sec_horas_totales", "")
        unit = request.form.get("sec_horas_totales_u", "")
        sec_vals.append(_join_val_unit(val, unit))
        # 8. Condiciones de prefiltro
        sec_pref = _text_or_na(request.form.get("sec_condicion_prefiltro"))
        sec_vals.append(sec_pref)
        # 9. Condiciones de pos filtro
        sec_pos = _text_or_na(request.form.get("sec_condicion_posfiltro"))
        sec_vals.append(sec_pos)

        draw_kv_table("Lecturas del equipo (Secador)", SEC_LABELS, sec_vals)
    else:
        draw_kv_table("Lecturas del equipo", DG_LABELS, dg_vals)
        if _is_oilfree(tipo_equipo):
            draw_kv_table("Compresor (oil free)", OF_LABELS, of_vals)

    # ===== DATOS ELÉCTRICOS =====
    def draw_electric(e3_vals_map, e1_vals_map, e3_rows, e1_rows, e3_units_map=None):
        nonlocal y
        row_h = 0.52*cm
        # Si no se proporciona e3_units_map, usar request.form como fallback
        if e3_units_map is None:
            e3_units_map = {}
        
        # Filter e3_rows: keep only rows where at least one phase has data
        filtered_e3 = []
        for titulo, key in e3_rows:
            # Para Alta Presión, los nombres de campos son diferentes
            if key == "ap_v":
                # Voltaje: l12, l23, l31
                fases = ("l12", "l23", "l31")
                units = [
                    request.form.get("ap_v_l12_u", "").strip(),
                    request.form.get("ap_v_l23_u", "").strip(),
                    request.form.get("ap_v_l31_u", "").strip()
                ]
                vals_raw = [e3_vals_map.get(f"ap_v_{ph}", "N/A") for ph in fases]
            elif key == "ap_i_motor":
                # Corriente de motor: l1, l2, l3
                fases = ("l1", "l2", "l3")
                units = [
                    request.form.get("ap_i_motor_l1_u", "").strip(),
                    request.form.get("ap_i_motor_l2_u", "").strip(),
                    request.form.get("ap_i_motor_l3_u", "").strip()
                ]
                vals_raw = [e3_vals_map.get(f"ap_i_motor_{ph}", "N/A") for ph in fases]
            elif key == "sec_i_carga":
                # Corriente comp. en carga para SECADOR: l1, l2, l3 (con prefijo sec_)
                fases = ("l1", "l2", "l3")
                units = [
                    request.form.get("sec_i_carga_l1_u", "").strip(),
                    request.form.get("sec_i_carga_l2_u", "").strip(),
                    request.form.get("sec_i_carga_l3_u", "").strip()
                ]
                # Intentar obtener valores del mapa primero, luego de request.form
                vals_raw = []
                for ph in fases:
                    val = e3_vals_map.get(f"sec_i_carga_{ph}", "")
                    if not val or val == "":
                        val = request.form.get(f"sec_i_carga_{ph}", "").strip()
                    vals_raw.append(val)
                print(f"[DEBUG SECADOR] sec_i_carga - vals_raw: {vals_raw}, units: {units}")
            elif key == "sec_v_carga":
                # Voltaje comp. en carga para SECADOR: l12, l23, l31 (con prefijo sec_)
                fases = ("l12", "l23", "l31")
                units = [
                    request.form.get("sec_v_carga_l12_u", "").strip(),
                    request.form.get("sec_v_carga_l23_u", "").strip(),
                    request.form.get("sec_v_carga_l31_u", "").strip()
                ]
                # Intentar obtener valores del mapa primero, luego de request.form
                vals_raw = []
                for ph in fases:
                    val = e3_vals_map.get(f"sec_v_carga_{ph}", "")
                    if not val or val == "":
                        val = request.form.get(f"sec_v_carga_{ph}", "").strip()
                    vals_raw.append(val)
                print(f"[DEBUG SECADOR] sec_v_carga - vals_raw: {vals_raw}, units: {units}")
            else:
                # Lógica estándar para otros equipos (compresores y secadores)
                # Los campos en el HTML son: {key}_l1_u, {key}_l2_u, {key}_l3_u para corriente
                # y {key}_l12_u, {key}_l23_u, {key}_l31_u para voltaje
                fases = ("l12","l23","l31") if key in ("v_carga", "v_descarga") else ("l1","l2","l3")
                units = []
                for ph in fases:
                    # Intentar obtener la unidad del mapa, si no, de request.form
                    unit_key = f"{key}_{ph}"
                    if e3_units_map and unit_key in e3_units_map:
                        unit = e3_units_map[unit_key].strip()
                    else:
                        unit = request.form.get(f"{key}_{ph}_u", "").strip()
                    units.append(unit)
                
                # Obtener valores directamente desde e3_vals_map (ya están sin unidades)
                vals_raw = [e3_vals_map.get(f"{key}_{ph}", "") for ph in fases]
            
            # Check if at least one value is not empty
            # Para secador y alta presión, verificar que los valores no estén vacíos
            # Convertir "N/A" a string vacío para la verificación
            vals_clean = [v if v and v != "N/A" else "" for v in vals_raw]
            has_data = any(v and v.strip() for v in vals_clean)
            if has_data:
                # Join each value with its unit
                vals_with_units = [_join_val_unit(v if v != "N/A" else "", u) for v, u in zip(vals_raw, units)]
                filtered_e3.append((titulo, vals_with_units))
        
        # Filter e1_rows: keep only rows with data
        filtered_e1 = []
        for titulo, key in e1_rows:
            unit = request.form.get(f"{key}_unit", "").strip()
            val_raw = e1_vals_map.get(key, "N/A")
            if val_raw and val_raw.strip() and val_raw.strip() != "N/A":
                val_with_unit = _join_val_unit(val_raw, unit)
                filtered_e1.append((titulo, val_with_unit))
        
        if not filtered_e3 and not filtered_e1:
            return  # Don't draw section if no data
        
        # Calcular el espacio total necesario:
        # - Encabezado de sección: 22 puntos (retornado por _draw_section)
        # - Espacio superior después del encabezado: 0.25*cm
        # - Encabezado "MEDICIÓN": 1 row_h
        # - Filas de datos: (len(filtered_e3) + len(filtered_e1)) * row_h
        # - Espacio inferior: 0.2*cm
        # - Margen adicional: 0.9*cm
        total_rows = 1 + len(filtered_e3) + len(filtered_e1)  # 1 para encabezado MEDICIÓN
        need = 22 + 0.25*cm + total_rows*row_h + 0.2*cm + 0.9*cm
        
        # Verificar que TODO el espacio esté disponible ANTES de empezar a dibujar
        y = _ensure_space(c, y, need, folio, fecha, tecnico, localidad)
        ye = _draw_section(c, "Datos eléctricos", y, need)

        c.setFont("Helvetica-Bold", 8.7)
        x0 = inner_x-0.3*cm; lab_w = 7.6*cm; cell = 3.1*cm
        yline = ye - 0.25*cm

        # Encabezado
        c.rect(x0, yline-row_h, lab_w+3*cell, row_h, fill=0, stroke=1)
        c.drawString(x0+2, yline-row_h+3, "MEDICIÓN")
        c.drawString(x0+lab_w+2,        yline-row_h+3, "L1 / L1-2")
        c.drawString(x0+lab_w+cell+2,   yline-row_h+3, "L2 / L2-3")
        c.drawString(x0+lab_w+2*cell+2, yline-row_h+3, "L3 / L3-1")
        yline -= row_h

        c.setFont("Helvetica", 8.6)

        # Trifásicos - ya verificamos el espacio completo, solo dibujamos
        for idx, (titulo, vals) in enumerate(filtered_e3):
            c.rect(x0, yline-row_h, lab_w, row_h, fill=0, stroke=1)
            c.drawString(x0+2, yline-row_h+3, titulo)

            for j, val in enumerate(vals):
                c.rect(x0+lab_w+j*cell, yline-row_h, cell, row_h, fill=0, stroke=1)
                c.drawString(x0+lab_w+j*cell+2, yline-row_h+3, val)
            yline -= row_h

        # Individuales - ya verificamos el espacio completo, solo dibujamos
        for idx, (titulo, val) in enumerate(filtered_e1):
            c.rect(x0, yline-row_h, lab_w+3*cell, row_h, fill=0, stroke=1)
            c.drawString(x0+2, yline-row_h+3, titulo)
            c.setFont("Helvetica-Bold", 8.6)
            c.drawRightString(x0+lab_w+3*cell-4, yline-row_h+3, val)
            c.setFont("Helvetica", 8.6)
            yline -= row_h

        y = yline - 0.2*cm

    if es_alta_presion_preventivo:
        # Solo Voltaje y Corriente de motor para Alta Presión
        draw_electric(ap_e3_vals, {}, AP_E3, AP_E1)
    elif es_secador_preventivo:
        # Solo Corriente comp. en carga (L1,L2,L3) y Voltaje comp. en carga (L1-2,L2-3,L3-1)
        # Usar sec_e3_vals en lugar de e3_vals para asegurar que solo tenga los campos del secador
        draw_electric(sec_e3_vals, e1_vals, SEC_E3, SEC_E1)
    else:
        draw_electric(e3_vals, e1_vals, E3, E1, e3_units)

    # OBSERVACIONES
    obs_lines = _wrap_text_force(observaciones, inner_w-0.6*cm)
    need_obs = 18 + len(obs_lines)*line_h + 0.9*cm
    y = _ensure_space(c, y, need_obs, folio, fecha, tecnico, localidad)
    yo = _draw_section(c, "Observaciones y recomendaciones", y, need_obs)
    c.setFont("Helvetica", 9)
    yy = yo - 0.55*cm
    for i, ln in enumerate(obs_lines):
        c.drawString(inner_x, yy - i*line_h, ln)
    y = yy - len(obs_lines)*line_h - 0.4*cm

    # FOTOS
    def draw_fotos(items):
        nonlocal y
        if not items:
            return

        gutter_col = 0.9*cm
        col_w = (inner_w - gutter_col) / 2.0
        img_w = col_w
        img_h = img_w * 0.70
        caption_h = 1.10*cm
        row_gap = 0.6*cm
        per_row_h = img_h + caption_h + row_gap

        idx = 0
        foto_num = 1

        def ellipsize(text, maxw):
            s = (text or "N/A").strip() or "N/A"
            while stringWidth(s, "Helvetica", 8.2) > maxw and len(s) > 3:
                s = s[:-2] + "…"
            return s

        while idx < len(items):
            disponible = y - 2.3*cm
            max_rows_fit = int((disponible - (18 + 0.8*cm)) // per_row_h)
            if max_rows_fit < 1:
                c.showPage(); _draw_header_and_footer(c, folio, fecha, tecnico, localidad)
                y = height - 3.2*cm
                continue

            rem_rows = math.ceil((len(items) - idx)/2)
            rows = min(max_rows_fit, rem_rows)
            need_here = 18 + rows*per_row_h + 0.8*cm
            yf = _draw_section(c, "Evidencias fotográficas", y, need_here)

            left_x = inner_x
            right_x = inner_x + col_w + gutter_col
            top = yf - 0.5*cm

            def draw_one(path, desc, x, ytop, num):
                c.rect(x, ytop - img_h, img_w, img_h, stroke=1, fill=0)
                if path and os.path.exists(path):
                    try:
                        c.drawImage(ImageReader(path), x, ytop - img_h, width=img_w, height=img_h,
                                    preserveAspectRatio=True, anchor='sw')
                    except Exception:
                        pass
                c.setFont("Helvetica", 8.2)
                maxw = img_w - 6
                lines = _wrap_text_force(desc or "N/A", maxw, "Helvetica", 8.2)
                line1 = ellipsize(lines[0] if lines else "N/A", maxw)
                line2 = ellipsize(lines[1] if len(lines) > 1 else "", maxw)
                base = ytop - img_h - 0.32*cm
                c.drawString(x, base, f"Foto {num}: {line1}")
                if line2:
                    c.drawString(x, base - 0.34*cm, line2)

            for r in range(rows):
                if idx < len(items):
                    p, d = items[idx]; idx += 1
                    draw_one(p, d, left_x, top - r*per_row_h, foto_num); foto_num += 1
                if idx < len(items):
                    p, d = items[idx]; idx += 1
                    draw_one(p, d, right_x, top - r*per_row_h, foto_num); foto_num += 1

            y = yf - rows*per_row_h - 0.3*cm

    # Si es Bitácora, limitamos a 2 fotos
    if ts in ("bitácora", "bitacora"):
        fotos = fotos[:2]
    draw_fotos(fotos)

    # FIRMAS
    need_firmas = 4.2*cm
    y = _ensure_space(c, y, need_firmas, folio, fecha, tecnico, localidad)
    yfm = _draw_section(c, "Firmas", y, need_firmas)
    c.setFont("Helvetica", 9)
    c.drawString(2.0*cm, yfm-1.0*cm, f"Técnico: {firma_tecnico_nombre}")
    c.line(2.0*cm, yfm-2.7*cm, 9.2*cm, yfm-2.7*cm)
    if firma_tecnico_path and os.path.exists(firma_tecnico_path):
        c.drawImage(ImageReader(firma_tecnico_path), 2.0*cm, yfm-2.6*cm, width=7.2*cm, height=1.6*cm,
                    preserveAspectRatio=True, anchor='sw')
    c.drawString(10.2*cm, yfm-1.0*cm, f"Cliente: {firma_cliente_nombre}")
    c.line(10.2*cm, yfm-2.7*cm, 17.2*cm, yfm-2.7*cm)
    if firma_cliente_path and os.path.exists(firma_cliente_path):
        c.drawImage(ImageReader(firma_cliente_path), 10.2*cm, yfm-2.6*cm, width=7.2*cm, height=1.6*cm,
                    preserveAspectRatio=True, anchor='sw')

    # --- cerrar el PDF y guardar en borrador ---
    c.showPage(); c.save(); buf.seek(0)
    pdf_bytes = buf.read()
    nombre_pdf = f"REPORTE_{tipo_servicio.upper()}_{cliente.replace(' ', '_')}.pdf"

    # Save report metadata to database for service history
    save_report(
        folio=folio,
        fecha=fecha,
        cliente=cliente,
        tipo_equipo=tipo_equipo,
        modelo=modelo,
        serie=serie,
        marca=marca,
        potencia=potencia,
        tipo_servicio=tipo_servicio,
        descripcion_servicio=desc_servicio,
        tecnico=tecnico,
        localidad=localidad
    )

    # Convertir fotos a base64 para guardar en borrador
    # Convertir fotos a base64 para guardar en borrador
    fotos_base64 = {}
    for i in range(1, 5):
        foto_file = request.files.get(f"foto{i}")
        # Buscar primero en foto{i}_data (hidden input con datos base64)
        foto_data = request.form.get(f"foto{i}_data")
        # Fallback a foto{i}_existing (nombre antiguo)
        existing_b64 = request.form.get(f"foto{i}_existing")
        
        if foto_file and foto_file.filename:
            # New file uploaded
            foto_file.seek(0)
            foto_bytes = foto_file.read()
            fotos_base64[f"foto{i}"] = base64.b64encode(foto_bytes).decode('utf-8')
        elif foto_data:
            # Use foto{i}_data (preferred - from hidden input)
            # Remove data URL prefix if present (data:image/png;base64,...)
            if "," in foto_data:
                foto_data = foto_data.split(",")[1]
            fotos_base64[f"foto{i}"] = foto_data
        elif existing_b64:
            # Use existing base64 data (legacy field name)
            if "," in existing_b64:
                existing_b64 = existing_b64.split(",")[1]
            fotos_base64[f"foto{i}"] = existing_b64
    
    # Preparar form_data para guardar en borrador
    form_data = {}
    for key in request.form:
        form_data[key] = request.form.get(key)
    
    # Get deal_id if provided
    deal_id = request.form.get("deal_id") or session.get("deal_id")
    if deal_id:
        try:
            deal_id = int(deal_id)
        except:
            deal_id = None
    
    # Guardar borrador completo con PDF
    save_draft_report(
        folio=folio,
        form_data=form_data,
        foto1=fotos_base64.get("foto1"),
        foto2=fotos_base64.get("foto2"),
        foto3=fotos_base64.get("foto3"),
        foto4=fotos_base64.get("foto4"),
        firma_tecnico=request.form.get("firma_tecnico_data"),
        firma_cliente=request.form.get("firma_cliente_data"),
        pdf_preview=pdf_bytes,
        deal_id=deal_id
    )

    # Redirigir a vista previa en lugar de descargar
    return redirect(url_for("vista_previa", folio=folio))


# === API: crear un nuevo folio y dejarlo en la sesión ===
@app.route("/api/nuevo_folio", methods=["POST"])
def api_nuevo_folio():
    if "user" not in session:
        return ("", 401)
    session["folio_actual"] = get_next_folio(session["prefijo"])
    return {"folio": session["folio_actual"]}

# ==================== API: Get deals by client ====================
@app.route("/api/deals/by_client/<int:cliente_id>", methods=["GET"])
def api_get_deals_by_client(cliente_id):
    """Get all deals for a specific client"""
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        deals = get_deals_by_client_id(cliente_id)
        # Format deals for dropdown: id, folio, titulo, tipo_deal
        deals_list = []
        for deal in deals:
            deals_list.append({
                'id': deal.get('id'),
                'folio': deal.get('folio') or f"ID-{deal.get('id')}",
                'titulo': deal.get('titulo', 'Sin título'),
                'tipo_deal': deal.get('tipo_deal', 'venta'),
                'etapa': deal.get('etapa', '')
            })
        return jsonify({"success": True, "deals": deals_list})
    except Exception as e:
        print(f"Error getting deals by client: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== DRAFT REPORT ROUTES ====================

@app.route("/api/autosave_draft", methods=["POST"])
def api_autosave_draft():
    """Auto-save draft report (called every few seconds from JavaScript)"""
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        
        folio = data.get("folio")
        form_data = data.get("form_data", {})
        
        # Extract photos and signatures from form_data (they're stored there by serializeForm)
        foto1 = form_data.get("foto1_data") or data.get("foto1_data")
        foto2 = form_data.get("foto2_data") or data.get("foto2_data")
        foto3 = form_data.get("foto3_data") or data.get("foto3_data")
        foto4 = form_data.get("foto4_data") or data.get("foto4_data")
        firma_tecnico = form_data.get("firma_tecnico_data") or data.get("firma_tecnico_data")
        firma_cliente = form_data.get("firma_cliente_data") or data.get("firma_cliente_data")
        
        if not folio:
            return jsonify({"error": "Missing folio"}), 400
        
        # Get deal_id from form_data or session
        deal_id = form_data.get("deal_id") or session.get("deal_id")
        if deal_id:
            try:
                deal_id = int(deal_id)
            except:
                deal_id = None
        
        # Save to database
        save_draft_report(
            folio=folio,
            form_data=form_data,
            foto1=foto1,
            foto2=foto2,
            foto3=foto3,
            foto4=foto4,
            firma_tecnico=firma_tecnico,
            firma_cliente=firma_cliente,
            deal_id=deal_id
        )
        
        return jsonify({"success": True, "message": "Draft saved"})
    
    except Exception as e:
        print(f"Error saving draft: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/guardar_borrador", methods=["POST"])
def guardar_borrador():
    """Generate PDF preview and redirect to preview page"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    # This route will reuse the existing PDF generation logic from generar_pdf
    # but instead of downloading, it saves to database and redirects to preview
    
    folio = request.form.get("folio") or session.get("folio_actual")
    
    # First, save all form data to draft (similar to autosave but with files)
    form_data = {}
    for key in request.form:
        form_data[key] = request.form.get(key)
    
    # Handle photo uploads - convert to Base64
    fotos_base64 = {}
    for i in range(1, 5):
        foto_file = request.files.get(f"foto{i}")
        if foto_file and foto_file.filename:
            foto_bytes = foto_file.read()
            fotos_base64[f"foto{i}_data"] = base64.b64encode(foto_bytes).decode('utf-8')
    
    # Generate PDF (reuse existing logic but capture to bytes)
    pdf_bytes = _generate_pdf_bytes(request.form, request.files)
    
    # Get deal_id if provided
    deal_id = request.form.get("deal_id") or session.get("deal_id")
    if deal_id:
        try:
            deal_id = int(deal_id)
        except:
            deal_id = None
    
    # Save complete draft including PDF
    save_draft_report(
        folio=folio,
        form_data=form_data,
        foto1=fotos_base64.get("foto1_data"),
        foto2=fotos_base64.get("foto2_data"),
        foto3=fotos_base64.get("foto3_data"),
        foto4=fotos_base64.get("foto4_data"),
        firma_tecnico=request.form.get("firma_tecnico_data"),
        firma_cliente=request.form.get("firma_cliente_data"),
        pdf_preview=pdf_bytes,
        deal_id=deal_id
    )
    
    return redirect(url_for("vista_previa", folio=folio))

@app.route("/vista_previa/<folio>")
def vista_previa(folio):
    """Show PDF preview page with Edit and Send buttons"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    draft = get_draft_by_folio(folio)
    if not draft:
        return "Borrador no encontrado", 404
    
    # Parse form_data to get client email
    try:
        form_data = json.loads(draft["form_data"]) if isinstance(draft["form_data"], str) else draft["form_data"]
        client_email = form_data.get("email", "")
    except:
        client_email = ""
    
    return render_template("vista_previa.html", 
                         folio=folio,
                         client_email=client_email,
                         draft=draft)


def _get_filename_from_draft(draft, folio):
    """Generate filename: Tipo_Descripcion_Folio.pdf"""
    try:
        form_data = json.loads(draft["form_data"]) if isinstance(draft["form_data"], str) else draft["form_data"]
        tipo = form_data.get("tipo_servicio", "Servicio").strip().replace(" ", "_")
        desc = form_data.get("descripcion_servicio", "Descripcion").strip().replace(" ", "_")
        
        # Sanitize
        import re
        tipo = re.sub(r'[\\/*?:"<>|]', "", tipo)
        desc = re.sub(r'[\\/*?:"<>|]', "", desc)
        
        # Limit length just in case
        if len(desc) > 30: desc = desc[:30]
        
        return f"{tipo}_{desc}_{folio}.pdf"
    except:
        return f"Reporte_{folio}.pdf"

@app.route("/api/pdf_preview/<folio>")
def api_pdf_preview(folio):
    """Return PDF file for preview or download"""
    if "user" not in session:
        return ("", 401)
    
    draft = get_draft_by_folio(folio)
    if not draft or not draft.get("pdf_preview"):
        return "PDF no encontrado", 404
    
    should_download = request.args.get('download') == 'true'
    filename = _get_filename_from_draft(draft, folio)
    
    return send_file(
        io.BytesIO(draft["pdf_preview"]),
        mimetype="application/pdf",
        as_attachment=should_download,
        download_name=filename
    )

@app.route("/editar_reporte/<folio>")
def editar_reporte(folio):
    """Load form with draft data for editing"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Set the folio in session for the form to use
    session["folio_actual"] = folio
    
    # Render the form - JavaScript will load the draft data
    return render_template(
        "formulario.html",
        folio=folio,
        lista_equipos=LISTA_EQUIPOS,
        dg_labels=DG_LABELS, 
        of_labels=OF_LABELS, 
        e3=E3, 
        e1=E1,
        edit_mode=True  # Flag to tell the template we're editing
    )



@app.route("/api/load_draft/<folio>")
def api_load_draft(folio):
    """Return draft data as JSON for form population"""
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    draft = get_draft_by_folio(folio)
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
    
    # Parse form_data
    try:
        form_data = json.loads(draft["form_data"]) if isinstance(draft["form_data"], str) else draft["form_data"]
    except:
        form_data = {}
    
    return jsonify({
        "form_data": form_data,
        "foto1_data": draft.get("foto1_data"),
        "foto2_data": draft.get("foto2_data"),
        "foto3_data": draft.get("foto3_data"),
        "foto4_data": draft.get("foto4_data"),
        "firma_tecnico_data": draft.get("firma_tecnico_data"),
        "firma_cliente_data": draft.get("firma_cliente_data")
    })

@app.route("/api/drafts", methods=["GET"])
def api_list_drafts():
    """Return all draft reports from database"""
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    drafts = get_all_drafts()
    result = []
    for draft in drafts:
        try:
            form_data = json.loads(draft["form_data"]) if isinstance(draft["form_data"], str) else draft["form_data"]
            result.append({
                "folio": draft["folio"],
                "savedAt": draft.get("updated_at") or draft.get("created_at"),
                "cliente": form_data.get("cliente", ""),
                "tipo": form_data.get("tipo_servicio", "")
            })
        except:
            result.append({
                "folio": draft["folio"],
                "savedAt": draft.get("updated_at") or draft.get("created_at"),
                "cliente": "",
                "tipo": ""
            })
    
    return jsonify(result)

@app.route("/api/delete_draft/<folio>", methods=["DELETE"])
def api_delete_draft(folio):
    """Delete a draft report from database"""
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    success = delete_draft(folio)
    if success:
        return jsonify({"success": True, "message": "Draft deleted"})
    else:
        return jsonify({"error": "Draft not found"}), 404

@app.route("/reportes_pendientes")
def reportes_pendientes():
    """Show pending draft reports (not sent yet)"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Get current user info
    user = get_user_by_username(session.get("user"))
    user_nombre = session.get("user_nombre", user.get("nombre", "") if user else "")
    user_puesto = session.get("puesto", user.get("puesto", "") if user else "")
    
    # Check if user is admin
    is_admin = user_puesto == "Administrador"
    
    # Get pending drafts
    pending_drafts = get_pending_drafts_by_tecnico(user_nombre, is_admin)
    
    # Parse form_data for each draft to extract info
    import json
    drafts_info = []
    for draft in pending_drafts:
        try:
            form_data = json.loads(draft["form_data"]) if isinstance(draft["form_data"], str) else draft["form_data"]
            drafts_info.append({
                "folio": draft["folio"],
                "fecha": form_data.get("fecha", ""),
                "cliente": form_data.get("cliente", ""),
                "tipo_servicio": form_data.get("tipo_servicio", ""),
                "tecnico": form_data.get("tecnico", ""),
                "updated_at": draft.get("updated_at") or draft.get("created_at", "")
            })
        except:
            drafts_info.append({
                "folio": draft["folio"],
                "fecha": "",
                "cliente": "",
                "tipo_servicio": "",
                "tecnico": "",
                "updated_at": draft.get("updated_at") or draft.get("created_at", "")
            })
    
    return render_template("reportes_pendientes.html", 
                         drafts=drafts_info,
                         is_admin=is_admin,
                         user_nombre=user_nombre)

@app.route("/enviar_reporte/<folio>", methods=["POST"])
def enviar_reporte(folio):
    """Send report via email to client"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Get draft data
    draft = get_draft_by_folio(folio)
    if not draft or not draft.get("pdf_preview"):
        return "Reporte no encontrado", 404
    
    # Get client email from form data
    try:
        form_data = json.loads(draft["form_data"]) if isinstance(draft["form_data"], str) else draft["form_data"]
        client_email = form_data.get("email", "").strip()
        cliente_nombre = form_data.get("cliente", "Cliente")
        tipo_servicio = form_data.get("tipo_servicio", "servicio")
    except:
        return "Error al obtener datos del cliente", 400
    
    if not client_email:
        return "No se especificó email del cliente", 400
    
    # Configure SMTP (use environment variables for production)
    # For Gmail: you need to use an App Password if 2FA is enabled
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "customerg0179@gmail.com")
    smtp_password = os.environ.get("SMTP_PASSWORD", "bhzt jwak cfdc vjjx")
    
    if not smtp_user or not smtp_password:
        return "Configuración de email no disponible. Configure SMTP_USER y SMTP_PASSWORD", 500
    
    try:
        # Create email
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = client_email
        msg['Cc'] = "customerservice@inair.com.mx"
        msg['Subject'] = f"Reporte de {tipo_servicio} - Folio {folio}"
        
        # Email body
        body = f"""
Estimado/a {cliente_nombre},

Adjunto encontrará el reporte de {tipo_servicio} correspondiente al folio {folio}.

Si tiene alguna pregunta o comentario, no dude en contactarnos.

Saludos cordiales,
InAIR - Servicio Técnico
        """.strip()
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF - CRÍTICO: Usar EXACTAMENTE el mismo patrón que send_cotizacion_pdf y send_factura_pdf
        pdf_bytes = draft["pdf_preview"]
        if not pdf_bytes:
            return "Error: PDF no disponible", 400
        
        # CRÍTICO: Asegurar que pdf_bytes sea realmente bytes, no string
        if isinstance(pdf_bytes, str):
            # Si es string, podría ser base64, intentar decodificar
            try:
                import base64
                pdf_bytes = base64.b64decode(pdf_bytes)
            except:
                # Si no es base64, convertir a bytes
                pdf_bytes = pdf_bytes.encode('latin-1')
        elif not isinstance(pdf_bytes, bytes):
            # Si es otro tipo, convertir a bytes
            pdf_bytes = bytes(pdf_bytes)
        
        # Verificar que el PDF tenga contenido válido (debe empezar con %PDF)
        if len(pdf_bytes) < 4 or pdf_bytes[:4] != b'%PDF':
            print(f"⚠️ ADVERTENCIA: El PDF puede estar corrupto. Primeros bytes: {pdf_bytes[:20]}")
            # No fallar, pero registrar la advertencia
        
        filename = _get_filename_from_draft(draft, folio)
        print(f"📎 Adjuntando PDF: {filename} ({len(pdf_bytes)} bytes)")
        
        # CRÍTICO: Usar EXACTAMENTE el mismo patrón que send_cotizacion_pdf (línea 134-136)
        # NO agregar Content-Type explícitamente, MIMEApplication lo maneja automáticamente
        pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(pdf_attachment)
        
        # CRÍTICO: Verificar que el adjunto esté en el mensaje antes de enviar
        attached_parts = []
        for part in msg.walk():
            content_disp = str(part.get_content_disposition() or '')
            if 'attachment' in content_disp.lower():
                attached_parts.append(part)
        
        if len(attached_parts) == 0:
            print(f"❌ ERROR CRÍTICO: No se encontraron adjuntos en el mensaje antes de enviar!")
            print(f"   Revisando estructura completa del mensaje MIME...")
            all_parts = list(msg.walk())
            print(f"   Total de partes en mensaje: {len(all_parts)}")
            for idx, part in enumerate(all_parts):
                ct = part.get_content_type()
                cd = str(part.get_content_disposition() or 'N/A')
                fn = part.get_filename() or 'N/A'
                print(f"   Parte #{idx}: Type={ct}, Disposition={cd}, Filename={fn}")
            return "Error: No se pudo adjuntar el PDF", 500
        
        print(f"✅ Verificación: {len(attached_parts)} adjunto(s) en el mensaje antes de enviar")
        for idx, part in enumerate(attached_parts, 1):
            filename_check = part.get_filename() or 'sin nombre'
            try:
                payload = part.get_payload(decode=True)
                size = len(payload) if payload else 0
                content_type = part.get_content_type()
                print(f"   ✅ Adjunto #{idx}: {filename_check} ({size} bytes, tipo: {content_type})")
            except Exception as e:
                print(f"   ⚠️ Adjunto #{idx}: {filename_check} (error al verificar: {e})")
        
        # Send email - CRÍTICO: Usar send_message() en lugar de sendmail() con as_string()
        # send_message() maneja mejor el encoding y los adjuntos
        # No necesita to_addrs porque los destinatarios ya están en los headers To y Cc
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        # CRÍTICO: Usar send_message() que maneja mejor los adjuntos y encoding
        # send_message() automáticamente usa los destinatarios de los headers To, Cc, Bcc
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email enviado exitosamente a {client_email} con adjunto PDF")
        
        # Mark draft as sent
        mark_draft_as_sent(folio)
        
        # Clear current folio from session
        session.pop("folio_actual", None)
        
        # Redirect to success page
        return render_template("envio_exitoso.html", folio=folio, email=client_email, filename=filename)
        
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return f"Error al enviar el correo: {str(e)}", 500



# ==================== ADMIN ROUTES ====================

@app.route("/admin/dashboard")
@require_role("admin")
def admin_dashboard():
    """Admin dashboard with statistics and navigation"""
    stats = get_dashboard_stats()
    return render_template("admin_dashboard.html", stats=stats)

# ---------- Client Management ----------

@app.route("/admin/clientes")
@require_permission("clientes")
def admin_clientes():
    """List all clients"""
    clients = get_all_clients()
    return render_template("admin_clientes.html", clients=clients, lista_equipos=LISTA_EQUIPOS)

@app.route("/admin/clientes/nuevo", methods=["POST"])
@require_permission("clientes")
def admin_clientes_nuevo():
    """Create new client"""
    nombre = request.form.get("nombre", "").strip()
    contacto = request.form.get("contacto", "").strip()
    telefono = request.form.get("telefono", "").strip()
    email = request.form.get("email", "").strip()
    direccion = request.form.get("direccion", "").strip()
    rfc = request.form.get("rfc", "").strip()
    vendedor_nombre = request.form.get("vendedor_nombre", "").strip()
    vendedor_email = request.form.get("vendedor_email", "").strip()
    vendedor_telefono = request.form.get("vendedor_telefono", "").strip()
    
    if nombre:
        client_id = create_client(nombre, contacto, telefono, email, direccion, rfc, vendedor_nombre, vendedor_email, vendedor_telefono)
        
        # Save additional contacts
        contact_names = request.form.getlist("contact_nombre[]")
        contact_emails = request.form.getlist("contact_email[]")
        contact_phones = request.form.getlist("contact_telefono[]")
        contact_positions = request.form.getlist("contact_puesto[]")
        
        for i, c_nombre in enumerate(contact_names):
            if c_nombre.strip():
                add_client_contact(
                    client_id,
                    c_nombre.strip(),
                    contact_emails[i].strip() if i < len(contact_emails) else "",
                    contact_phones[i].strip() if i < len(contact_phones) else "",
                    contact_positions[i].strip() if i < len(contact_positions) else ""
                )
    
    return redirect(url_for("admin_clientes"))

@app.route("/admin/clientes/editar/<int:client_id>", methods=["POST"])
@require_permission("clientes")
def admin_clientes_editar(client_id):
    """Update client information"""
    nombre = request.form.get("nombre", "").strip()
    contacto = request.form.get("contacto", "").strip()
    telefono = request.form.get("telefono", "").strip()
    email = request.form.get("email", "").strip()
    direccion = request.form.get("direccion", "").strip()
    rfc = request.form.get("rfc", "").strip()
    vendedor_nombre = request.form.get("vendedor_nombre", "").strip()
    vendedor_email = request.form.get("vendedor_email", "").strip()
    vendedor_telefono = request.form.get("vendedor_telefono", "").strip()
    
    if nombre:
        update_client(client_id, nombre, contacto, telefono, email, direccion, rfc, vendedor_nombre, vendedor_email, vendedor_telefono)
        
        # Update contacts (delete all and re-add)
        delete_client_contacts(client_id)
        
        contact_names = request.form.getlist("contact_nombre[]")
        contact_emails = request.form.getlist("contact_email[]")
        contact_phones = request.form.getlist("contact_telefono[]")
        contact_positions = request.form.getlist("contact_puesto[]")
        
        for i, c_nombre in enumerate(contact_names):
            if c_nombre.strip():
                add_client_contact(
                    client_id,
                    c_nombre.strip(),
                    contact_emails[i].strip() if i < len(contact_emails) else "",
                    contact_phones[i].strip() if i < len(contact_phones) else "",
                    contact_positions[i].strip() if i < len(contact_positions) else ""
                )
    
    return redirect(url_for("admin_clientes"))

@app.route("/admin/clientes/eliminar/<int:client_id>", methods=["POST"])
@require_permission("clientes")
def admin_clientes_eliminar(client_id):
    """Delete client"""
    delete_client(client_id)
    return redirect(url_for("admin_clientes"))

# ---------- User Management ----------

@app.route("/admin/usuarios")
@require_permission("usuarios")
def admin_usuarios():
    """List all users"""
    users = get_all_users()
    puestos = get_all_puestos()
    return render_template("admin_usuarios.html", users=users, puestos=puestos)

@app.route("/admin/usuarios/nuevo", methods=["POST"])
@require_permission("usuarios")
def admin_usuarios_nuevo():
    """Create new user"""
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "").strip()
    nombre = request.form.get("nombre", "").strip()
    prefijo = request.form.get("prefijo", "").strip().upper()
    role = request.form.get("role", "technician").strip()
    puesto = request.form.get("puesto", "").strip()
    telefono = request.form.get("telefono", "").strip()
    email = request.form.get("email", "").strip()
    email_smtp = request.form.get("email_smtp", "").strip()
    password_smtp = request.form.get("password_smtp", "").strip()
    firma_email = request.form.get("firma_email", "")  # Don't strip to preserve line breaks
    
    # Handle signature image upload
    firma_imagen = None
    if 'firma_imagen' in request.files:
        file = request.files['firma_imagen']
        if file and file.filename:
            import base64
            firma_imagen = base64.b64encode(file.read()).decode('utf-8')
    
    if username and password and nombre and prefijo:
        try:
            create_user(username, password, nombre, prefijo, role, puesto, telefono, email, email_smtp, password_smtp, firma_email, firma_imagen)
        except:
            pass  # User already exists
    
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuarios/eliminar/<int:user_id>", methods=["POST"])
@require_permission("usuarios")
def admin_usuarios_eliminar(user_id):
    """Delete user"""
    # Get current user to prevent self-deletion
    current_user = get_user_by_username(session.get("user"))
    if current_user and current_user["id"] != user_id:
        delete_user(user_id)
    
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuarios/editar/<int:user_id>", methods=["POST"])
@require_permission("usuarios")
def admin_usuarios_editar(user_id):
    """Edit existing user"""
    data = {
        'nombre': request.form.get("nombre", "").strip(),
        'prefijo': request.form.get("prefijo", "").strip().upper(),
        'role': request.form.get("role", "technician").strip(),
        'puesto': request.form.get("puesto", "").strip(),
        'telefono': request.form.get("telefono", "").strip(),
        'email': request.form.get("email", "").strip(),
    }
    
    # SMTP Configuration
    email_smtp = request.form.get("email_smtp", "").strip()
    if email_smtp:
        data['email_smtp'] = email_smtp
    
    password_smtp = request.form.get("password_smtp", "").strip()
    if password_smtp:  # Only update if provided
        data['password_smtp'] = password_smtp
    
    # Email signature (don't strip to preserve line breaks)
    firma_email = request.form.get("firma_email", "")
    data['firma_email'] = firma_email  # Always save (even if empty)
    
    # Handle signature image upload
    if 'firma_imagen' in request.files:
        file = request.files['firma_imagen']
        if file and file.filename:
            import base64
            data['firma_imagen'] = base64.b64encode(file.read()).decode('utf-8')
    
    # Only update password if provided
    new_password = request.form.get("password", "").strip()
    if new_password:
        data['password'] = new_password
    
    update_user(user_id, data)
    return redirect(url_for("admin_usuarios"))

# ---------- Puestos Management ----------

@app.route("/api/puestos", methods=["GET"])
@require_role("admin")
def api_puestos_list():
    """Get all puestos"""
    puestos = get_all_puestos()
    return jsonify({"success": True, "puestos": puestos})

@app.route("/api/puestos", methods=["POST"])
@require_role("admin")
def api_puestos_create():
    """Create a new puesto"""
    data = request.json
    nombre = data.get('nombre', '').strip()
    permisos = data.get('permisos', 'formulario')
    
    if not nombre:
        return jsonify({"success": False, "error": "El nombre es requerido"}), 400
    
    puesto_id = create_puesto(nombre, permisos)
    if puesto_id:
        return jsonify({"success": True, "id": puesto_id, "nombre": nombre})
    return jsonify({"success": False, "error": "Ya existe un puesto con ese nombre"}), 400

@app.route("/api/puestos/<int:id>", methods=["PUT"])
@require_role("admin")
def api_puestos_update(id):
    """Update a puesto"""
    data = request.json
    nombre = data.get('nombre')
    permisos = data.get('permisos')
    
    success = update_puesto(id, nombre=nombre, permisos=permisos)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Error al actualizar o el nombre ya existe"}), 400

@app.route("/api/puestos/<int:id>", methods=["DELETE"])
@require_role("admin")
def api_puestos_delete(id):
    """Delete a puesto"""
    success = delete_puesto(id)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "No se puede eliminar: hay usuarios con este puesto"}), 400

# ---------- Service History ----------

@app.route("/admin/historial")
@require_permission("historial")
def admin_historial():
    """View service history with filters"""
    search_term = request.args.get("search", "").strip()
    tipo_servicio = request.args.get("tipo_servicio", "").strip()
    fecha_inicio = request.args.get("fecha_inicio", "").strip()
    fecha_fin = request.args.get("fecha_fin", "").strip()
    
    if search_term or tipo_servicio or fecha_inicio or fecha_fin:
        reports = search_reports(search_term, tipo_servicio, fecha_inicio, fecha_fin)
    else:
        reports = get_all_reports()
    
    return render_template("admin_historial.html", reports=reports)

@app.route("/admin/historial/<folio>")
@require_permission("historial")
def admin_historial_detalle(folio):
    """Get report details as JSON"""
    report = get_report_by_folio(folio)
    if report:
        return jsonify(report)
    return jsonify({"error": "Report not found"}), 404

# ---------- Almacen (Inventory) Management ----------

@app.route("/admin/almacen")
@require_permission("almacen")
def admin_almacen():
    """List all inventory items"""
    refacciones = get_all_refacciones()
    clientes = get_all_clients()
    return render_template("admin_almacen.html", refacciones=refacciones, clientes=clientes)

@app.route("/api/almacen/refaccion/<numero_parte>", methods=["GET"])
@require_permission("almacen")
def api_get_refaccion_by_numero_parte(numero_parte):
    """Get refaccion by numero_parte for autofill"""
    try:
        ref = get_refaccion_by_numero_parte(numero_parte)
        if ref:
            return jsonify({"success": True, "refaccion": ref})
        return jsonify({"success": False, "error": "No encontrada"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== OCU ENDPOINTS ====================

@app.route("/api/ocu", methods=["POST"])
@require_permission("crm")
def api_create_ocu():
    """
    Create an Orden de Cumplimiento (OCu) from a customer PO.
    Body: { folio_cliente, cliente_id, cliente_nombre, notas, items:[{numero_parte, descripcion, unidad, cantidad}] }
    """
    data = request.json or {}
    folio_cliente = data.get("folio_cliente")
    cliente_id = data.get("cliente_id")
    cliente_nombre = data.get("cliente_nombre", "")
    notas = data.get("notas", "")
    items = data.get("items", [])

    if not items or not folio_cliente:
        return jsonify({"success": False, "error": "folio_cliente e items son requeridos"}), 400

    # Crear oc_cliente y OCu
    oc_cliente_id = create_oc_cliente(folio_cliente, cliente_id, cliente_nombre, notas)
    ocu_id = create_ocu(oc_cliente_id, cliente_id, cliente_nombre, estado="open", notas=notas)

    # Procesar items: calcular disponible y reservar
    total_faltante = 0
    total_reservado = 0
    for it in items:
        numero_parte = it.get("numero_parte", "").strip()
        descripcion = it.get("descripcion", "")
        unidad = it.get("unidad", "PZA")
        cantidad = float(it.get("cantidad", 0) or 0)
        reservado = 0
        faltante = cantidad

        ref = get_refaccion_by_numero_parte(numero_parte) if numero_parte else None
        if ref:
            disponible = (ref.get("cantidad", 0) or 0) - (ref.get("apartados", 0) or 0)
            reservado = min(disponible, cantidad) if disponible > 0 else 0
            faltante = max(0, cantidad - reservado)

            # Crear reserva para lo reservado (apartados)
            if reservado > 0:
                create_reserva(
                    refaccion_id=ref["id"],
                    cliente_id=cliente_id,
                    cantidad=reservado,
                    orden_compra=str(folio_cliente),
                    cliente_nombre=cliente_nombre or None
                )

        total_reservado += reservado
        total_faltante += faltante
        add_ocu_item(ocu_id, numero_parte, descripcion, unidad, cantidad, reservado, faltante)

        # Generar requisición de compra si faltante > 0
        if faltante > 0:
            create_purchase_requisition(ocu_id, numero_parte, faltante, notas=f"Faltante de OCu {ocu_id}")

    # Si todo reservado, crear solicitud de factura
    estado = "ready_to_invoice"
    if total_reservado == 0:
        estado = "waiting_purchase"
    elif total_faltante > 0 and total_reservado > 0:
        estado = "partial_waiting_purchase"

    # Crear solicitud de factura si hay stock disponible (ready_to_invoice o partial)
    if estado == "ready_to_invoice":
        create_finance_request(ocu_id, notas=f"OCu {ocu_id} lista para facturar")
    elif estado == "partial_waiting_purchase" and total_reservado > 0:
        # También crear finance_request para OCUs parciales con stock disponible
        create_finance_request(ocu_id, notas=f"OCu {ocu_id} parcial - partidas disponibles en stock")

    # Actualizar estado de OCu
    update_remision_state_sql = "UPDATE ocu SET estado = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute(update_remision_state_sql, (estado, ocu_id))
        conn.commit()

    # Notificar al contador si hay stock disponible (solo si total_reservado > 0)
    from database import notify_contador_ocu_nueva
    if total_reservado > 0:
        try:
            notify_contador_ocu_nueva(ocu_id)
        except Exception as e:
            print(f"Error sending OCu notifications: {e}")

    ocu = get_ocu_by_id(ocu_id)
    return jsonify({"success": True, "ocu": ocu, "estado": estado})

@app.route("/api/ocu/<int:ocu_id>", methods=["GET"])
@require_permission("crm")
def api_get_ocu(ocu_id):
    ocu = get_ocu_by_id(ocu_id)
    if not ocu:
        return jsonify({"success": False, "error": "OCu no encontrada"}), 404
    return jsonify({"success": True, "ocu": ocu})

# ==================== FINANCE REQUESTS ====================

@app.route("/api/finance_requests", methods=["GET"])
@require_permission("finanzas")
def api_list_finance_requests():
    from database import get_deal_by_id, get_db
    import sqlite3
    status = request.args.get("status")
    requests_list = get_finance_requests(status)
    
    # Enriquecer con información de documentos y factura vinculada
    for fr in requests_list:
        ocu_id = fr.get('ocu_id')
        if ocu_id:
            # Obtener información del OCu (estado, items disponibles vs faltantes)
            ocu = get_ocu_by_id(ocu_id)
            if ocu:
                fr['ocu_estado'] = ocu.get('estado', 'open')
                items = ocu.get('items', [])
                items_disponibles = [it for it in items if (it.get('reservado', 0) or 0) > 0]
                items_faltantes = [it for it in items if (it.get('faltante', 0) or 0) > 0]
                fr['items_disponibles_count'] = len(items_disponibles)
                fr['items_faltantes_count'] = len(items_faltantes)
                fr['total_reservado'] = sum((it.get('reservado', 0) or 0) for it in items)
                fr['total_faltante'] = sum((it.get('faltante', 0) or 0) for it in items)
                fr['es_parcial'] = fr['total_reservado'] > 0 and fr['total_faltante'] > 0
            
            # Buscar factura vinculada a esta OCu
            with sqlite3.connect(DATABASE) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM facturas WHERE ocu_id = ? LIMIT 1", (ocu_id,))
                factura_row = cursor.fetchone()
                if factura_row:
                    fr['factura_id'] = factura_row['id']
            
            # Buscar deal que tenga este ocu_id
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM crm_deals WHERE ocu_id = ?", (ocu_id,))
                deal_row = cursor.fetchone()
                if deal_row:
                    deal_id = deal_row['id']
                    deal = get_deal_by_id(deal_id)
                    if deal:
                        # Obtener cotización vinculada
                        cotizaciones = deal.get('cotizaciones', [])
                        if cotizaciones:
                            # Tomar la primera cotización
                            cot_id = cotizaciones[0].get('id')
                            fr['cotizacion_id'] = cot_id
                            fr['cotizacion_folio'] = cotizaciones[0].get('folio')
                        
                        # Obtener OC del cliente si existe
                        oc_file_path = deal.get('oc_cliente_file_path')
                        if oc_file_path:
                            fr['oc_cliente_file_path'] = oc_file_path
    
    return jsonify({"success": True, "requests": requests_list})

@app.route("/api/finance_requests/<int:fr_id>/esperar_orden_completa", methods=["POST"])
@require_permission("finanzas")
def api_esperar_orden_completa(fr_id):
    """Marcar finance_request para esperar orden completa"""
    from database import update_finance_request_status
    updated = update_finance_request_status(fr_id, "waiting")
    if updated:
        return jsonify({"success": True, "message": "Solicitud marcada para esperar orden completa"})
    return jsonify({"success": False, "error": "No se pudo actualizar"}), 400

@app.route("/api/finance_requests/verificar_ocu/<int:ocu_id>", methods=["POST"])
@require_permission("finanzas")
def api_verificar_crear_fr_ocu(ocu_id):
    """Verificar y crear finance_request para un OCu si no existe y tiene stock"""
    from database import get_ocu_by_id, create_finance_request, get_db
    import sqlite3
    
    # Verificar si ya existe finance_request
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM finance_requests WHERE ocu_id = ?", (ocu_id,))
        existing = cursor.fetchone()
        if existing:
            return jsonify({"success": True, "message": "Finance request ya existe", "fr_id": existing['id']})
    
    # Obtener OCu
    ocu = get_ocu_by_id(ocu_id)
    if not ocu:
        return jsonify({"success": False, "error": "OCu no encontrada"}), 404
    
    # Verificar items y calcular stock disponible
    items = ocu.get('items', [])
    total_reservado = sum((it.get('reservado', 0) or 0) for it in items)
    total_faltante = sum((it.get('faltante', 0) or 0) for it in items)
    
    if total_reservado <= 0:
        return jsonify({"success": False, "error": "No hay stock disponible para facturar"}), 400
    
    # Determinar notas según el estado
    estado = ocu.get('estado', 'open')
    if total_faltante > 0:
        notas = f"OCu {ocu_id} parcial - partidas disponibles en stock"
    else:
        notas = f"OCu {ocu_id} lista para facturar"
    
    # Crear finance_request
    try:
        fr_id = create_finance_request(ocu_id, notas=notas)
        return jsonify({"success": True, "message": "Finance request creado", "fr_id": fr_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/finance_requests/<int:fr_id>/generar_factura", methods=["POST"])
@require_permission("finanzas")
def api_generar_factura_from_finance_request(fr_id):
    """
    Crear factura en borrador desde una solicitud de factura (finance_request).
    Idempotente: si ya existe factura ligada a la OCu, la reutiliza.
    No descuenta inventario.
    """
    fr_list = get_finance_requests()
    fr = next((r for r in fr_list if r.get('id') == fr_id), None)
    if not fr:
        return jsonify({"success": False, "error": "Solicitud no encontrada"}), 404
    ocu_id = fr.get('ocu_id')
    if not ocu_id:
        return jsonify({"success": False, "error": "Solicitud sin OCu vinculada"}), 400

    # Reutilizar factura si ya existe ligada a esta OCu
    existing = None
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        try:
            c.execute("SELECT id FROM facturas WHERE ocu_id = ? LIMIT 1", (ocu_id,))
            row = c.fetchone()
            if row:
                existing = row[0]
        except Exception as e:
            print(f"Error buscando factura por ocu_id: {e}")

    if existing:
        # Solo marcar en_proceso al generar/reutilizar borrador
        update_finance_request_status(fr_id, "in_progress")
        return jsonify({"success": True, "factura_id": existing})

    ocu = get_ocu_by_id(ocu_id)
    if not ocu:
        return jsonify({"success": False, "error": "OCu no encontrada"}), 404
    items = ocu.get('items', [])
    
    # FILTRAR: Solo incluir items con stock disponible (reservado > 0)
    # El contador solo debe facturar lo que está disponible, no los faltantes
    items_con_stock = [it for it in items if (it.get('reservado', 0) or 0) > 0]

    partidas = []
    subtotal_total = 0

    # Intentar usar precios desde la cotización (buscada por folio_ocu)
    cot_items = None
    folio_lookup = fr.get('folio_ocu') or ocu.get('folio_ocu')
    if folio_lookup:
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id FROM cotizaciones WHERE folio = ? LIMIT 1", (folio_lookup,))
            row = c.fetchone()
            if row:
                cot = get_cotizacion_by_id(row['id'])
                cot_items = cot.get('items') if cot else None
            conn.close()
        except Exception as e:
            print(f"Error buscando cotizacion por folio {folio_lookup}: {e}")

    iva_pct = 0
    if cot_items:
        iva_pct = cot.get('iva_porcentaje') or 0
        # Normalizar si viene como fracción (ej. 0.08 -> 8%)
        try:
            iva_pct = float(iva_pct)
            if iva_pct < 1:
                iva_pct = iva_pct * 100
        except:
            iva_pct = 0
        # Crear un mapa de items de cotización por numero_parte para matching
        cot_items_map = {it.get('numero_parte', ''): it for it in cot_items}
        
        # Solo procesar items del OCu que tienen stock disponible
        for ocu_item in items_con_stock:
            numero_parte = ocu_item.get('numero_parte', '')
            reservado = float(ocu_item.get('reservado', 0) or 0)
            
            # Buscar item correspondiente en cotización
            cot_item = cot_items_map.get(numero_parte)
            if cot_item:
                precio = cot_item.get('precio_unitario')
                if precio is None:
                    try:
                        importe = float(cot_item.get('importe', 0) or 0)
                        cantidad_cot = float(cot_item.get('cantidad', 0) or 0)
                        precio = importe / cantidad_cot if cantidad_cot else 0
                    except:
                        precio = 0
                # Usar la cantidad RESERVADA (stock disponible), no la cantidad total
                qty = reservado
                subtotal = (precio or 0) * qty
                subtotal_total += subtotal
                partidas.append({
                    "codigo": numero_parte,
                    "descripcion": ocu_item.get('descripcion') or cot_item.get('descripcion') or '',
                    "cantidad": qty,
                    "unidad": ocu_item.get('unidad') or cot_item.get('unidad') or 'PZA',
                    "precio_unitario": precio or 0,
                    "subtotal": subtotal
                })
    else:
        # Fallback sin precios (solo items con stock disponible)
        for it in items_con_stock:
            reservado = float(it.get('reservado', 0) or 0)
            # Usar la cantidad RESERVADA (stock disponible)
            qty = reservado
            subtotal_total += 0
            partidas.append({
                "codigo": it.get('numero_parte') or '',
                "descripcion": it.get('descripcion') or '',
                "cantidad": qty,
                "unidad": it.get('unidad') or 'PZA',
                "precio_unitario": 0,
                "subtotal": 0
            })

    numero_factura = get_next_factura_folio()
    fecha_emision = datetime.now().strftime("%Y-%m-%d")
    cliente_id = ocu.get('cliente_id')
    cliente_nombre = ocu.get('cliente_nombre') or fr.get('cliente_nombre') or 'Cliente'
    notas = fr.get('notas') or f"Generada desde solicitud de factura #{fr_id} OCu {ocu_id}"

    factura_id = create_factura(
        numero_factura=numero_factura,
        fecha_emision=fecha_emision,
        cliente_nombre=cliente_nombre,
        subtotal=subtotal_total,
        iva_porcentaje=iva_pct,
        cliente_id=cliente_id,
        cliente_rfc=None,
        cotizacion_id=None,
        moneda='MXN',
        fecha_vencimiento=None,
        metodo_pago=None,
        notas=notas,
        partidas=partidas
    )

    # Ligar factura con OCu
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        try:
            c.execute("UPDATE facturas SET ocu_id = ? WHERE id = ?", (ocu_id, factura_id))
            conn.commit()
        except Exception as e:
            print(f"Error ligando factura con OCu: {e}")

    # Solo marcar en_progreso; se marcará facturada cuando la factura se emita/pague
    update_finance_request_status(fr_id, "in_progress")
    return jsonify({"success": True, "factura_id": factura_id})

# ==================== PURCHASE REQUISITIONS ====================

@app.route("/api/purchase_requisitions", methods=["GET"])
@require_permission("compras")
def api_list_purchase_requisitions():
    from database import get_deal_by_id, get_cotizacion_by_id, get_db
    status = request.args.get("status")
    reqs = get_purchase_requisitions(status)
    
    # Enriquecer con información de documentos
    for req in reqs:
        ocu_id = req.get('ocu_id')
        if ocu_id:
            # Buscar deal que tenga este ocu_id
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM crm_deals WHERE ocu_id = ?", (ocu_id,))
                deal_row = cursor.fetchone()
                if deal_row:
                    deal_id = deal_row['id']
                    deal = get_deal_by_id(deal_id)
                    if deal:
                        # Obtener cotización vinculada
                        cotizaciones = deal.get('cotizaciones', [])
                        if cotizaciones:
                            # Tomar la primera cotización
                            cot_id = cotizaciones[0].get('id')
                            req['cotizacion_id'] = cot_id
                            req['cotizacion_folio'] = cotizaciones[0].get('folio')
                        
                        # Obtener OC del cliente si existe
                        oc_file_path = deal.get('oc_cliente_file_path')
                        if oc_file_path:
                            req['oc_cliente_file_path'] = oc_file_path
    
    return jsonify({"success": True, "requisitions": reqs})

@app.route("/api/purchase_requisitions/<int:req_id>/marcar_en_proceso", methods=["POST"])
@require_permission("compras")
def api_marcar_requisicion_en_proceso(req_id):
    updated = update_purchase_requisition_status(req_id, "in_progress")
    return jsonify({"success": updated})

@app.route("/api/purchase_requisitions/<int:req_id>/marcar_orden_colocada", methods=["POST"])
@require_permission("compras")
def api_marcar_requisicion_orden_colocada(req_id):
    updated = update_purchase_requisition_status(req_id, "ordered")
    return jsonify({"success": updated})

@app.route("/api/purchase_requisitions/<int:req_id>/marcar_recibido", methods=["POST"])
@require_permission("compras")
def api_marcar_requisicion_recibido(req_id):
    # No se toca inventario (solo estado)
    updated = update_purchase_requisition_status(req_id, "received")
    return jsonify({"success": updated})

# Helper: create OCu from deal (latest cotizacion)
def create_ocu_from_deal(deal):
    """
    Create an OCu from the latest cotizacion linked to the deal.
    Returns (created: bool, message: str, ocu_id: int or None)
    """
    deal_id = deal.get('id')
    cliente_id = deal.get('cliente_id')
    cliente_nombre = deal.get('cliente_nombre')

    # If already has OCu, skip
    if deal.get('ocu_id'):
        return False, "El trato ya tiene una OCu creada.", deal.get('ocu_id')

    cotizaciones = deal.get('cotizaciones') or []
    if not cotizaciones:
        return False, "El trato no tiene cotización vinculada, no se creó la OCu.", None

    # Tomar la más reciente (última por id)
    latest_cot = sorted(cotizaciones, key=lambda c: c.get('id', 0))[-1]
    cotizacion_id = latest_cot.get('id')
    cot = get_cotizacion_by_id(cotizacion_id)
    if not cot or not cot.get('items'):
        return False, "La cotización vinculada no tiene partidas, no se creó la OCu.", None

    folio_cliente = cot.get('folio') or f"COT-{cotizacion_id}"
    notas = f"OCu generada desde trato {deal.get('folio', deal_id)}"

    # Crear oc_cliente y OCu
    oc_cliente_id = create_oc_cliente(folio_cliente, cliente_id, cliente_nombre, notas)
    ocu_id = create_ocu(oc_cliente_id, cliente_id, cliente_nombre, estado="open", notas=notas)

    total_reservado = 0
    total_faltante = 0

    for it in cot.get('items', []):
        numero_parte = it.get('numero_parte', '').strip()
        descripcion = it.get('descripcion', '')
        unidad = it.get('unidad', 'PZA')
        cantidad = float(it.get('cantidad', 0) or 0)
        reservado = 0
        faltante = cantidad

        ref = get_refaccion_by_numero_parte(numero_parte) if numero_parte else None
        if ref:
            disponible = (ref.get("cantidad", 0) or 0) - (ref.get("apartados", 0) or 0)
            reservado = min(disponible, cantidad) if disponible > 0 else 0
            faltante = max(0, cantidad - reservado)

            # Crear reserva si hay stock disponible
            if reservado > 0:
                create_reserva(
                    refaccion_id=ref["id"],
                    cliente_id=cliente_id,
                    cantidad=reservado,
                    orden_compra=str(folio_cliente),
                    cliente_nombre=cliente_nombre or None
                )

        total_reservado += reservado
        total_faltante += faltante
        add_ocu_item(ocu_id, numero_parte, descripcion, unidad, cantidad, reservado, faltante)

        # Requisición de compra por faltante
        if faltante > 0:
            create_purchase_requisition(ocu_id, numero_parte, faltante, notas=f"Faltante de OCu {ocu_id}")

    # Estado final
    estado = "ready_to_invoice"
    if total_reservado == 0:
        estado = "waiting_purchase"
    elif total_faltante > 0 and total_reservado > 0:
        estado = "partial_waiting_purchase"

    if estado == "ready_to_invoice":
        create_finance_request(ocu_id, notas=f"OCu {ocu_id} lista para facturar")

    # Update OCu estado
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("UPDATE ocu SET estado = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (estado, ocu_id))
        conn.commit()

    # Notificar al contador si hay stock disponible (solo si total_reservado > 0)
    from database import notify_contador_ocu_nueva
    if total_reservado > 0:
        try:
            notify_contador_ocu_nueva(ocu_id)
        except Exception as e:
            print(f"Error sending OCu notifications: {e}")

    # Guardar ocu_id en el trato
    set_deal_ocu_id(deal_id, ocu_id)

    return True, f"OCu creada con estado {estado}", ocu_id

@app.route("/admin/almacen/nueva", methods=["POST"])
@require_permission("almacen")
def admin_almacen_nueva():
    """Create new inventory item"""
    numero_parte = request.form.get("numero_parte", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    unidad = request.form.get("unidad", "").strip()
    cantidad = request.form.get("cantidad", "0").strip()
    ubicacion = request.form.get("ubicacion", "").strip()
    ubicacion_especifica = request.form.get("ubicacion_especifica", "").strip()
    detalles = request.form.get("detalles_importacion", "").strip()
    
    if not numero_parte:
        return redirect(url_for("admin_almacen"))
    
    # Parse cantidad safely
    try:
        cantidad_int = int(float(cantidad))
    except:
        cantidad_int = 0
    
    # Check if exists to update (only quantity) or create new
    existing = get_refaccion_by_numero_parte(numero_parte)
    if existing:
        new_qty = (existing.get("cantidad") or 0) + cantidad_int
        # keep other fields intact; just update qty and timestamps
        update_refaccion(
            existing["id"],
            existing.get("numero_parte", numero_parte),
            existing.get("descripcion", descripcion or ""),
            existing.get("unidad", unidad or ""),
            new_qty,
            existing.get("ubicacion", ubicacion or ""),
            existing.get("detalles_importacion", detalles or ""),
            existing.get("ubicacion_especifica", ubicacion_especifica or "")
        )
        flash(f"Refacción existente. Cantidad actualizada a {new_qty}.", "success")
    else:
        if descripcion:
            try:
                create_refaccion(numero_parte, descripcion, unidad, cantidad_int, ubicacion, detalles, ubicacion_especifica)
                flash("Refacción creada.", "success")
            except Exception as e:
                print(f"Error creating refaccion: {e}")
            
    return redirect(url_for("admin_almacen"))

@app.route("/admin/almacen/editar/<int:id>", methods=["POST"])
@require_role("admin")
def admin_almacen_editar(id):
    """Update inventory item"""
    numero_parte = request.form.get("numero_parte", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    unidad = request.form.get("unidad", "").strip()
    cantidad = request.form.get("cantidad", "0").strip()
    ubicacion = request.form.get("ubicacion", "").strip()
    ubicacion_especifica = request.form.get("ubicacion_especifica", "").strip()
    detalles = request.form.get("detalles_importacion", "").strip()
    
    if numero_parte and descripcion:
        try:
            update_refaccion(id, numero_parte, descripcion, unidad, int(cantidad), ubicacion, detalles, ubicacion_especifica)
        except Exception as e:
            print(f"Error updating refaccion: {e}")
            
    return redirect(url_for("admin_almacen"))

@app.route("/admin/almacen/carga_masiva", methods=["POST"])
@require_role("admin")
def admin_almacen_carga_masiva():
    """Bulk upload inventory items via JSON or Excel"""
    import openpyxl
    
    # 1. Handle JSON data (Copy/Paste)
    if request.is_json:
        data = request.get_json()
        items = data.get("items", [])
        count = 0
        for item in items:
            try:
                # Expected format: [Part, Desc, Qty, Unit, Loc, SpecificLoc]
                if len(item) >= 2:
                    create_refaccion(
                        numero_parte=str(item[0]).strip(),
                        descripcion=str(item[1]).strip(),
                        cantidad=int(item[2]) if len(item) > 2 and str(item[2]).isdigit() else 0,
                        unidad=str(item[3]).strip() if len(item) > 3 else "",
                        ubicacion=str(item[4]).strip() if len(item) > 4 else "",
                        ubicacion_especifica=str(item[5]).strip() if len(item) > 5 else ""
                    )
                    count += 1
            except Exception as e:
                print(f"Error adding item {item}: {e}")
        return jsonify({"success": True, "count": count})

    # 2. Handle File Upload (Excel)
    file = request.files.get("file")
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            count = 0
            # Skip header row
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0]: # Must have part number
                    try:
                        create_refaccion(
                            numero_parte=str(row[0]).strip(),
                            descripcion=str(row[1]).strip() if row[1] else "",
                            cantidad=int(row[2]) if row[2] and str(row[2]).isdigit() else 0,
                            unidad=str(row[3]).strip() if row[3] else "",
                            ubicacion=str(row[4]).strip() if row[4] else "",
                            ubicacion_especifica=str(row[5]).strip() if len(row) > 5 and row[5] else ""
                        )
                        count += 1
                    except Exception as e:
                        print(f"Error processing row {row}: {e}")
            return jsonify({"success": True, "count": count})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    return jsonify({"success": False, "error": "Invalid request"}), 400

@app.route("/admin/almacen/eliminar/<int:id>", methods=["POST"])
@require_role("admin")
def admin_almacen_eliminar(id):
    """Delete inventory item"""
    delete_refaccion(id)
    return redirect(url_for("admin_almacen"))

@app.route("/api/almacen/buscar")
def api_almacen_buscar():
    """Search inventory items (API)"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    query = request.args.get("q", "").strip()
    ubicacion = request.args.get("ubicacion", "").strip()
    
    results = search_refacciones(query, ubicacion)
    return jsonify([dict(r) for r in results])

# ---------- Maintenance Plans ----------
# NOTE: These routes are commented out because the maintenance plan functions
# don't exist in database.py. Equipment maintenance is now handled through
# the client equipment system instead.

# @app.route("/admin/mantenimiento")
# @require_role("admin")
# def admin_mantenimiento():
#     """List all maintenance plans"""
#     plans = get_all_maintenance_plans()
#     return render_template("admin_mantenimiento.html", plans=plans)

# @app.route("/admin/mantenimiento/nuevo", methods=["GET", "POST"])
# @require_role("admin")
# def admin_mantenimiento_nuevo():
#     """Create new maintenance plan"""
#     if request.method == "POST":
#         cliente_id = request.form.get("cliente_id", type=int)
#         tipo_equipo = request.form.get("tipo_equipo", "").strip()
#         modelo = request.form.get("modelo", "").strip()
#         serie = request.form.get("serie", "").strip()
#         frecuencia_dias = request.form.get("frecuencia_dias", type=int)
#         fecha_inicial = request.form.get("fecha_inicial", "").strip()
#         
#         if cliente_id and tipo_equipo and frecuencia_dias and fecha_inicial:
#             create_maintenance_plan(cliente_id, tipo_equipo, modelo, serie, 
#                                    frecuencia_dias, fecha_inicial)
#             return redirect(url_for("admin_mantenimiento"))
#     
#     # GET request - show form
#     clients = get_all_clients()
#     return render_template("admin_mantenimiento_nuevo.html", 
#                          clients=clients, 
#                          lista_equipos=LISTA_EQUIPOS)

# @app.route("/admin/mantenimiento/<int:plan_id>")
# @require_role("admin")
# def admin_mantenimiento_detalle(plan_id):
#     """View maintenance plan details"""
#     plan = get_maintenance_plan_by_id(plan_id)
#     if not plan:
#         return redirect(url_for("admin_mantenimiento"))
#     
#     services = get_services_by_plan(plan_id)
#     
#     # Get parts for each service
#     for service in services:
#         service['parts'] = get_parts_by_service(service['id'])
#     
#     return render_template("admin_mantenimiento_detalle.html", 
#                          plan=plan, 
#                          services=services)

# @app.route("/admin/mantenimiento/<int:plan_id>/servicio", methods=["POST"])
# @require_role("admin")
# def admin_mantenimiento_agregar_servicio(plan_id):
#     """Add service to maintenance plan"""
#     fecha_servicio = request.form.get("fecha_servicio", "").strip()
#     descripcion = request.form.get("descripcion", "").strip()
#     tecnico = request.form.get("tecnico", "").strip()
#     folio = request.form.get("folio", "").strip()
#     
#     if fecha_servicio and descripcion:
#         service_id = create_maintenance_service(plan_id, fecha_servicio, 
#                                                descripcion, tecnico, folio)
#         
#         # Add parts if provided
#         part_names = request.form.getlist("part_nombre[]")
#         part_quantities = request.form.getlist("part_cantidad[]")
#         part_descriptions = request.form.getlist("part_descripcion[]")
#         
#         for i, nombre in enumerate(part_names):
#             if nombre.strip():
#                 cantidad = int(part_quantities[i]) if i < len(part_quantities) and part_quantities[i].isdigit() else 1
#                 desc = part_descriptions[i] if i < len(part_descriptions) else ""
#                 create_part(service_id, nombre.strip(), cantidad, desc.strip())
#     
#     return redirect(url_for("admin_mantenimiento_detalle", plan_id=plan_id))

# @app.route("/admin/mantenimiento/<int:plan_id>/toggle", methods=["POST"])
# @require_role("admin")
# def admin_mantenimiento_toggle(plan_id):
#     """Toggle maintenance plan active status"""
#     from database import toggle_maintenance_plan
#     toggle_maintenance_plan(plan_id)
#     return redirect(url_for("admin_mantenimiento"))


# ==========================================
# API Routes for Auto-fill
# ==========================================

@app.route("/api/clientes")
def api_clientes():
    """Get list of all clients"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    clients = get_all_clients()
    return jsonify([{
        "id": c["id"],
        "nombre": c["nombre"],
        "contacto": c.get("contacto", ""),
        "telefono": c.get("telefono", ""),
        "email": c.get("email", ""),
        "direccion": c.get("direccion", "")
    } for c in clients])

@app.route("/api/cliente/<int:client_id>")
def api_cliente_detalle(client_id):
    """Get client details"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    client = get_client_by_id(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    return jsonify({
        "id": client["id"],
        "nombre": client["nombre"],
        "contacto": client["contacto"],
        "telefono": client["telefono"],
        "email": client["email"],
        "direccion": client["direccion"],
        "rfc": client.get("rfc", ""),
        "vendedor_nombre": client.get("vendedor_nombre", ""),
        "vendedor_email": client.get("vendedor_email", ""),
        "vendedor_telefono": client.get("vendedor_telefono", ""),
        "contactos": get_client_contacts(client_id)
    })

@app.route("/api/equipos/<int:client_id>")
def api_client_equipment(client_id):
    """Get all equipment for a client"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    equipment = get_client_equipment(client_id)
    return jsonify([{
        "id": e["id"],
        "tipo_equipo": e["tipo_equipo"],
        "modelo": e["modelo"],
        "serie": e["serie"],
        "marca": e["marca"],
        "potencia": e["potencia"],
        "proximo_servicio": e.get("proximo_servicio")
    } for e in equipment])
    return jsonify({
        "id": client["id"],
        "nombre": client["nombre"],
        "contacto": client["contacto"],
        "telefono": client["telefono"],
        "email": client["email"],
        "direccion": client["direccion"]
    })

@app.route("/api/tipos_equipo/<int:client_id>")
def api_tipos_equipo(client_id):
    """Get unique equipment types for a client"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    types = get_equipment_types_by_client(client_id)
    return jsonify(types)

@app.route("/api/modelos/<int:client_id>/<path:tipo_equipo>")
def api_modelos(client_id, tipo_equipo):
    """Get models for a client and equipment type"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    models = get_models_by_client_and_type(client_id, tipo_equipo)
    return jsonify(models)

@app.route("/api/equipo/<int:equipment_id>")
def api_equipo_detalle(equipment_id):
    """Get full equipment details"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    equipment = get_equipment_by_id(equipment_id)
    if not equipment:
        return jsonify({"error": "Equipment not found"}), 404
        
    return jsonify(dict(equipment))

# ==========================================
# Admin Routes for Equipment Management
# ==========================================

@app.route("/admin/clientes/<int:client_id>/equipos", methods=["POST"])
@require_role("admin")
def admin_agregar_equipo(client_id):
    """Add equipment to a client"""
    tipo_equipo = request.form.get("tipo_equipo")
    modelo = request.form.get("modelo")
    serie = request.form.get("serie")
    marca = request.form.get("marca")
    potencia = request.form.get("potencia")
    
    # Maintenance Info
    ultimo_servicio = request.form.get("ultimo_servicio")
    frecuencia_meses = int(request.form.get("frecuencia_meses", 1))
    
    # Calculate next service
    proximo_servicio = None
    if ultimo_servicio:
        try:
            last_date = datetime.strptime(ultimo_servicio, '%Y-%m-%d')
            # Add months (approximate as 30 days * months for simplicity, or use relativedelta if available, but standard lib doesn't have it. 
            # Let's use a simple approximation or a custom function if needed. 
            # For now, 30 days * months is a reasonable approximation for maintenance intervals usually defined in hours/months.)
            # Better: Use a helper to add months correctly if possible, but standard datetime doesn't support adding months directly.
            # Let's just use 30 days per month for now to avoid external deps like dateutil.
            next_date = last_date + timedelta(days=frecuencia_meses * 30)
            proximo_servicio = next_date.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Kits (JSON strings)
    # We will receive lists of parts (qty, desc) for each kit.
    # The form will likely send arrays like kit_2000_qty[], kit_2000_desc[]
    import json
    
    def get_kit_data(prefix):
        qtys = request.form.getlist(f"{prefix}_qty[]")
        descs = request.form.getlist(f"{prefix}_desc[]")
        parts = []
        for q, d in zip(qtys, descs):
            if q.strip() or d.strip(): # Only add if not empty
                parts.append({"cantidad": q, "descripcion": d})
        return json.dumps(parts) if parts else None

    kit_2000 = get_kit_data("kit_2000")
    kit_4000 = get_kit_data("kit_4000")
    kit_6000 = get_kit_data("kit_6000")
    kit_8000 = get_kit_data("kit_8000")
    kit_16000 = get_kit_data("kit_16000")
    
    if tipo_equipo:
        add_client_equipment(client_id, tipo_equipo, modelo, serie, marca, potencia,
                             ultimo_servicio, frecuencia_meses, proximo_servicio,
                             kit_2000, kit_4000, kit_6000, kit_8000, kit_16000)
        
    return redirect(url_for("admin_clientes"))

@app.route("/admin/equipos/eliminar/<int:equipment_id>", methods=["POST"])
@require_role("admin")
def admin_eliminar_equipo(equipment_id):
    """Delete equipment"""
    # We need client_id to redirect back properly, but for now redirecting to clients list
    delete_client_equipment(equipment_id)
    return redirect(url_for("admin_clientes"))



# ==================== MÓDULO DE EQUIPOS ====================
# Rutas independientes para gestión de equipos (no tocar lógica de reportes)

@app.route("/admin/equipos_modulo")
@require_permission("equipos")
def admin_equipos_modulo():
    """Vista principal del módulo de equipos"""
    return render_template("equipos.html", LISTA_EQUIPOS=LISTA_EQUIPOS)

@app.route("/admin/calendario")
@require_permission("equipos")
def admin_calendario():
    """Vista del calendario de mantenimiento"""
    return render_template("calendario_mantenimiento.html")

@app.route("/api/clientes/<int:cliente_id>/equipos", methods=["GET"])
def api_cliente_equipos(cliente_id):
    """Obtener equipos asignados a un cliente desde equipos_calendario + info del cliente"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get client info
        c.execute("SELECT * FROM clients WHERE id = ?", (cliente_id,))
        cliente = c.fetchone()
        
        # Get equipment
        c.execute("""
            SELECT id, serie, tipo_equipo, modelo, marca, potencia 
            FROM equipos_calendario 
            WHERE cliente_id = ? AND activo = 1
            ORDER BY tipo_equipo, modelo, serie
        """, (cliente_id,))
        
        equipos = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return jsonify({
            "cliente": dict(cliente) if cliente else None,
            "equipos": equipos
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/equipos_list", methods=["GET"])
@require_permission("equipos")
def api_equipos_list():
    """Listar todos los equipos del calendario"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT 
                e.*,
                c.nombre as cliente_nombre
            FROM equipos_calendario e
            LEFT JOIN clients c ON e.cliente_id = c.id
            WHERE e.activo = 1
            ORDER BY e.id DESC
        """)
        
        equipos = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return jsonify(equipos)
    except Exception as e:
        print(f"ERROR API EQUIPOS: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/equipos_create", methods=["POST"])
@require_role("admin")
def api_equipos_create():
    """Crear nuevo equipo en calendario"""
    data = request.json
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    print(f"DEBUG CREATE EQUIPO: {data}") # Debug log
    
    try:
        c.execute("""
            INSERT INTO equipos_calendario 
            (cliente_id, serie, tipo_equipo, modelo, marca, potencia, 
             frecuencia_meses, mes_inicio, anio_inicio, tipo_servicio_inicial, reiniciar_en_horas, notas, clasificacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(data.get("cliente_id")) if data.get("cliente_id") else None,
            data.get("serie"),
            data.get("tipo_equipo"),
            data.get("modelo"),
            data.get("marca"),
            data.get("potencia"),
            data.get("frecuencia_meses"),
            data.get("mes_inicio"),
            data.get("anio_inicio"),
            data.get("tipo_servicio_inicial", "2000 Horas"),
            int(data.get("reiniciar_en_horas")) if data.get("reiniciar_en_horas") else None,
            data.get("notas"),
            data.get("clasificacion", "General")
        ))
        
        conn.commit()
        equipo_id = c.lastrowid
        conn.close()
        
        return jsonify({"success": True, "id": equipo_id})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": "Serie ya existe"}), 400

@app.route("/api/equipos_update/<int:equipo_id>", methods=["PUT"])
@require_permission("equipos")
def api_equipos_update(equipo_id):
    """Actualizar equipo"""
    data = request.json
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    print(f"DEBUG UPDATE EQUIPO {equipo_id}: {data}") # Debug log
    
    c.execute("""
        UPDATE equipos_calendario 
        SET cliente_id=?, tipo_equipo=?, modelo=?, marca=?, potencia=?,
            frecuencia_meses=?, mes_inicio=?, anio_inicio=?, tipo_servicio_inicial=?, reiniciar_en_horas=?, notas=?, clasificacion=?
        WHERE id=?
    """, (
        int(data.get("cliente_id")) if data.get("cliente_id") else None,
        data.get("tipo_equipo"),
        data.get("modelo"),
        data.get("marca"),
        data.get("potencia"),
        data.get("frecuencia_meses"),
        data.get("mes_inicio"),
        data.get("anio_inicio"),
        data.get("tipo_servicio_inicial", "2000 Horas"),
        int(data.get("reiniciar_en_horas")) if data.get("reiniciar_en_horas") else None,
        data.get("notas"),
        data.get("clasificacion", "General"),
        equipo_id
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/equipos/<int:equipo_id>/kits", methods=["GET"])
@require_permission("equipos")
def api_equipos_kits_get(equipo_id):
    """Obtener kits de refacciones para un equipo"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM equipos_kits WHERE equipo_id = ?", (equipo_id,))
    kits = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(kits)

@app.route("/api/equipos/<int:equipo_id>/kits", methods=["POST"])
@require_permission("equipos")
def api_equipos_kits_save(equipo_id):
    """Guardar kits de refacciones para un equipo"""
    data = request.json # Expects list of kits: [{tipo_servicio, refacciones_json}, ...]
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    try:
        # Delete existing kits for this equipment to replace with new list
        c.execute("DELETE FROM equipos_kits WHERE equipo_id = ?", (equipo_id,))
        
        for kit in data:
            c.execute("""
                INSERT INTO equipos_kits (equipo_id, tipo_servicio, refacciones_json)
                VALUES (?, ?, ?)
            """, (equipo_id, kit['tipo_servicio'], kit['refacciones_json']))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        conn.close()
        print(f"ERROR SAVING KITS: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/equipos_delete/<int:equipo_id>", methods=["DELETE"])
@require_role("admin")
def api_equipos_delete(equipo_id):
    """Eliminar equipo (soft delete)"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("UPDATE equipos_calendario SET activo = 0 WHERE id = ?", (equipo_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/equipos_historial/<int:equipo_id>", methods=["GET"])
@require_role("admin")
def api_equipos_historial(equipo_id):
    """Obtener historial de servicios del equipo"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Obtener serie del equipo
    c.execute("SELECT serie FROM equipos_calendario WHERE id = ?", (equipo_id,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return jsonify([])
    
    serie = result["serie"]
    
    # Buscar reportes que contengan esa serie
    c.execute("""
        SELECT folio, fecha_creation, form_data
        FROM drafts
        WHERE form_data LIKE ?
        ORDER BY fecha_creation DESC
    """, (f"%{serie}%",))
    
    reportes = []
    for row in c.fetchall():
        try:
            form_data = json.loads(row["form_data"])
            if form_data.get("serie") == serie:
                reportes.append({
                    "folio": row["folio"],
                    "fecha": row["fecha_creation"],
                    "tipo_servicio": form_data.get("tipo_servicio"),
                    "descripcion": form_data.get("descripcion_servicio")
                })
        except:
            pass
    
    conn.close()
    return jsonify(reportes)

# ==================== FASE 4: CATÁLOGO DE REFACCIONES ====================

@app.route("/api/refacciones_catalogo", methods=["GET"])
@require_role("admin")
def api_refacciones_catalogo():
    """Listar catálogo de refacciones"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM refacciones_catalogo ORDER BY tipo_equipo, tipo_servicio")
    refacciones = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(refacciones)

@app.route("/api/refacciones_catalogo/create", methods=["POST"])
@require_role("admin")
def api_refacciones_catalogo_create():
    """Crear refacción en catálogo"""
    data = request.json
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    try:
        c.execute("""
            INSERT INTO refacciones_catalogo 
            (tipo_equipo, tipo_servicio, nombre_refaccion, cantidad, unidad)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.get("tipo_equipo"),
            data.get("tipo_servicio"),
            data.get("nombre_refaccion"),
            data.get("cantidad"),
            data.get("unidad")
        ))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": "Refacción ya existe"}), 400

@app.route("/api/refacciones_catalogo/<int:id>", methods=["DELETE"])
@require_role("admin")
def api_refacciones_catalogo_delete(id):
    """Eliminar refacción del catálogo"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM refacciones_catalogo WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/equipos/<int:equipo_id>/refacciones", methods=["GET"])
@require_role("admin")
def api_equipos_refacciones(equipo_id):
    """Obtener refacciones de un equipo (catálogo + custom)"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Obtener tipo de equipo
    c.execute("SELECT tipo_equipo FROM equipos_calendario WHERE id = ?", (equipo_id,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return jsonify({"catalogo": [], "custom": []})
    
    tipo_equipo = result["tipo_equipo"]
    
    # Catálogo general
    c.execute("""
        SELECT * FROM refacciones_catalogo 
        WHERE tipo_equipo = ?
        ORDER BY tipo_servicio, nombre_refaccion
    """, (tipo_equipo,))
    catalogo = [dict(row) for row in c.fetchall()]
    
    # Custom del equipo
    c.execute("""
        SELECT * FROM equipos_refacciones_custom 
        WHERE equipo_id = ?
        ORDER BY tipo_servicio, nombre_refaccion
    """, (equipo_id,))
    custom = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return jsonify({"catalogo": catalogo, "custom": custom})

# ==================== FASE 5: CALENDARIO DE MANTENIMIENTO ====================

@app.route("/api/calendario/<int:anio>/<int:mes>", methods=["GET"])
@require_role("admin")
def api_calendario_mes(anio, mes):
    """Obtener equipos que requieren servicio en un mes específico"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    equipos = []
    
    # Fetch all kits to avoid N+1 queries
    c.execute("SELECT * FROM equipos_kits")
    all_kits = [dict(row) for row in c.fetchall()]
    # Group kits by equipment_id
    kits_by_equipo = {}
    for k in all_kits:
        if k['equipo_id'] not in kits_by_equipo:
            kits_by_equipo[k['equipo_id']] = []
        kits_by_equipo[k['equipo_id']].append(k)

    for row in c.fetchall(): # This fetchall is empty because I already fetched above? No, different cursor execution.
        # Wait, I need to re-execute the equipment query or fetch before kits query.
        pass
    
    # Let's re-structure to be safe
    c.execute("""
        SELECT 
            e.*,
            c.nombre as cliente_nombre
        FROM equipos_calendario e
        LEFT JOIN clients c ON e.cliente_id = c.id
        WHERE e.activo = 1
    """)
    rows = c.fetchall()
    
    for row in rows:
        equipo = dict(row)
        # Calcular si le toca servicio este mes
        mes_inicio = equipo["mes_inicio"]
        anio_inicio = equipo["anio_inicio"]
        frecuencia = equipo["frecuencia_meses"]
        
        # Calcular meses desde inicio
        meses_desde_inicio = (anio - anio_inicio) * 12 + (mes - mes_inicio)
        
        if meses_desde_inicio >= 0 and meses_desde_inicio % frecuencia == 0:
            equipo["mes_servicio"] = mes
            equipo["anio_servicio"] = anio
            
            # Calculate Service Type with cycle reset support
            service_count = (meses_desde_inicio // frecuencia) + 1
            
            # Get tipo_servicio_inicial (default to 2000 Horas)
            servicio_inicial = equipo.get("tipo_servicio_inicial", "2000 Horas")
            
            # Extract initial hours value (e.g., "2000 Horas" -> 2000)
            try:
                horas_iniciales = int(servicio_inicial.split()[0])
            except:
                horas_iniciales = 2000
            
            # Apply cycle reset if configured
            reiniciar_en = equipo.get("reiniciar_en_horas")
            
            if reiniciar_en:
                # Build the complete cycle from 2000 to reiniciar_en (always starts at 2000)
                servicios_en_ciclo = []
                hora_actual = 2000
                while hora_actual <= reiniciar_en:
                    servicios_en_ciclo.append(hora_actual)
                    hora_actual += 2000
                
                # Find the starting position of horas_iniciales in the cycle
                try:
                    posicion_inicial = servicios_en_ciclo.index(horas_iniciales)
                except ValueError:
                    # If horas_iniciales is not in cycle, default to 0 (start at 2000)
                    posicion_inicial = 0
                
                # Calculate position: start at posicion_inicial, then advance (service_count - 1) steps
                # Use modulo to wrap around when reaching the end
                ciclo_index = (posicion_inicial + (service_count - 1)) % len(servicios_en_ciclo)
                hours_est = servicios_en_ciclo[ciclo_index]
            else:
                # No cycle reset: continue incrementing
                hours_est = horas_iniciales + ((service_count - 1) * 2000)
            
            service_name_est = f"{hours_est} Horas"
            equipo["tipo_servicio_calculado"] = service_name_est
            
            # Find matching kit
            equipo_kits = kits_by_equipo.get(equipo['id'], [])
            suggested_parts = []
            
            # Try exact match
            matching_kit = next((k for k in equipo_kits if k['tipo_servicio'] == service_name_est), None)
            
            # If not found, try default service type
            if not matching_kit:
                 matching_kit = next((k for k in equipo_kits if k['tipo_servicio'] == equipo.get('tipo_servicio_inicial')), None)
            
            if matching_kit:
                try:
                    suggested_parts = json.loads(matching_kit['refacciones_json'])
                except:
                    pass
            
            equipo["refacciones_sugeridas"] = suggested_parts
            
            # Check if service was completed (report exists for this month/year)
            c.execute("""
                SELECT folio, fecha FROM reports 
                WHERE serie = ? 
                AND strftime('%Y', fecha) = ? 
                AND strftime('%m', fecha) = ?
                ORDER BY fecha DESC LIMIT 1
            """, (equipo['serie'], str(anio), str(mes).zfill(2)))
            
            report_row = c.fetchone()
            if report_row:
                equipo["estatus_servicio"] = "REALIZADO"
                equipo["folio_servicio"] = report_row[0]  # For clickable link
            else:
                equipo["estatus_servicio"] = "PENDIENTE"
                equipo["folio_servicio"] = None
            
            equipos.append(equipo)
    
    conn.close()
    return jsonify(equipos)




# ==================== FASE 6: MÓDULO DE COTIZACIONES ====================

@app.route("/admin/cotizaciones")
@require_permission("cotizaciones")
def admin_cotizaciones():
    """List all quotations"""
    cotizaciones = get_all_cotizaciones()
    return render_template("admin_cotizaciones.html", cotizaciones=cotizaciones)

@app.route("/admin/cotizaciones/nueva", methods=["GET", "POST"])
@require_permission("cotizaciones")
def admin_cotizaciones_nueva():
    """Create new quotation"""
    deal_id = request.args.get('deal_id') or request.form.get('deal_id')
    
    if request.method == "POST":
        data = request.form.to_dict()
        
        # Process items from form (dynamic list)
        items = []
        lineas = request.form.getlist('item_linea[]')
        cantidades = request.form.getlist('item_cantidad[]')
        unidades = request.form.getlist('item_unidad[]')
        partes = request.form.getlist('item_parte[]')
        descripciones = request.form.getlist('item_descripcion[]')
        tiempos = request.form.getlist('item_tiempo[]')
        precios = request.form.getlist('item_precio[]')
        importes = request.form.getlist('item_importe[]')
        
        for i in range(len(lineas)):
            if descripciones[i]: # Only add if description exists
                items.append({
                    'linea': int(lineas[i]) if lineas[i] else i+1,
                    'cantidad': float(cantidades[i]) if cantidades[i] else 0,
                    'unidad': unidades[i],
                    'numero_parte': partes[i],
                    'descripcion': descripciones[i],
                    'tiempo_entrega_item': tiempos[i],
                    'precio_unitario': float(precios[i]) if precios[i] else 0,
                    'importe': float(importes[i]) if importes[i] else 0
                })
        
        # Create quote
        cotizacion_id = create_cotizacion(data, items)
        if cotizacion_id:
            # Auto-link to deal if deal_id was provided
            if deal_id:
                link_cotizacion_to_deal(int(deal_id), cotizacion_id)
                # Actualizar valor estimado automáticamente
                _update_deal_valor_estimado_from_cotizaciones(int(deal_id))
                return redirect(url_for("admin_crm_ver", id=deal_id))
            return redirect(url_for("admin_cotizaciones"))
        else:
            # Handle error (flash message ideally)
            pass

    # GET: Show form
    clients = get_all_clients()
    # Generate next folio for default sucursal (Tijuana)
    next_folio = get_next_cotizacion_folio('Tijuana')
    
    # If coming from CRM deal, pre-fill client
    pre_cliente_id = request.args.get('cliente_id')
    pre_cliente = None
    if pre_cliente_id:
        pre_cliente = get_client_by_id(int(pre_cliente_id))
    
    users = get_all_users()
    return render_template("admin_cotizacion_form.html", clients=clients, next_folio=next_folio, 
                          cotizacion=None, deal_id=deal_id, pre_cliente=pre_cliente, users=users)

@app.route("/admin/cotizaciones/editar/<int:id>", methods=["GET", "POST"])
@require_permission("cotizaciones")
def admin_cotizaciones_editar(id):
    """Edit existing quotation"""
    if request.method == "POST":
        data = request.form.to_dict()
        
        # Process items
        items = []
        lineas = request.form.getlist('item_linea[]')
        cantidades = request.form.getlist('item_cantidad[]')
        unidades = request.form.getlist('item_unidad[]')
        partes = request.form.getlist('item_parte[]')
        descripciones = request.form.getlist('item_descripcion[]')
        tiempos = request.form.getlist('item_tiempo[]')
        precios = request.form.getlist('item_precio[]')
        importes = request.form.getlist('item_importe[]')
        
        for i in range(len(lineas)):
            if descripciones[i]:
                items.append({
                    'linea': int(lineas[i]) if lineas[i] else i+1,
                    'cantidad': float(cantidades[i]) if cantidades[i] else 0,
                    'unidad': unidades[i],
                    'numero_parte': partes[i],
                    'descripcion': descripciones[i],
                    'tiempo_entrega_item': tiempos[i],
                    'precio_unitario': float(precios[i]) if precios[i] else 0,
                    'importe': float(importes[i]) if importes[i] else 0
                })
        
        update_cotizacion(id, data, items)
        return redirect(url_for("admin_cotizaciones"))

    # GET: Show form with data
    cotizacion = get_cotizacion_by_id(id)
    clients = get_all_clients()
    users = get_all_users()
    return render_template("admin_cotizacion_form.html", clients=clients, cotizacion=cotizacion, users=users)

@app.route("/admin/cotizaciones/eliminar/<int:id>", methods=["POST"])
@require_permission("cotizaciones")
def admin_cotizaciones_eliminar(id):
    """Delete quotation"""
    delete_cotizacion(id)
    return redirect(url_for("admin_cotizaciones"))

@app.route("/api/cotizaciones/folio/<sucursal>")
@require_permission("cotizaciones")
def api_cotizaciones_folio(sucursal):
    """Get next folio for given sucursal"""
    folio = get_next_cotizacion_folio(sucursal)
    return jsonify({'folio': folio})

@app.route("/api/almacen/buscar-producto")
@require_permission("cotizaciones")
def api_almacen_buscar_producto():
    """Search products in Almacen for autocomplete"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    # Search in almacen
    productos = search_refacciones(search_term=query)
    
    # Return relevant fields with delivery time suggestion
    results = []
    for p in productos[:10]:  # Limit to 10 results
        stock = p.get('cantidad', 0) or 0
        tiempo_entrega = "1-3 días" if stock >= 1 else "4-6 semanas"
        results.append({
            'id': p['id'],
            'numero_parte': p['numero_parte'],
            'descripcion': p['descripcion'],
            'unidad': p.get('unidad', 'PZA'),
            'stock': stock,
            'tiempo_entrega': tiempo_entrega
        })
    
    return jsonify(results)

def generate_factura_pdf_bytes(factura_id):
    """Generate PDF bytes for invoice - Shared function for web and email"""
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    
    factura = get_factura_by_id(factura_id)
    if not factura:
        return None
    
    # Create PDF with SimpleDocTemplate for better layout
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=80)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=8, leading=10)
    style_cell = ParagraphStyle('CellWrap', parent=styles['Normal'], fontSize=7, leading=9)
    style_right = ParagraphStyle('Right', parent=styles['Normal'], fontSize=8, alignment=TA_RIGHT)
    
    HEADER_BG = colors.HexColor("#4472C4")
    
    # ====== HEADER ======
    logo_path = os.path.join("static", "img", "logo_inair.png")
    if os.path.exists(logo_path):
        logo = RLImage(logo_path, width=120, height=50)
    else:
        logo = Paragraph("<b>INAIR</b>", style_normal)
    
    company_info_text = Paragraph("""
        <para align="right" fontSize="7" leading="9">
        <b>INGENIERÍA EN AIRE</b><br/>
        RFC: IAM140525BG4<br/>
        AVENIDA ALFONSO VIDAL Y PLANAS # 435, INT. 5-A, NUEVA TIJUANA,<br/>
        DEL TIJUANA<br/>
        TIJUANA, BAJA CALIFORNIA, MEXICO CP 22435<br/>
        601 - GENERAL DE LEY PERSONAS MORALES
        </para>
    """, style_right)
    
    header_table = Table([[logo, company_info_text]], colWidths=[150, 365])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    
    # ====== FACTURA INFO BOX ======
    iva_percent = factura.get('iva_porcentaje', 16)
    if iva_percent < 1:
        iva_percent = iva_percent * 100
    
    factura_info = Paragraph(f"""
        <para align="right" fontSize="8" backColor="#E8F4F8" leftIndent="10" rightIndent="10" spaceBefore="8" spaceAfter="8">
        <b>Factura: {factura['numero_factura']}</b><br/>
        Fecha: {factura['fecha_emision']}<br/>
        Fecha vencimiento: {factura.get('fecha_vencimiento') or 'N/A'}<br/>
        F.C.: 1.0<br/>
        Comprobante: I- Ingreso<br/>
        Moneda: {factura.get('moneda', 'MXN')} Pesos
        </para>
    """, style_right)
    
    info_table = Table([[Spacer(1,1), factura_info]], colWidths=[315, 210])
    elements.append(info_table)
    elements.append(Spacer(1, 15))
    
    # ====== CLIENT SECTION ======
    cliente_info = None
    if factura.get('cliente_id'):
        cliente_info = get_client_by_id(factura['cliente_id'])
    
    client_text = f"<b>Contacto:</b><br/><br/><b>{factura['cliente_nombre']}</b><br/>"
    
    if cliente_info:
        if cliente_info.get('direccion'):
            client_text += f"{cliente_info['direccion']}<br/>"
        if cliente_info.get('telefono'):
            client_text += f"Tel: {cliente_info['telefono']}<br/>"
    
    if factura.get('cliente_rfc'):
        client_text += f"RFC: {factura['cliente_rfc']}<br/>"
    
    if cliente_info and cliente_info.get('referencia'):
        client_text += f"Su referencia: {cliente_info['referencia']}"
    
    elements.append(Paragraph(client_text, style_normal))
    elements.append(Spacer(1, 15))
    
    # ====== ITEMS TABLE ======
    table_header = ['No.', 'Código', 'Descripción', 'Cantidad', 'Unidad', 'Precio unitario', 'Importe']
    data = [table_header]
    
    item_number = 1
    for partida in factura.get('partidas', []):
        desc_paragraph = Paragraph(partida['descripcion'] or '', style_cell)
        codigo_paragraph = Paragraph(partida.get('codigo', 'N/A') or 'N/A', style_cell)
        
        data.append([
            str(item_number),
            codigo_paragraph,
            desc_paragraph,
            f"{partida['cantidad']:.2f}",
            partida.get('unidad', 'SER'),
            f"$ {partida['precio_unitario']:,.2f}",
            f"$ {partida['subtotal']:,.2f}"
        ])
        item_number += 1
    
    col_widths = [30, 75, 190, 50, 40, 70, 70]
    items_table = Table(data, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),
        ('ALIGN', (5, 1), (6, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))
    
    # ====== TOTALS ======
    totals_data = [
        ['Subtotal', f"$ {factura['subtotal']:,.2f}"],
        [f"IVA {iva_percent:.0f}%", f"$ {factura['iva_monto']:,.2f}"],
        ['Total', f"$ {factura['total']:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[100, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 11),
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    totals_wrapper = Table([[Spacer(1,1), totals_table]], colWidths=[325, 200])
    elements.append(totals_wrapper)
    elements.append(Spacer(1, 15))
    
    # ====== PAYMENT CONDITIONS TEXT ======
    payment_conditions = f"""
    <para fontSize="7" leading="9" alignment="justify">
    POR ESTE PAGARÉ ME(NOS) OBLIGO(AMOS) A PAGAR INCONDICIONALMENTE A LA ORDEN DE INGENIERÍA EN AIRE S.A. DE C.V. 
    POR LA CANTIDAD DE: MXN $ {factura['total']:,.2f} - {num_a_letras(factura['total'])} PESOS M.N. EN LA CIUDAD DE TIJUANA, 
    BAJA CALIFORNIA AL VENCIMIENTO DE ESTE TÍTULO. LA SUMA QUE AMPARA ESTE PAGARÉ CAUSARÁ INTERESES MORATORIOS A RAZÓN DEL 5% 
    MENSUAL A PARTIR DE LA FECHA DE SU VENCIMIENTO. EN CASO DE COBRO JUDICIAL PAGARÉ LOS GASTOS QUE SE OCASIONEN, 
    RENUNCIANDO A MI AFUERO DOMICILIARIO.
    </para>
    """
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(payment_conditions, style_normal))
    elements.append(Spacer(1, 10))
    
    # Signature line
    signature_line = Paragraph("<para alignment='center'>_______________________________________<br/>Nombre y firma</para>", style_normal)
    elements.append(signature_line)
    elements.append(Spacer(1, 15))
    
    # ====== FOOTER FUNCTION ======
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#E74C3C'))
        canvas.setLineWidth(1.5)
        canvas.line(40, 70, A4[0] - 40, 70)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(40, 55, "INGENIERÍA EN AIRE SA DE CV  RFC: IAI160525B06")
        canvas.setFont('Helvetica', 6)
        canvas.drawString(40, 45, "Avenida Alfonso Vidal y Planas #445, Interior S/N, Colonia Nueva Tijuana, Tijuana, Baja California, México, Cp: 22435")
        canvas.drawString(40, 35, "Tel: (664) 250-0022 | pedidos@inair.com.mx | www.inair.com.mx")
        canvas.setFont('Helvetica', 6)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(A4[0] - 40, 55, f"Estado: {factura['estado_pago']}")
        canvas.drawRightString(A4[0] - 40, 47, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        canvas.restoreState()
    
    # Build PDF
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer.getvalue()

def generate_cotizacion_pdf_bytes(cotizacion_id):
    """Generate PDF bytes for quotation - Shared function for web and email"""
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.lib.colors import HexColor
    
    cotizacion = get_cotizacion_by_id(cotizacion_id)
    if not cotizacion:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=80)
    elements = []
    styles = getSampleStyleSheet()
    
    # Brand colors
    INAIR_RED = HexColor("#D20000")
    INAIR_DARK = HexColor("#333333")
    HEADER_BG = HexColor("#1a1a2e")
    
    # Custom styles
    style_title = ParagraphStyle('Title', parent=styles['Heading1'], textColor=INAIR_RED, fontSize=16, alignment=TA_CENTER)
    style_subtitle = ParagraphStyle('Subtitle', parent=styles['Normal'], textColor=INAIR_DARK, fontSize=10, alignment=TA_CENTER)
    style_section = ParagraphStyle('Section', parent=styles['Heading3'], textColor=INAIR_RED, fontSize=12, spaceAfter=6)
    style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=9, leading=12)
    style_small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    style_right = ParagraphStyle('Right', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT)
    
    # --- HEADER with Logo ---
    logo_path = os.path.join(app.root_path, 'static', 'img', 'logo_inair.png')
    
    header_data = []
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=120, height=40)
        header_left = logo
    else:
        header_left = Paragraph("<b>INAIR</b>", style_title)
    
    header_right = Paragraph(f"""
        <b>Cotización</b><br/>
        <font size="14" color="#D20000"><b>Folio {cotizacion['folio']}</b></font><br/>
        {cotizacion['sucursal'] or 'Tijuana'}, B.C., {cotizacion['fecha']}<br/>
        Vigencia: {cotizacion['vigencia']}
    """, style_right)
    
    header_table = Table([[header_left, header_right]], colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # --- CLIENT INFO ---
    elements.append(Paragraph("Cotizado a:", style_section))
    client_info = f"""
        <b>{cotizacion['cliente_nombre']}</b><br/>
        RFC: {cotizacion.get('cliente_rfc') or 'N/A'}<br/>
        {cotizacion['cliente_direccion'] or ''}<br/>
        Tel: {cotizacion['cliente_telefono'] or ''}<br/>
        AT'N: {cotizacion['atencion_a'] or ''}<br/>
        <font color="#D20000"><b>Referencia: {cotizacion['referencia'] or ''}</b></font>
    """
    elements.append(Paragraph(client_info, style_normal))
    elements.append(Spacer(1, 15))
    
    
    # --- ITEMS TABLE ---
    table_header = ['Línea', 'Cant.', 'Unidad', 'Clave', 'Descripción', 'Entrega', 'P. Unitario', 'Importe']
    data = [table_header]
    
    # Style for wrapping text in description column
    style_cell = ParagraphStyle('CellWrap', parent=styles['Normal'], fontSize=8, leading=10)
    
    for item in cotizacion['items']:
        # Wrap description in Paragraph for proper line wrapping
        desc_paragraph = Paragraph(item['descripcion'] or '', style_cell)
        clave_paragraph = Paragraph(item['numero_parte'] or '', style_cell)
        
        data.append([
            str(item['linea']),
            f"{item['cantidad']:.2f}",
            item['unidad'] or 'PZA',
            clave_paragraph,
            desc_paragraph,
            item['tiempo_entrega_item'] or '',
            f"${item['precio_unitario']:,.2f}",
            f"{cotizacion['moneda']} ${item['importe']:,.2f}"
        ])
    
    col_widths = [30, 35, 40, 65, 170, 50, 60, 70]
    items_table = Table(data, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Body
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Linea
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Cant
        ('ALIGN', (6, 1), (7, -1), 'RIGHT'),   # Prices
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),   # Changed to TOP for multi-line text
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor("#f8f8f8")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))
    
    # --- TOTALS ---
    totals_data = [
        ['Subtotal', f"{cotizacion['moneda']} ${cotizacion['subtotal']:,.2f}"],
        [f"IVA {int(cotizacion['iva_porcentaje']*100)}%", f"{cotizacion['moneda']} ${cotizacion['iva_monto']:,.2f}"],
        ['Total', f"{cotizacion['moneda']} ${cotizacion['total']:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[100, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 11),
        ('TEXTCOLOR', (0, 2), (-1, 2), INAIR_RED),
        ('LINEABOVE', (0, 2), (-1, 2), 1, INAIR_RED),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    # Right-align totals table
    totals_wrapper = Table([[Spacer(1,1), totals_table]], colWidths=[335, 200])
    elements.append(totals_wrapper)
    elements.append(Spacer(1, 20))
    
    # --- TERMS AND CONDITIONS ---
    elements.append(Paragraph("Términos y Condiciones Generales", style_section))
    elements.append(Paragraph(f"<font color='#D20000'><b>Términos de pago: {cotizacion['condiciones_pago'] or '15 días'}</b></font>", style_normal))
    elements.append(Spacer(1, 8))
    
    terms = f"""
    <b>MONEDA:</b> Precios cotizados en {cotizacion['moneda']} pagaderos en {cotizacion['moneda']} o en moneda nacional al tipo de cambio del D.O.F. vigente el día del pago.<br/><br/>
    <b>TIEMPO DE ENTREGA:</b> {cotizacion['tiempo_entrega'] or 'Aplica a partir de la recepción de la Orden de Compra. Sujeto a cambio sin previo aviso por parte de fábrica.'}<br/><br/>
    <b>GARANTÍA EN PARTES:</b> La garantía es por 6 meses y solo por defectos de fabricación.<br/><br/>
    <b>INDICACIONES:</b> Enviar su Orden de Compra a pedidos@inair.com.mx indicando el número de cotización.
    """
    if cotizacion['notas']:
        terms += f"<br/><br/><b>NOTAS:</b> {cotizacion['notas']}"
    
    elements.append(Paragraph(terms, style_small))
    elements.append(Spacer(1, 30))
    
    # --- VENDEDOR/COTIZADOR INFO (centered at end) ---
    style_center = ParagraphStyle('CenterVendedor', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)
    
    # Logic to get the correct vendor (Deal Owner > Cotizador)
    vendedor_id = None
    
    # 1. Try to find linked deal
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT deal_id FROM crm_deal_cotizaciones WHERE cotizacion_id = ?", (cotizacion_id,))
        row = c.fetchone()
        if row:
            deal_id = row[0]
            # Get deal's vendor
            c.execute("SELECT vendedor_id FROM crm_deals WHERE id = ?", (deal_id,))
            deal_row = c.fetchone()
            if deal_row:
                vendedor_id = deal_row[0]
        conn.close()
    except Exception as e:
        print(f"Error fetching deal vendor: {e}")
        
    # 2. Fallback to existing logic if no deal vendor found
    if not vendedor_id:
        vendedor_id = cotizacion.get('vendedor_id') or cotizacion.get('cotizador_id')
        
    if vendedor_id:
        vendedor = get_user_by_id(vendedor_id)
        if vendedor:
            vendedor_info = f"""
                <b>{vendedor.get('nombre', vendedor.get('username', 'N/A'))}</b><br/>
                Tel: {vendedor.get('telefono', 'N/A')}<br/>
                {vendedor.get('email', 'N/A')}
            """
            elements.append(Paragraph(vendedor_info, style_center))
            elements.append(Spacer(1, 20))
        
    # --- BUILD PDF with Footer ---
    def add_footer(canvas_obj, doc_obj):
        canvas_obj.saveState()
        # Footer line
        canvas_obj.setStrokeColor(INAIR_RED)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(40, 70, letter[0] - 40, 70)
        
        # Company info
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(40, 55, "INGENIERÍA EN AIRE SA DE CV  RFC: IAI160525806")
        canvas_obj.drawString(40, 45, "Avenida Alfonso Vidal y Planas #445, Interior S/N, Colonia Nueva Tijuana, Tijuana, Baja California, México, Cp: 22435")
        canvas_obj.drawString(40, 35, "Tel: (664) 250-0022 | pedidos@inair.com.mx | www.inair.com.mx")
        canvas_obj.restoreState()
    
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer.getvalue()

@app.route("/admin/cotizaciones/pdf/<int:id>")
@require_permission("cotizaciones")
def admin_cotizaciones_pdf(id):
    """Generate professional PDF for quotation"""
    pdf_bytes = generate_cotizacion_pdf_bytes(id)
    if not pdf_bytes:
        return "Cotización no encontrada", 404
    
    buffer = io.BytesIO(pdf_bytes)
    cotizacion = get_cotizacion_by_id(id)
    
    # Check if download mode
    is_download = request.args.get('download') == 'true'
    return send_file(buffer, as_attachment=is_download, 
                     download_name=f"Cotizacion_{cotizacion['folio']}.pdf" if is_download else None, 
                     mimetype='application/pdf')


# ==================== CRM MODULE ====================

# ==================== CRM MODULE ====================

@app.route("/admin/crm")
@require_permission("crm")
def admin_crm():
    """CRM Kanban Dashboard - shows stages based on user's puesto"""
    # Refresh user data from database to get latest puesto/role
    user = get_user_by_username(session.get("user"))
    if user:
        session["puesto"] = user.get("puesto", "")
        session["role"] = user.get("role", "technician")
    
    user_id = session.get("user_id")
    role = session.get("role")
    puesto = session.get("puesto")
    
    # Get all puestos that have CRM stages configured
    all_stages = get_all_puesto_stages()
    available_puestos = list(set([s['puesto'] for s in all_stages]))
    available_puestos.sort()
    
    # Admin and Director can choose which puesto to view (via query parameter)
    if role == "admin" or compare_ignore_case(puesto, "director"):
        # Allow admin to select which puesto CRM to view
        selected_puesto = request.args.get('puesto', 'Vendedor')
        
        # Verify the selected puesto exists
        if selected_puesto not in available_puestos and available_puestos:
            selected_puesto = available_puestos[0]
        
        deals = get_all_deals()
        activities = get_pending_activities()
        puesto_stages = get_stages_by_puesto(selected_puesto)
        stages = [s['stage_name'] for s in puesto_stages] if puesto_stages else CRM_STAGES
        all_puesto_stages = puesto_stages if puesto_stages else []
        is_admin_view = True
        view_puesto = selected_puesto
    # Gerente de Ventas sees all Vendedor stages and all deals
    elif compare_ignore_case(puesto, "Gerente de Ventas"):
        deals = get_all_deals()
        activities = get_pending_activities()
        puesto_stages = get_stages_by_puesto("Vendedor")
        stages = [s['stage_name'] for s in puesto_stages] if puesto_stages else CRM_STAGES
        all_puesto_stages = puesto_stages if puesto_stages else []
        is_admin_view = True
        view_puesto = "Vendedor"
    # Other puestos (Vendedor, Cotizador, Ger. Servicios) see their own stages
    else:
        # IMPORTANTE: Técnico de Servicio debe usar los mismos stages que Gerente de Servicios Técnicos
        if compare_ignore_case(puesto, "Técnico de Servicio"):
            # Usar los stages del Gerente de Servicios Técnicos
            puesto_stages = get_stages_by_puesto("Gerente de Servicios Técnicos")
            if puesto_stages:
                stages = [s['stage_name'] for s in puesto_stages]
                all_puesto_stages = puesto_stages
            else:
                # Fallback si no hay stages configurados
                stages = ['Programado', 'Realizado', 'Requiere Cotización', 'Cotizado']
                all_puesto_stages = []
            # Técnico de Servicio ve solo los tratos de servicio asignados a él
            deals = get_deals_by_tecnico(user_id, tipo_deal='servicio')
            activities = get_pending_activities()  # TODO: Filtrar por técnico si es necesario
            is_admin_view = False
            view_puesto = "Gerente de Servicios Técnicos"  # Usar el mismo view_puesto para que vea el mismo CRM
        else:
            puesto_stages = get_stages_by_puesto(puesto)
            if puesto_stages:
                stages = [s['stage_name'] for s in puesto_stages]
            else:
                # Fallback: if no custom stages, use original behavior
                stages = CRM_STAGES
            
            # IMPORTANTE: Los vendedores solo ven sus propios tratos (filtrado por vendedor_id)
            # Otros puestos (Cotizador, etc.) ven todos los tratos en sus stages
            if compare_ignore_case(puesto, "Vendedor"):
                deals = get_deals_by_vendor(user_id)
                activities = get_pending_activities_by_vendor(user_id)
            else:
                # Para Cotizador y otros puestos: ver todos los tratos en sus stages
                deals = get_deals_by_puesto(puesto)
                activities = get_pending_activities()  # TODO: Filtrar por puesto si es necesario
            all_puesto_stages = puesto_stages if puesto_stages else []
            is_admin_view = False
            view_puesto = puesto
    
    # Get stage colors for template
    stage_colors = {s['stage_name']: s['color'] for s in all_puesto_stages}
    
    # Generate dynamic CRM title based on puesto
    # Para Técnico de Servicio, usar su propio título aunque view_puesto sea Gerente
    crm_titles = {
        'Vendedor': 'Ventas',
        'Cotizador': 'Cotización',
        'Gerente de Ventas': 'Ventas',
        'Gerente de Servicios Técnicos': 'Servicios Técnicos',
        'Técnico de Servicio': 'Servicios Técnicos',
        'Contador': 'Finanzas',
        'Administrador': 'Administración',
        'Director': 'Dirección',
    }
    # Si es Técnico de Servicio, usar su título aunque view_puesto sea diferente
    if compare_ignore_case(puesto, "Técnico de Servicio"):
        crm_title = crm_titles.get('Técnico de Servicio', 'Servicios Técnicos')
    else:
        crm_title = crm_titles.get(view_puesto, view_puesto)
    
    return render_template("admin_crm.html", 
                           deals=deals, 
                           stages=stages, 
                           pending_activities=activities, 
                           is_admin=is_admin_view,
                           stage_colors=stage_colors,
                           current_puesto=puesto,
                           view_puesto=view_puesto,
                           available_puestos=available_puestos,
                           crm_title=crm_title)

@app.route("/user/crm")
@require_permission("crm")
def user_crm():
    """Redirect to main CRM route (consolidated)"""
    return redirect(url_for("admin_crm"))

@app.route("/admin/crm/nuevo", methods=["GET", "POST"])
@require_permission("crm")
def admin_crm_nuevo():
    """Create new deal"""
    user_id = session.get("user_id")
    role = session.get("role")
    puesto = session.get("puesto")
    
    # Check if user is Gerente de Servicios Técnicos
    is_service_manager = puesto == "Gerente de Servicios Técnicos"
    
    if request.method == "POST":
        tipo_deal = request.form.get('tipo_deal', 'venta')
        
        # If Vendedor, force their ID. Else use form value.
        if role != "admin" and not in_list_ignore_case(puesto, ["Director", "Gerente de Ventas"]):
            vendedor_id_to_use = user_id
        else:
            vendedor_id_to_use = request.form.get('vendedor_id') or user_id

        # Obtener notas (priorizar notasJson si existe, sino usar notas)
        notas_value = request.form.get('notasJson') or request.form.get('notas') or ''
        
        data = {
            'cliente_id': request.form.get('cliente_id') or None,
            'contacto_nombre': request.form.get('contacto_nombre'),
            'vendedor_id': vendedor_id_to_use,
            'titulo': request.form.get('titulo'),
            'valor_estimado': float(request.form.get('valor_estimado') or 0),
            'moneda': request.form.get('moneda', 'USD'),
            'etapa': request.form.get('etapa', 'Prospecto'),
            'fecha_cierre_estimada': request.form.get('fecha_cierre_estimada') or None,
            'producto_servicio': request.form.get('producto_servicio'),
            'notas': notas_value,
            'email': request.form.get('email'),
            'firma_vendedor': request.form.get('firma_vendedor'),
            'mensaje_envio': request.form.get('mensaje_envio'),
            'tipo_deal': tipo_deal,
            'fecha_servicio': request.form.get('fecha_servicio') or None,
            'tiempo_estimado_horas': float(request.form.get('tiempo_estimado_horas') or 0) if request.form.get('tiempo_estimado_horas') else None
        }
        
        deal_id = create_deal(data)
        
        # Si hay cotizaciones vinculadas, recalcular valor estimado
        if deal_id:
            _update_deal_valor_estimado_from_cotizaciones(deal_id)
        
        if deal_id and tipo_deal == 'servicio':
            # Save equipments for service deals
            equipments_json = request.form.get('equipments')
            if equipments_json:
                import json
                try:
                    equipments = json.loads(equipments_json)
                    for idx, equip in enumerate(equipments):
                        add_equipo_to_deal(
                            deal_id, 
                            equip.get('tipo_equipo', ''),
                            equip.get('modelo', ''),
                            equip.get('serie', ''),
                            equip.get('descripcion_servicio', ''),
                            equip.get('detalles_adicionales', ''),
                            idx
                        )
                except Exception as e:
                    print(f"Error saving equipments: {e}")
            
            # Save technicians for service deals
            tecnicos_json = request.form.get('tecnicos')
            if tecnicos_json:
                import json
                try:
                    tecnicos = json.loads(tecnicos_json)
                    for tecnico in tecnicos:
                        tecnico_id = tecnico.get('tecnico_id')
                        puntos = int(tecnico.get('puntos', 0))
                        if tecnico_id:
                            assign_tecnico_to_deal(deal_id, tecnico_id, user_id, puntos)
                            # Create notification for assigned technician
                            create_notification(
                                user_id=tecnico_id,
                                tipo='servicio_asignado',
                                titulo='Nuevo Servicio Asignado',
                                mensaje=f'Has sido asignado al servicio: {data.get("titulo", "Sin título")}',
                                deal_id=deal_id
                            )
                except Exception as e:
                    print(f"Error saving technicians: {e}")
        
        if deal_id:
            # Get the created deal to show the generated folio
            created_deal = get_deal_by_id(deal_id)
            if created_deal and created_deal.get('folio'):
                # Redirect to edit page to show the folio
                return redirect(url_for('admin_crm_editar', id=deal_id))
            return redirect(url_for("admin_crm"))
    
    # GET request
    clients = get_all_clients()
    users = get_all_users()
    
    # Use puesto-specific stages for the form
    puesto_stages = get_stages_by_puesto(puesto) if puesto else []
    if puesto_stages:
        stages = puesto_stages  # Pass full objects for service form
    else:
        # For compatibility, create dict-like objects
        stages = [{'stage_name': s} for s in CRM_STAGES]
    
    cotizaciones = get_all_cotizaciones()
    
    # Pass flag to template to disable vendor selection if needed
    can_assign_vendor = (role == "admin" or in_list_ignore_case(puesto, ["Director", "Gerente de Ventas"]))
    
    # Get current module based on puesto
    current_module = get_current_module(puesto)
    
    # Get email content for this module (template or personalized)
    # For new deals, use template (no deal_id yet)
    mensaje_template = get_deal_email_content(None, current_module, 'mensaje') if None else None
    firma_template = get_deal_email_content(None, current_module, 'firma') if None else None
    
    # Get template directly for new deals
    template_mensaje = get_email_template(current_module, 'mensaje')
    template_firma = get_email_template(current_module, 'firma')
    
    mensaje_default = template_mensaje.get('default_content', '') if template_mensaje else ''
    firma_default = template_firma.get('default_content', '') if template_firma else ''
    
    # Get current user's signature for pre-loading (legacy compatibility)
    current_user = get_user_by_id(user_id)
    user_firma = current_user.get('firma_email', '') if current_user else ''
    
    # Get current user info for vendedor field
    current_user_info = get_user_by_id(user_id)
    
    # Choose template based on puesto
    if is_service_manager:
        return render_template("admin_crm_form_servicio.html", deal=None, clients=clients, 
                             users=users, stages=stages, can_assign_vendor=can_assign_vendor,
                             current_module=current_module, mensaje_default=mensaje_default, firma_default=firma_default,
                             current_user=current_user_info)
    else:
        # Extract stage names for regular form
        stage_names = [s.get('stage_name', s) if isinstance(s, dict) else s for s in stages]
        return render_template("admin_crm_form.html", deal=None, clients=clients, users=users, 
                             stages=stage_names, cotizaciones=cotizaciones, 
                             can_assign_vendor=can_assign_vendor, user_firma=user_firma,
                             current_module=current_module, mensaje_default=mensaje_default, firma_default=firma_default,
                             current_user=current_user_info)

@app.route("/admin/crm/editar/<int:id>", methods=["GET", "POST"])
@require_permission("crm")
def admin_crm_editar(id):
    """Edit existing deal"""
    deal = get_deal_by_id(id)
    if not deal:
        return "Trato no encontrado", 404
        
    user_id = session.get("user_id")
    role = session.get("role")
    puesto = session.get("puesto")
    
    # Check if this is a service deal
    tipo_deal = deal.get('tipo_deal', 'venta')
    
    # Verify ownership if restricted
    if role != "admin" and puesto not in ["Director", "Gerente de Ventas", "Gerente de Servicios Técnicos"]:
        if deal['vendedor_id'] != user_id:
            return "No tienes permiso para editar este trato", 403

    if request.method == "POST":
        # Obtener notas (priorizar notasJson si existe, sino usar notas)
        notas_value = request.form.get('notasJson') or request.form.get('notas') or ''
        
        # If Vendedor, keep existing vendor_id (or force theirs). 
        # If Admin/Director, allow change.
        if role != "admin" and not in_list_ignore_case(puesto, ["Director", "Gerente de Ventas", "Gerente de Servicios Técnicos"]):
            vendedor_id_to_use = deal['vendedor_id'] # Keep original
        else:
            vendedor_id_to_use = request.form.get('vendedor_id') or deal['vendedor_id']

        # Manejar subida de archivo OC del cliente
        oc_file_path = None
        if 'oc_cliente_file' in request.files:
            oc_file = request.files['oc_cliente_file']
            if oc_file and oc_file.filename:
                import os
                from werkzeug.utils import secure_filename
                from datetime import datetime
                
                # Crear directorio si no existe
                upload_dir = os.path.join('static', 'uploads', 'deals', 'oc_cliente')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generar nombre único
                filename = secure_filename(oc_file.filename)
                file_ext = os.path.splitext(filename)[1]
                unique_filename = f"oc_cliente_{id}_{int(datetime.now().timestamp())}{file_ext}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                # Guardar archivo
                oc_file.save(file_path)
                
                # Guardar ruta relativa (sin 'static/')
                oc_file_path = f"uploads/deals/oc_cliente/{unique_filename}"
        
        data = {
            'cliente_id': request.form.get('cliente_id') or None,
            'contacto_nombre': request.form.get('contacto_nombre'),
            'vendedor_id': vendedor_id_to_use,
            'titulo': request.form.get('titulo'),
            'valor_estimado': float(request.form.get('valor_estimado') or 0),
            'moneda': request.form.get('moneda', 'USD'),
            'etapa': request.form.get('etapa'),
            'fecha_cierre_estimada': request.form.get('fecha_cierre_estimada') or None,
            'producto_servicio': request.form.get('producto_servicio'),
            'notas': notas_value,
            'email': request.form.get('email'),
            'firma_vendedor': request.form.get('firma_vendedor'),
            'mensaje_envio': request.form.get('mensaje_envio'),
            'tipo_deal': request.form.get('tipo_deal', tipo_deal),
            'fecha_servicio': request.form.get('fecha_servicio') or None,
            'tiempo_estimado_horas': float(request.form.get('tiempo_estimado_horas') or 0) if request.form.get('tiempo_estimado_horas') else None
        }
        
        # Agregar oc_cliente_file_path si se subió un archivo
        if oc_file_path:
            data['oc_cliente_file_path'] = oc_file_path
        
        update_deal(id, data)
        
        # Si hay cotizaciones vinculadas, recalcular valor estimado
        _update_deal_valor_estimado_from_cotizaciones(id)
        
        # Handle equipment updates for service deals
        if tipo_deal == 'servicio':
            equipments_json = request.form.get('equipments')
            if equipments_json:
                import json
                try:
                    equipments = json.loads(equipments_json)
                    # Delete existing equipments and re-add (simple approach)
                    # In production, you might want a smarter diff-based update
                    existing = get_equipos_by_deal(id)
                    for eq in existing:
                        delete_equipo_deal(eq['id'])
                    
                    for idx, equip in enumerate(equipments):
                        add_equipo_to_deal(
                            id, 
                            equip.get('tipo_equipo', ''),
                            equip.get('modelo', ''),
                            equip.get('serie', ''),
                            equip.get('descripcion_servicio', ''),
                            equip.get('detalles_adicionales', ''),
                            idx
                        )
                except Exception as e:
                    print(f"Error updating equipments: {e}")
            
            # Handle technicians updates for service deals
            tecnicos_json = request.form.get('tecnicos')
            if tecnicos_json:
                import json
                try:
                    tecnicos = json.loads(tecnicos_json)
                    # Get existing technicians
                    existing_tecnicos = get_tecnicos_by_deal(id)
                    existing_ids = {t['tecnico_id'] for t in existing_tecnicos}
                    new_ids = {t.get('tecnico_id') for t in tecnicos if t.get('tecnico_id')}
                    
                    # Remove technicians that are no longer in the list
                    for existing in existing_tecnicos:
                        if existing['tecnico_id'] not in new_ids:
                            remove_tecnico_from_deal(id, existing['tecnico_id'])
                    
                    # Add or update technicians
                    for tecnico in tecnicos:
                        tecnico_id = tecnico.get('tecnico_id')
                        puntos = int(tecnico.get('puntos', 0))
                        if tecnico_id:
                            if tecnico_id in existing_ids:
                                # Update points
                                update_tecnico_puntos(id, tecnico_id, puntos)
                            else:
                                # Add new technician
                                assign_tecnico_to_deal(id, tecnico_id, user_id, puntos)
                                # Create notification
                                create_notification(
                                    user_id=tecnico_id,
                                    tipo='servicio_asignado',
                                    titulo='Nuevo Servicio Asignado',
                                    mensaje=f'Has sido asignado al servicio: {data.get("titulo", deal.get("titulo", "Sin título"))}',
                                    deal_id=id
                                )
                except Exception as e:
                    print(f"Error updating technicians: {e}")
        
        return redirect(url_for("admin_crm"))
    
    # GET request - show form
    clients = get_all_clients()
    users = get_all_users()
    
    # Use puesto-specific stages for the form
    puesto_stages = get_stages_by_puesto(puesto) if puesto else []
    if puesto_stages:
        stages = puesto_stages
    else:
        stages = [{'stage_name': s} for s in CRM_STAGES]
    
    cotizaciones = get_all_cotizaciones()
    
    can_assign_vendor = (role == "admin" or in_list_ignore_case(puesto, ["Director", "Gerente de Ventas"]))
    
    # Get current module based on puesto
    current_module = get_current_module(puesto)
    
    # Get email content for this deal and module
    mensaje = get_deal_email_content(id, current_module, 'mensaje')
    firma = get_deal_email_content(id, current_module, 'firma')
    
    # Get current user's signature for pre-loading (legacy compatibility)
    current_user = get_user_by_id(user_id)
    user_firma = current_user.get('firma_email', '') if current_user else ''
    
    # Get current user info for vendedor field
    current_user_info = get_user_by_id(user_id)
    
    # Get vendedor info for the deal if it exists
    vendedor_info = None
    if deal and deal.get('vendedor_id'):
        vendedor_info = get_user_by_id(deal['vendedor_id'])
    
    # Choose template based on deal type
    if tipo_deal == 'servicio':
        return render_template("admin_crm_form_servicio.html", deal=deal, clients=clients, 
                             users=users, stages=stages, can_assign_vendor=can_assign_vendor,
                             current_module=current_module, mensaje=mensaje, firma=firma,
                             current_user=current_user_info, vendedor_info=vendedor_info)
    else:
        # Extract stage names for regular form
        stage_names = [s.get('stage_name', s) if isinstance(s, dict) else s for s in stages]
        return render_template("admin_crm_form.html", deal=deal, clients=clients, users=users, 
                             stages=stage_names, cotizaciones=cotizaciones, 
                             can_assign_vendor=can_assign_vendor, user_firma=user_firma,
                             current_module=current_module, mensaje=mensaje, firma=firma,
                             current_user=current_user_info, vendedor_info=vendedor_info)

@app.route("/admin/crm/ver/<int:id>")
@require_permission("crm")
def admin_crm_ver(id):
    """View deal details (read-only with generate quote option)"""
    deal = get_deal_by_id(id)
    if not deal:
        return "Trato no encontrado", 404
    
    # Check if this is a service deal
    tipo_deal = deal.get('tipo_deal', 'venta')
    
    # Get client info if exists
    client = None
    if deal.get('cliente_id'):
        client = get_client_by_id(deal['cliente_id'])
    
    # If service deal, use service view
    if tipo_deal == 'servicio':
        user_id = session.get("user_id")
        
        # Check if current user is an assigned technician
        is_assigned_technician = is_tecnico_assigned_to_deal(id, user_id)
        
        # Get all users for technician assignment dropdown
        users = get_all_users()
        
        # Get linked reports for this deal
        linked_reports = get_reports_by_deal(id)
        
        # Debug: Print to console (remove in production)
        print(f"DEBUG: Deal ID: {id}, Found {len(linked_reports)} reports")
        for r in linked_reports:
            print(f"  - Folio: {r.get('folio')}, Status: {r.get('status')}")
        
        return render_template("admin_crm_view_servicio.html", 
                             deal=deal, 
                             client=client,
                             users=users,
                             linked_reports=linked_reports,
                             is_assigned_technician=is_assigned_technician)
    
    # Regular deal view (sales)
    # Get linked cotizaciones
    linked_cotizaciones = []
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT c.* FROM cotizaciones c
            JOIN crm_deal_cotizaciones dc ON c.id = dc.cotizacion_id
            WHERE dc.deal_id = ?
        """, (id,))
        linked_cotizaciones = [dict(row) for row in c.fetchall()]
        conn.close()
    except:
        pass
    
    # Get linked invoices (facturas) based on linked cotizaciones
    linked_facturas = []
    if linked_cotizaciones:
        try:
            cot_ids = [c['id'] for c in linked_cotizaciones]
            if cot_ids:
                placeholders = ','.join(['?'] * len(cot_ids))
                conn = sqlite3.connect(DATABASE)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query = f"SELECT * FROM facturas WHERE cotizacion_id IN ({placeholders}) ORDER BY created_at DESC"
                c.execute(query, tuple(cot_ids))
                linked_facturas = [dict(row) for row in c.fetchall()]
                conn.close()
        except Exception as e:
            print(f"Error fetching linked invoices: {e}")
            pass
    
    # Get linked PIs (Proforma Invoices)
    linked_pis = []
    try:
        linked_pis = get_pis_for_deal(id)
    except Exception as e:
        print(f"Error fetching linked PIs: {e}")
        pass
    
    # Add PIs to deal object for template compatibility
    deal['pis'] = linked_pis
    
    # Get activities
    activities = get_deal_activities(id)
    
    # Get current user's signature for pre-loading
    user_id = session.get("user_id")
    current_user = get_user_by_id(user_id)
    user_firma = current_user.get('firma_email', '') if current_user else ''
    
    # Get current module based on puesto
    puesto = session.get('puesto')
    current_module = get_current_module(puesto)
    
    # Get email content for this deal and module
    mensaje = get_deal_email_content(id, current_module, 'mensaje')
    firma = get_deal_email_content(id, current_module, 'firma')
    
    return render_template("admin_crm_view.html", deal=deal, client=client, 
                          linked_cotizaciones=linked_cotizaciones, linked_facturas=linked_facturas,
                          linked_pis=linked_pis, activities=activities, user_firma=user_firma,
                          current_module=current_module, mensaje=mensaje, firma=firma)

@app.route("/admin/crm/eliminar/<int:id>", methods=["POST"])
@require_permission("crm")
def admin_crm_eliminar(id):
    """Delete deal"""
    deal = get_deal_by_id(id)
    if not deal:
        return "Trato no encontrado", 404
        
    user_id = session.get("user_id")
    role = session.get("role")
    puesto = session.get("puesto")
    
    # Verify ownership if restricted
    if role != "admin" and puesto not in ["Director", "Gerente de Ventas"]:
        if deal['vendedor_id'] != user_id:
            return "No tienes permiso para eliminar este trato", 403
            
    delete_deal(id)
    return redirect(url_for("admin_crm"))

# CRM API Routes
@app.route("/api/crm/deals")
@require_permission("crm")
def api_crm_deals():
    """Get all deals as JSON"""
    user_id = session.get("user_id")
    role = session.get("role")
    puesto = session.get("puesto")
    
    if role == "admin" or in_list_ignore_case(puesto, ["Director", "Gerente de Ventas"]):
        deals = get_all_deals()
    else:
        deals = get_deals_by_vendor(user_id)
        
    return jsonify(deals)

@app.route("/api/crm/deal/<int:deal_id>/upload-oc", methods=["POST"])
@require_permission("crm")
def api_crm_deal_upload_oc(deal_id):
    """Upload OC (Orden de Compra) file for a deal"""
    try:
        # Verificar que el trato existe
        deal = get_deal_by_id(deal_id)
        if not deal:
            return jsonify({"success": False, "error": "Trato no encontrado"}), 404
        
        # Verificar permisos
        user_id = session.get("user_id")
        role = session.get("role")
        puesto = session.get("puesto")
        
        if role != "admin" and not in_list_ignore_case(puesto, ["Director", "Gerente de Ventas", "Gerente de Servicios Técnicos"]):
            if deal.get('vendedor_id') != user_id:
                return jsonify({"success": False, "error": "No autorizado"}), 403
        
        # Verificar que se envió un archivo
        if 'oc_cliente_file' not in request.files:
            return jsonify({"success": False, "error": "No se recibió ningún archivo"}), 400
        
        oc_file = request.files['oc_cliente_file']
        if not oc_file or not oc_file.filename:
            return jsonify({"success": False, "error": "No se seleccionó ningún archivo"}), 400
        
        # Validar tipo de archivo
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        filename = oc_file.filename.lower()
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return jsonify({"success": False, "error": "Solo se permiten archivos PDF, JPG, JPEG o PNG"}), 400
        
        # Validar tamaño (máximo 10MB) - leer solo para verificar, luego resetear
        file_content = oc_file.read()
        if len(file_content) > 10 * 1024 * 1024:
            return jsonify({"success": False, "error": "El archivo es demasiado grande. Máximo 10MB"}), 400
        
        # Resetear el archivo para poder guardarlo
        oc_file.seek(0)
        
        # Guardar archivo
        from werkzeug.utils import secure_filename
        upload_dir = os.path.join('static', 'uploads', 'deals', 'oc_cliente')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = os.path.splitext(oc_file.filename)[1]
        unique_filename = f"oc_cliente_{deal_id}_{int(datetime.now().timestamp())}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        oc_file.save(file_path)
        
        # Guardar ruta en base de datos
        oc_file_path = f"uploads/deals/oc_cliente/{unique_filename}"
        from database import update_deal
        update_deal(deal_id, {'oc_cliente_file_path': oc_file_path})
        
        return jsonify({
            "success": True,
            "message": "OC del cliente adjuntada correctamente",
            "file_path": oc_file_path
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:id>/etapa", methods=["POST"])
@require_permission("crm")
def api_crm_deal_etapa(id):
    """Update deal stage (for drag-drop) and execute triggers"""
    # Check permission first
    deal = get_deal_by_id(id)
    if not deal:
        return jsonify({"success": False, "error": "Not found"}), 404
        
    user_id = session.get("user_id")
    role = session.get("role")
    puesto = session.get("puesto")
    
    # Allow the user who owns the deal OR admins/directors OR service managers/technicians
    if role != "admin" and puesto not in ["Director", "Gerente de Ventas", "Gerente de Servicios Técnicos", "Técnico de Servicio"]:
        # For other puestos, they can move deals in their visible stages
        user_stages = get_stages_by_puesto(puesto)
        user_stage_names = [s['stage_name'] for s in user_stages]
        if deal['etapa'] not in user_stage_names:
            return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.json
    new_stage = data.get('etapa')
    view_puesto_from_request = data.get('view_puesto')  # Puesto de la vista (para admins)
    
    # Validate stage: must be in either global CRM_STAGES or any puesto's stages
    all_stages = get_all_puesto_stages()
    valid_stages = set(CRM_STAGES) | set(s['stage_name'] for s in all_stages)
    
    if new_stage and new_stage in valid_stages:
        old_stage = deal['etapa']
        
        # DETECTAR PUESTO PARA TRIGGERS
        # IMPORTANTE: Para triggers, necesitamos el puesto del usuario que está moviendo el trato
        # El trigger se busca usando: source_puesto (puesto del usuario) + source_stage (stage HACIA el cual se mueve)
        puesto_para_trigger = puesto
        
        # Si el usuario no tiene puesto (puede ser admin o vendedor sin puesto asignado)
        if not puesto or puesto == "" or puesto is None:
            # Opción 1: Obtener puesto desde parámetro de la vista (enviado desde frontend) - para admins
            if view_puesto_from_request:
                puesto_para_trigger = view_puesto_from_request
                print(f"🔍 Usuario sin puesto: usando puesto de la vista (frontend): '{view_puesto_from_request}'")
            else:
                # Opción 2: Detectar automáticamente qué puesto tiene el stage NUEVO (new_stage)
                # Esto es importante porque el trigger se busca usando el stage de destino
                for stage_info in all_stages:
                    if compare_ignore_case(stage_info['stage_name'], new_stage):
                        puesto_para_trigger = stage_info['puesto']
                        print(f"🔍 Usuario sin puesto: stage nuevo '{new_stage}' pertenece a puesto '{puesto_para_trigger}'")
                        break
                
                # Si no se encontró el puesto del stage nuevo, intentar con el stage anterior
                if not puesto_para_trigger or puesto_para_trigger == "":
                    for stage_info in all_stages:
                        if compare_ignore_case(stage_info['stage_name'], old_stage):
                            puesto_para_trigger = stage_info['puesto']
                            print(f"🔍 Usuario sin puesto: stage anterior '{old_stage}' pertenece a puesto '{puesto_para_trigger}'")
                            break
                
                # Si aún no se encontró, usar el primer puesto disponible o 'Vendedor' por defecto
                if not puesto_para_trigger or puesto_para_trigger == "":
                    available_puestos = list(set([s['puesto'] for s in all_stages]))
                    if available_puestos:
                        puesto_para_trigger = available_puestos[0]
                        print(f"🔍 Usuario sin puesto: usando primer puesto disponible: '{puesto_para_trigger}'")
                    else:
                        puesto_para_trigger = "Vendedor"
                        print(f"🔍 Usuario sin puesto: usando puesto por defecto: 'Vendedor'")
        
        # Actualizar puesto para usar en el resto de la función (envío de emails, etc.)
        puesto_original = puesto  # Guardar puesto original
        puesto = puesto_para_trigger  # Usar puesto detectado para triggers y emails
        
        # Check for triggers BEFORE updating stage
        print(f"\n{'='*60}")
        print(f"🔍 VERIFICANDO TRIGGER AUTOMÁTICO")
        print(f"{'='*60}")
        print(f"   Usuario: {session.get('user', 'N/A')} (role: {role})")
        print(f"   Puesto del usuario: '{puesto}'")
        print(f"   Puesto para trigger: '{puesto_para_trigger}'")
        print(f"   Stage seleccionado: '{new_stage}'")
        print(f"   Stage anterior: '{old_stage}'")
        
        # IMPORTANTE: Buscar trigger usando el stage NUEVO (source) y el puesto del usuario
        # El trigger se activa cuando se mueve HACIA new_stage desde cualquier stage anterior
        # Ejemplo: Si un Vendedor mueve a "Solicitud de Cotización", busca trigger con:
        #   source_puesto = "Vendedor", source_stage = "Solicitud de Cotización"
        trigger = get_trigger_for_stage(puesto_para_trigger, new_stage)
        
        if trigger:
            print(f"\n✅ TRIGGER ENCONTRADO Y ACTIVADO:")
            print(f"   Origen: {trigger['source_puesto']} -> '{trigger['source_stage']}'")
            print(f"   Destino: {trigger['target_puesto']} -> '{trigger['target_stage']}'")
            print(f"\n   El trato se moverá automáticamente a:")
            print(f"   '{trigger['target_stage']}' en el módulo '{trigger['target_puesto']}'")
            print(f"   (El stage '{new_stage}' será reemplazado por '{trigger['target_stage']}')")
            # Update to target stage (trigger takes precedence)
            update_deal_stage(id, trigger['target_stage'])
            print(f"\n✅ Trato actualizado a stage: '{trigger['target_stage']}'")
            # Note: The deal will now appear in target_puesto's view with target_stage
        else:
            print(f"\nℹ️  NO HAY TRIGGER definido para:")
            print(f"   {puesto_para_trigger} -> '{new_stage}'")
            print(f"   El trato se moverá al stage seleccionado: '{new_stage}'")
            # No trigger, update to the stage the user selected
            update_deal_stage(id, new_stage)
            print(f"✅ Trato actualizado a stage: '{new_stage}'")
        
        print(f"{'='*60}\n")
        
        # AUTO-SEND EMAIL based on user's puesto and stage
        email_sent = False
        email_error = None
        email_to = None
        cotizacion_folio = None
        factura_id = None
        factura_numero = None
        
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG: Trato movido a '{new_stage}' por usuario con puesto '{puesto}'")
        print(f"{'='*60}\n")
        
        # LÓGICA 1: CONTADOR envía FACTURA cuando mueve a "Enviado al Cliente"
        if compare_ignore_case(puesto, "Contador") and compare_ignore_case(new_stage, "Enviado al Cliente"):
            print(f"✅ Condición cumplida: Etapa='Enviado al Cliente' y Puesto='Contador'")
            deal = get_deal_by_id(id)
            
            # Get linked facturas from linked cotizaciones
            linked_facturas = []
            if deal and deal.get('cotizaciones'):
                try:
                    cot_ids = [c['id'] for c in deal['cotizaciones']]
                    if cot_ids:
                        placeholders = ','.join(['?'] * len(cot_ids))
                        conn = sqlite3.connect(DATABASE)
                        conn.row_factory = sqlite3.Row
                        c = conn.cursor()
                        query = f"SELECT * FROM facturas WHERE cotizacion_id IN ({placeholders}) ORDER BY created_at DESC"
                        c.execute(query, tuple(cot_ids))
                        linked_facturas = [dict(row) for row in c.fetchall()]
                        conn.close()
                except Exception as e:
                    print(f"Error fetching linked invoices: {e}")
            
            if linked_facturas:
                # Get most recent factura
                factura = linked_facturas[0]
                factura_id = factura['id']
                factura_numero = factura['numero_factura']
                print(f"✅ Factura encontrada: {factura_numero}")
                
                # Get client email from deal
                cliente_email = deal.get('email')
                email_to = cliente_email
                print(f"📧 Email del cliente: {cliente_email or 'NO CONFIGURADO ❌'}")
                
                if cliente_email and factura_id:
                    print(f"✅ Iniciando envío de email con factura...")
                    try:
                        # Get accountant info
                        contador = get_user_by_id(user_id)
                        contador_email = contador['email'] if contador else None
                        contador_nombre = contador['nombre'] if contador else 'Contador INAIR'
                        
                        # Get accountant SMTP credentials (if configured)
                        smtp_user = contador.get('email_smtp') if contador else None
                        smtp_password = contador.get('password_smtp') if contador else None
                        
                        print(f"\n🔍 DEBUG api_crm_deal_etapa - Datos del contador:")
                        print(f"   contador_id: {user_id}")
                        print(f"   contador_nombre: '{contador_nombre}'")
                        print(f"   contador_email (regular): '{contador_email}'")
                        print(f"   smtp_user (email_smtp): '{smtp_user}'")
                        print(f"   smtp_password configurada: {'Sí' if smtp_password else 'No'}")
                        
                        # Get message from draft (NUEVO: usar borrador del chat)
                        from database import get_email_draft
                        draft = get_email_draft(id, 'factura', factura_id)
                        
                        if draft:
                            mensaje = draft.get('mensaje', '')
                            asunto = draft.get('asunto')
                            # TODO: Cargar adjuntos del borrador si existen
                        else:
                            # Fallback: usar campos antiguos del deal (compatibilidad)
                            mensaje = deal.get('mensaje_envio', '')
                            asunto = None
                        
                        # Get signature
                        firma = deal.get('firma_vendedor')  # Reuse same field for now
                        firma_imagen = contador.get('firma_imagen') if contador else None
                        
                        # Send email with PDF
                        from email_sender import send_factura_pdf
                        print(f"📧 Llamando a send_factura_pdf con:")
                        print(f"   factura_id: {factura_id}")
                        print(f"   cliente_email: '{cliente_email}'")
                        print(f"   contador_email: '{contador_email}'")
                        print(f"   smtp_user: '{smtp_user}'")
                        print(f"   deal_id: {id}")
                        send_factura_pdf(
                            factura_id, 
                            cliente_email,
                            contador_email=contador_email,
                            contador_nombre=contador_nombre,
                            firma_contador=firma,
                            mensaje_personalizado=mensaje,
                            smtp_user=smtp_user,
                            smtp_password=smtp_password,
                            firma_imagen=firma_imagen,
                            deal_id=id,  # Para guardar historial de emails
                            subject=asunto  # Usar asunto del borrador si existe
                        )
                        
                        # Delete draft after sending
                        if draft:
                            from database import delete_email_draft
                            delete_email_draft(id, 'factura', factura_id)
                            print(f"✅ Borrador eliminado después de envío")
                        print(f"✅ PDF de factura {factura_numero} enviado a {cliente_email}")
                        email_sent = True
                    except Exception as e:
                        print(f"❌ Error enviando PDF de factura: {e}")
                        email_error = str(e)
                        import traceback
                        traceback.print_exc()
                else:
                    if not cliente_email:
                        print(f"❌ ERROR: No se puede enviar email - Email del cliente NO configurado")
                        email_error = "Email del cliente no configurado"
                    if not factura_id:
                        print(f"❌ ERROR: No se puede enviar email - No hay factura vinculada")
                        email_error = "No hay factura vinculada"
            else:
                print(f"❌ ERROR: El trato no tiene facturas vinculadas")
                email_error = "No hay factura vinculada"
        
        # LÓGICA 2: VENDEDOR mueve a "Cotización enviada" - YA NO ENVÍA AUTOMÁTICAMENTE
        # El envío ahora se hace exclusivamente con el botón "Enviar desde ERP"
        elif compare_ignore_case(puesto, "Vendedor") and compare_ignore_case(new_stage, "Cotización enviada"):
            print(f"✅ Condición cumplida: Etapa='Cotización enviada' y Puesto='Vendedor'")
            print(f"ℹ️  El envío de correo ahora se hace exclusivamente con el botón 'Enviar desde ERP'")
            print(f"   No se enviará correo automáticamente al cambiar de etapa")
            # No se envía correo automáticamente - el usuario debe usar el botón "Enviar desde ERP"
        else:
            # No hay envío automático para este puesto/etapa
            if compare_ignore_case(new_stage, "Enviado al Cliente"):
                if not compare_ignore_case(puesto, "Contador"):
                    print(f"ℹ️  Puesto '{puesto}' no envía facturas automáticamente (requiere 'Contador')")
            elif compare_ignore_case(new_stage, "Cotización enviada"):
                if not compare_ignore_case(puesto, "Vendedor"):
                    print(f"ℹ️  Puesto '{puesto}' no envía cotizaciones automáticamente (requiere 'Vendedor')")
            else:
                print(f"ℹ️  Etapa '{new_stage}' no requiere envío automático")
        
        # Crear OCu cuando se mueve a Ganado (idempotente)
        ocu_created = False
        ocu_message = None
        ocu_id_resp = None
        if compare_ignore_case(new_stage, "Ganado"):
            refreshed_deal = get_deal_by_id(id)
            if refreshed_deal:
                try:
                    created, msg, ocu_created_id = create_ocu_from_deal(refreshed_deal)
                    ocu_created = created
                    ocu_message = msg
                    ocu_id_resp = ocu_created_id
                    print(f"🔄 OCu: {msg} (ocu_id={ocu_created_id})")
                except Exception as e:
                    ocu_message = f"Error creando OCu: {e}"
                    print(ocu_message)
            else:
                ocu_message = "No se pudo refrescar el trato para crear OCu."

        # Return response (trigger was already handled above)
        response_data = {
            "success": True,
            "email_sent": email_sent,
            "email_to": email_to,
            "cotizacion_folio": cotizacion_folio,
            "factura_numero": factura_numero,
            "email_error": email_error,
            "ocu_created": ocu_created,
            "ocu_message": ocu_message,
            "ocu_id": ocu_id_resp
        }
        
        # Add trigger info if it was activated
        if trigger:
            response_data["triggered"] = True
            response_data["target_stage"] = trigger['target_stage']
            response_data["target_puesto"] = trigger['target_puesto']
            print(f"✅ Respuesta incluye información del trigger: {trigger['target_puesto']} -> {trigger['target_stage']}")
        else:
            response_data["triggered"] = False
        
        return jsonify(response_data)
    return jsonify({"success": False, "error": "Invalid stage"}), 400

@app.route("/api/crm/deal/<int:id>/actividad", methods=["POST"])
@require_permission("crm")
def api_crm_deal_actividad(id):
    """Add activity to deal"""
    # Check permission
    deal = get_deal_by_id(id)
    if not deal:
        return jsonify({"success": False, "error": "Not found"}), 404
        
    user_id = session.get("user_id")
    role = session.get("role")
    puesto = session.get("puesto")
    
    if role != "admin" and puesto not in ["Director", "Gerente de Ventas"]:
        if deal['vendedor_id'] != user_id:
             return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.json
    activity_id = create_activity(id, data)
    if activity_id:
        return jsonify({"success": True, "id": activity_id})
    return jsonify({"success": False}), 400

@app.route("/api/crm/actividad/<int:id>/completar", methods=["POST"])
@require_permission("crm")
def api_crm_actividad_completar(id):
    """Mark activity as complete"""
    mark_activity_complete(id, True)
    return jsonify({"success": True})

@app.route("/api/crm/actividad/<int:id>", methods=["DELETE"])
@require_role("admin")
def api_crm_actividad_eliminar(id):
    """Delete activity"""
    delete_activity(id)
    return jsonify({"success": True})

# ==================== API ENDPOINTS: MENSAJES INTERNOS (FASE 1) ====================

@app.route("/api/crm/deal/<int:deal_id>/messages", methods=["GET"])
@require_permission("crm")
def api_get_deal_messages(deal_id):
    """Get all messages for a deal"""
    try:
        messages = get_deal_messages(deal_id)
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:deal_id>/messages", methods=["POST"])
@require_permission("crm")
def api_create_deal_message(deal_id):
    """Create a new message in a deal (supports attachments)"""
    try:
        user_id = session.get("user_id")
        
        # Support both JSON (backward compat) and form-data (with files)
        if request.is_json:
            data = request.json
            mensaje = data.get("mensaje", "").strip()
            files = []
        else:
            # Form data with files
            mensaje = request.form.get("mensaje", "").strip()
            # Get files
            files = []
            file_keys = [k for k in request.files.keys() if k.startswith('attachment')]
            for key in file_keys:
                file_storage = request.files[key]
                if file_storage and file_storage.filename:
                    files.append(file_storage)
        
        if not mensaje and not files:
            return jsonify({"success": False, "error": "Mensaje vacío y sin adjuntos"}), 400
        
        # Process attachments if any
        saved_attachments = []
        
        if files:
            # Validate attachments
            is_valid, error_msg, total_size = validate_attachments(files)
            if not is_valid:
                return jsonify({"success": False, "error": error_msg}), 400
            
            # Save attachments
            for file_storage in files:
                try:
                    att_data = save_attachment(file_storage, subfolder='messages')
                    saved_attachments.append(att_data)
                    print(f"   📎 Archivo guardado: {att_data['original_name']} ({format_file_size(att_data['size'])})")
                except Exception as e:
                    print(f"   ❌ Error guardando adjunto: {e}")
                    return jsonify({"success": False, "error": f"Error guardando adjunto: {str(e)}"}), 400
        
        # Create message
        message_id = create_deal_message(deal_id, user_id, mensaje or "(mensaje con adjuntos)")
        
        # Save attachment records linked to this message
        for att_data in saved_attachments:
            try:
                create_attachment(
                    owner_type='internal_message',
                    owner_id=message_id,
                    filename=os.path.basename(att_data['file_path']),
                    original_name=att_data['original_name'],
                    mime_type=att_data['mime_type'],
                    size=att_data['size'],
                    file_path=att_data['file_path'],
                    created_by=user_id
                )
            except Exception as e:
                print(f"   ⚠️ Error guardando registro de adjunto: {e}")
        
        return jsonify({
            "success": True, 
            "message_id": message_id,
            "attachments_count": len(saved_attachments)
        })
    except Exception as e:
        print(f"Error creando mensaje: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/message/<int:message_id>", methods=["DELETE"])
@require_permission("crm")
def api_delete_deal_message(message_id):
    """Delete a message"""
    try:
        # TODO: Add permission check (only message owner or admin)
        success = delete_deal_message(message_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== EMAIL CHAT ENDPOINTS ====================

@app.route("/api/crm/deal/<int:deal_id>/email-chat", methods=["GET"])
@require_permission("crm")
def api_get_email_chat(deal_id):
    """Get all emails for a deal to display in chat format"""
    try:
        from database import get_deal_emails, get_deal_email_drafts, get_deal_by_id
        
        # Get deal info to filter emails by client relationship
        deal = get_deal_by_id(deal_id)
        if not deal:
            return jsonify({"success": False, "error": "Trato no encontrado"}), 404
        
        # Get client email for filtering
        client_email = deal.get('email', '').lower().strip() if deal.get('email') else ''
        
        # Get sent/received emails
        emails = get_deal_emails(deal_id)
        
        # VERIFICACIÓN CRÍTICA PREVIA: Filtrar emails que no pertenecen a este deal_id (a prueba de errores)
        # Esto es una capa adicional de seguridad por si get_deal_emails retorna algo incorrecto
        emails_filtered = []
        for email in emails:
            email_deal_id = email.get('deal_id')
            if email_deal_id is None or email_deal_id != deal_id:
                # Si el deal_id es None o no coincide, EXCLUIR este email inmediatamente
                email_id = email.get('id')
                print(f"⚠️ ADVERTENCIA CRÍTICA: Email ID {email_id} tiene deal_id={email_deal_id} pero se esperaba {deal_id}. EXCLUIDO del chat.")
                continue
            emails_filtered.append(email)
        
        # Usar solo los emails filtrados
        emails = emails_filtered
        
        # Get drafts
        drafts = get_deal_email_drafts(deal_id)
        
        # Combine and format for chat display
        messages = []
        seen_email_ids = set()  # Para deduplicar por ID de BD
        seen_message_ids = set()  # Para deduplicar por Message-ID
        
        # Add emails with deduplication and client filtering
        from database import get_attachments
        for email in emails:
            email_id = email.get('id')
            message_id = email.get('message_id', '').strip().lower() if email.get('message_id') else None
            
            # VERIFICACIÓN CRÍTICA ADICIONAL: Doble verificación de deal_id (a prueba de errores)
            email_deal_id = email.get('deal_id')
            if email_deal_id is None or email_deal_id != deal_id:
                # Si el deal_id es None o no coincide, EXCLUIR este email inmediatamente
                print(f"⚠️ ADVERTENCIA CRÍTICA: Email ID {email_id} tiene deal_id={email_deal_id} pero se esperaba {deal_id}. EXCLUIDO.")
                continue
            
            # DEDUPLICACIÓN: Saltar si ya vimos este email por ID
            if email_id and email_id in seen_email_ids:
                continue
            if email_id:
                seen_email_ids.add(email_id)
            
            # DEDUPLICACIÓN: Saltar si ya vimos este email por Message-ID
            if message_id and message_id in seen_message_ids:
                continue
            if message_id:
                seen_message_ids.add(message_id)
            
            # FILTRO ADICIONAL: Excluir emails internos que no tienen relación con el cliente
            # Solo si el email no tiene asunto Y no está relacionado con el cliente del trato
            remitente = (email.get('remitente') or '').lower()
            destinatario = (email.get('destinatario') or '').lower()
            asunto = email.get('asunto', '').strip()
            
            # Si el email no tiene asunto Y no involucra al email del cliente, probablemente es un email interno sin relación
            if not asunto and client_email:
                # Verificar si el email involucra al cliente
                involves_client = (client_email in remitente or client_email in destinatario)
                # Si no involucra al cliente, es probablemente un email interno sin relación - excluirlo
                if not involves_client:
                    continue
            
            # Load attachments for this email
            attachments = []
            if email_id:
                attachments = get_attachments('email', email_id)
            
            messages.append({
                'id': email_id,
                'type': 'email',
                'direccion': email.get('direccion') or email.get('direction', 'entrada'),
                'remitente': email.get('remitente') or email.get('from'),
                'destinatario': email.get('destinatario') or email.get('to'),
                'asunto': email.get('asunto') or email.get('subject'),
                'cuerpo': email.get('cuerpo') or email.get('body'),
                'created_at': email.get('created_at'),
                'attachments': attachments
            })
        
        # Add drafts (as pending messages)
        for draft in drafts:
            messages.append({
                'id': f"draft_{draft['id']}",
                'type': 'draft',
                'direccion': 'salida',
                'remitente': 'Yo',
                'asunto': draft.get('asunto'),
                'cuerpo': draft.get('mensaje'),
                'created_at': draft.get('updated_at') or draft.get('created_at'),
                'tipo_documento': draft.get('tipo_documento'),
                'documento_id': draft.get('documento_id'),
                'is_draft': True
            })
        
        # Sort by date (most recent first)
        messages.sort(key=lambda x: x.get('created_at') or '', reverse=True)
        
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:deal_id>/email-draft", methods=["POST"])
@require_permission("crm")
def api_save_email_draft(deal_id):
    """Save email draft (will be sent when deal moves to corresponding stage)"""
    try:
        from flask import session
        from database import save_email_draft, get_deal_by_id
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "Usuario no autenticado"}), 401
        
        # Get deal to determine document type
        deal = get_deal_by_id(deal_id)
        if not deal:
            return jsonify({"success": False, "error": "Trato no encontrado"}), 404
        
        # Determine tipo_documento and documento_id from deal
        tipo_documento = None
        documento_id = None
        
        # Check for cotización
        if deal.get('cotizaciones') and len(deal['cotizaciones']) > 0:
            tipo_documento = 'cotizacion'
            documento_id = deal['cotizaciones'][0]['id']
        # Check for factura (from linked cotizaciones)
        elif deal.get('cotizaciones'):
            try:
                cot_ids = [c['id'] for c in deal['cotizaciones']]
                if cot_ids:
                    import sqlite3
                    conn = sqlite3.connect(DATABASE)
                    conn.row_factory = sqlite3.Row
                    c = conn.cursor()
                    placeholders = ','.join(['?'] * len(cot_ids))
                    query = f"SELECT * FROM facturas WHERE cotizacion_id IN ({placeholders}) ORDER BY created_at DESC LIMIT 1"
                    c.execute(query, tuple(cot_ids))
                    factura_row = c.fetchone()
                    conn.close()
                    if factura_row:
                        tipo_documento = 'factura'
                        documento_id = factura_row['id']
            except Exception as e:
                print(f"Error checking facturas: {e}")
        # Check for PI
        if not tipo_documento and deal.get('pis') and len(deal['pis']) > 0:
            tipo_documento = 'pi'
            documento_id = deal['pis'][0]['id']
        
        if not tipo_documento:
            return jsonify({"success": False, "error": "No hay documento vinculado (cotización, factura, PI, etc.)"}), 400
        
        mensaje = request.form.get('mensaje', '').strip()
        asunto = request.form.get('asunto', '').strip()
        
        # Process attachments
        files = []
        file_keys = [k for k in request.files.keys() if k.startswith('attachment')]
        for key in file_keys:
            file_storage = request.files[key]
            if file_storage and file_storage.filename:
                files.append(file_storage)
        
        # Save attachments and get their IDs
        attachment_ids = []
        if files:
            # Import functions
            from file_utils import save_attachment, validate_attachments
            from database import create_attachment
            import os
            
            # Validate attachments
            is_valid, error_msg, total_size = validate_attachments(files)
            if not is_valid:
                return jsonify({"success": False, "error": error_msg}), 400
            
            for file_storage in files:
                try:
                    att_data = save_attachment(file_storage, subfolder='email_drafts')
                    att_id = create_attachment(
                        owner_type='email_draft',
                        owner_id=deal_id,  # Temporary, will be updated when sent
                        filename=os.path.basename(att_data['file_path']),
                        original_name=att_data['original_name'],
                        mime_type=att_data['mime_type'],
                        size=att_data['size'],
                        file_path=att_data['file_path'],
                        created_by=user_id
                    )
                    attachment_ids.append(att_id)
                except Exception as e:
                    print(f"   ⚠️ Error guardando adjunto: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Save draft
        draft_id = save_email_draft(
            deal_id=deal_id,
            tipo_documento=tipo_documento,
            documento_id=documento_id,
            mensaje=mensaje,
            asunto=asunto,
            adjuntos=attachment_ids if attachment_ids else None,
            created_by=user_id
        )
        
        return jsonify({
            "success": True,
            "draft_id": draft_id,
            "message": "Borrador guardado. Se enviará cuando muevas el trato a la etapa correspondiente."
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== API ENDPOINTS: NOTIFICACIONES ====================

@app.route("/api/notifications", methods=["GET"])
def api_get_notifications():
    """Get notifications for current user"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "error": "No autenticado"}), 401
        
        leido = request.args.get("leido")
        if leido is not None:
            leido = leido.lower() in ['true', '1', 'yes']
        
        notifications = get_user_notifications(user_id, leido=leido)
        unread_count = get_unread_notification_count(user_id)
        
        return jsonify({
            "success": True,
            "notifications": notifications,
            "unread_count": unread_count
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
def api_mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        success = mark_notification_read(notification_id)
        unread_count = get_unread_notification_count(session.get("user_id"))
        return jsonify({"success": success, "unread_count": unread_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/notifications/mark-all-read", methods=["POST"])
def api_mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "error": "No autenticado"}), 401
        
        success = mark_all_notifications_read(user_id)
        return jsonify({"success": success, "unread_count": 0})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/notifications/<int:notification_id>", methods=["DELETE"])
def api_delete_notification(notification_id):
    """Delete a notification"""
    try:
        success = delete_notification(notification_id)
        unread_count = get_unread_notification_count(session.get("user_id"))
        return jsonify({"success": success, "unread_count": unread_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== API ENDPOINTS: EMAIL HISTORY (FASE 2) ====================

@app.route("/api/crm/deal/<int:deal_id>/emails", methods=["GET"])
@require_permission("crm")
def api_get_deal_emails(deal_id):
    """Get email history for a specific deal (Maintain backward compat or redirect to threads?)"""
    # We'll keep this as is for now, but usually the UI will now call the thread endpoint
    try:
        emails = get_deal_emails(deal_id)
        return jsonify({"success": True, "emails": emails})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:deal_id>/threads", methods=["GET"])
@require_permission("crm")
def api_get_deal_threads(deal_id):
    """Get emails grouped by thread - FILTRADO ESTRICTO por deal_id"""
    try:
        print(f"\n📧 API GET DEAL THREADS - Deal #{deal_id}")
        print(f"{'='*60}")
        
        # FILTRAR ESTRICTAMENTE POR deal_id
        emails = get_deal_emails(deal_id)
        print(f"📧 Total emails para threads del trato #{deal_id}: {len(emails)}")
        
        # Verificar que todos pertenecen a este deal_id
        emails_wrong_deal = [e for e in emails if e.get('deal_id') != deal_id]
        if emails_wrong_deal:
            print(f"⚠️ ADVERTENCIA: {len(emails_wrong_deal)} emails con deal_id incorrecto en threads!")
            # Filtrar emails incorrectos
            emails = [e for e in emails if e.get('deal_id') == deal_id]
        
        # Group by thread_root_id (RFC-compliant) con fallback a thread_id
        threads_map = {}
        seen_email_ids = set()
        
        for email in emails:
            # Deduplicar emails por ID
            email_id = email.get('id')
            if email_id and email_id in seen_email_ids:
                print(f"   ⚠️ Email duplicado en threads: ID={email_id}, Asunto={email.get('asunto', '')[:50]}")
                continue
            if email_id:
                seen_email_ids.add(email_id)
            
            # CRÍTICO: Agrupar por thread_id PRIMERO (más estable y consistente)
            # thread_id se calcula del subject normalizado, por lo que es más confiable para agrupación
            email_thread_id = email.get('thread_id')
            email_thread_root = email.get('thread_root_id')
            
            # Usar thread_id como clave principal SIEMPRE (más estable)
            # Si no hay thread_id, usar thread_root_id como fallback
            # Si no hay ninguno, crear uno basado en subject normalizado
            if email_thread_id:
                t_id = email_thread_id
            elif email_thread_root:
                # Si solo hay thread_root_id, usarlo pero también crear thread_id del subject
                # para que emails futuros se agrupen correctamente
                t_id = email_thread_root
            else:
                # Fallback: crear thread_id del subject normalizado
                subject_norm = email.get('subject_norm') or email.get('asunto', '')
                from database import normalize_subject
                normalized = normalize_subject(subject_norm)
                t_id = normalized[:100] if normalized else f"thread_{email.get('id')}"
            
            if t_id not in threads_map:
                threads_map[t_id] = {
                    'thread_id': t_id,  # Clave principal para buscar después
                    'thread_root_id': email_thread_root,  # Guardar thread_root_id también
                    'subject': email.get('subject_norm') or email.get('asunto'),  # Usar subject normalizado si existe
                    'last_message_date': email.get('created_at'),
                    'message_count': 0,
                    'unread_count': 0,
                    'emails': []
                }
            
            threads_map[t_id]['emails'].append(email)
            threads_map[t_id]['message_count'] += 1
            if email.get('direccion') == 'entrada' and email.get('estado') == 'recibido':
                threads_map[t_id]['unread_count'] += 1
            
            # Update last message (emails come sorted DESC from get_deal_emails)
            if not threads_map[t_id].get('latest_email'):
                threads_map[t_id]['latest_email'] = email
                # Usar subject normalizado si existe, sino asunto original
                threads_map[t_id]['subject'] = email.get('subject_norm') or email.get('asunto')
        
        # Convert to list and sort by last message date (most recent first)
        threads = list(threads_map.values())
        threads.sort(key=lambda t: t['last_message_date'] or '', reverse=True)
        
        print(f"   ✅ {len(threads)} threads únicos encontrados para trato #{deal_id}")
        print(f"{'='*60}\n")
        
        return jsonify({"success": True, "threads": threads})
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERROR en api_get_deal_threads para deal #{deal_id}:")
        print(error_trace)
        return jsonify({"success": False, "error": str(e), "trace": error_trace}), 500

@app.route("/api/crm/deal/<int:deal_id>/thread-messages", methods=["GET"])
@require_permission("crm")
def api_get_thread_messages(deal_id):
    """Get all messages for a specific thread"""
    try:
        thread_id = request.args.get('thread_id')
        if not thread_id:
            return jsonify({"success": False, "error": "Missing thread_id"}), 400
        
        print(f"\n🔍 CONSULTA DE THREAD - Deal #{deal_id}, Thread: '{thread_id[:50]}'")
        print(f"{'='*60}")
            
        # FILTRAR ESTRICTAMENTE POR deal_id (no mezclar tratos)
        all_emails = get_deal_emails(deal_id)
        print(f"📧 Total emails en historial del trato #{deal_id}: {len(all_emails)}")
        
        # Verificar que todos los emails pertenecen a este deal_id
        emails_wrong_deal = [e for e in all_emails if e.get('deal_id') != deal_id]
        if emails_wrong_deal:
            print(f"⚠️ ADVERTENCIA: {len(emails_wrong_deal)} emails con deal_id incorrecto detectados!")
            for e in emails_wrong_deal[:3]:
                print(f"   - Email ID {e.get('id')}: deal_id={e.get('deal_id')} (esperado: {deal_id})")
        
        # Contar por dirección
        entrada_count = len([e for e in all_emails if e.get('direccion') == 'entrada'])
        salida_count = len([e for e in all_emails if e.get('direccion') == 'salida'])
        print(f"   - Entrada: {entrada_count}")
        print(f"   - Salida: {salida_count}")
        
        # Filter by thread_id (clave principal) o thread_root_id (fallback)
        # CRÍTICO: Buscar por thread_id primero porque es más estable y consistente
        thread_emails = []
        for e in all_emails:
            email_thread_id = e.get('thread_id')
            email_thread_root = e.get('thread_root_id')
            
            # Match si el thread_id pasado coincide con thread_id o thread_root_id del email
            # Esto cubre todos los casos: emails agrupados por thread_id o por thread_root_id
            if (email_thread_id and email_thread_id == thread_id) or \
               (email_thread_root and email_thread_root == thread_id):
                thread_emails.append(e)
        
        print(f"📧 Emails filtrados por thread_root_id/thread_id '{thread_id[:50] if thread_id else 'N/A'}': {len(thread_emails)}")
        if not thread_emails:
            # DEBUG: Mostrar qué thread_ids/thread_root_ids hay disponibles
            available_thread_roots = set(e.get('thread_root_id') for e in all_emails if e.get('thread_root_id'))
            available_thread_ids = set(e.get('thread_id') for e in all_emails if e.get('thread_id'))
            print(f"   ⚠️ Thread IDs disponibles (thread_root_id): {list(available_thread_roots)[:5]}")
            print(f"   ⚠️ Thread IDs disponibles (thread_id): {list(available_thread_ids)[:5]}")
        else:
            print(f"   ✅ Encontrados {len(thread_emails)} emails en el thread")
        
        if thread_emails:
            entrada_thread = len([e for e in thread_emails if e.get('direccion') == 'entrada'])
            salida_thread = len([e for e in thread_emails if e.get('direccion') == 'salida'])
            print(f"   - Entrada en thread: {entrada_thread}")
            print(f"   - Salida en thread: {salida_thread}")
            print(f"   - Ejemplos de asuntos: {[e.get('asunto', '')[:40] for e in thread_emails[:3]]}")
        else:
            print(f"⚠️ NO SE ENCONTRARON EMAILS PARA ESTE THREAD_ID")
            print(f"   Thread IDs disponibles en este trato: {list(set(e.get('thread_id', 'N/A') for e in all_emails if e.get('thread_id')))[:5]}")
        
        # ORDEN DESCENDENTE: más reciente primero (como Outlook/Gmail)
        thread_emails.sort(key=lambda x: x['created_at'], reverse=True)
        
        # LOGS DETALLADOS ANTES DE DEDUPLICACIÓN
        print(f"\n📊 DIAGNÓSTICO DE DUPLICADOS:")
        print(f"   Total emails antes de deduplicación: {len(thread_emails)}")
        email_ids = [e.get('id') for e in thread_emails if e.get('id')]
        message_ids = [e.get('message_id') for e in thread_emails if e.get('message_id')]
        print(f"   IDs únicos (DB): {len(set(email_ids))} de {len(email_ids)}")
        print(f"   Message-IDs únicos: {len(set(message_ids))} de {len(message_ids)}")
        
        # Detectar duplicados por ID de BD (más confiable)
        seen_db_ids = {}
        duplicates_by_id = []
        for email in thread_emails:
            db_id = email.get('id')
            if db_id:
                if db_id in seen_db_ids:
                    duplicates_by_id.append({
                        'id': db_id,
                        'asunto': email.get('asunto', '')[:50],
                        'created_at': email.get('created_at')
                    })
                else:
                    seen_db_ids[db_id] = email
        
        if duplicates_by_id:
            print(f"   ⚠️ DUPLICADOS POR ID DE BD ENCONTRADOS: {len(duplicates_by_id)}")
            for dup in duplicates_by_id[:3]:
                print(f"      - ID {dup['id']}: {dup['asunto']} ({dup['created_at']})")
        
        # DEDUPLICACIÓN ROBUSTA: Priorizar ID de BD, luego message_id
        seen_ids = set()
        unique_emails = []
        for email in thread_emails:
            # PRIORIDAD 1: ID de BD (más confiable)
            db_id = email.get('id')
            if db_id:
                if db_id in seen_ids:
                    print(f"   ⚠️ Email duplicado por ID de BD: ID={db_id}, asunto='{email.get('asunto', '')[:40]}'")
                    continue
                seen_ids.add(db_id)
                unique_emails.append(email)
            # PRIORIDAD 2: Message-ID (si no hay ID de BD)
            else:
                msg_id = email.get('message_id', '').lower().strip() if email.get('message_id') else None
                if msg_id:
                    if msg_id in seen_ids:
                        print(f"   ⚠️ Email duplicado por Message-ID: message_id={msg_id[:30]}, asunto='{email.get('asunto', '')[:40]}'")
                        continue
                    seen_ids.add(msg_id)
                    unique_emails.append(email)
                # PRIORIDAD 3: Fallback (solo si no hay ID ni message_id)
                else:
                    fallback_key = f"{email.get('created_at')}_{email.get('remitente')}_{email.get('asunto')}"
                    if fallback_key in seen_ids:
                        print(f"   ⚠️ Email duplicado por fallback: {fallback_key[:50]}")
                        continue
                    seen_ids.add(fallback_key)
                    unique_emails.append(email)
        
        if len(unique_emails) != len(thread_emails):
            print(f"   ⚠️ Se eliminaron {len(thread_emails) - len(unique_emails)} emails duplicados")
        
        # Load attachments for each email (después de deduplicación)
        for email in unique_emails:
            attachments = get_attachments('email', email['id'])
            email['attachments'] = attachments
        
        # LOG FINAL
        print(f"\n   ✅ RESULTADO FINAL:")
        print(f"      - Emails únicos: {len(unique_emails)}")
        print(f"      - IDs únicos: {len(set(e.get('id') for e in unique_emails if e.get('id')))}")
        print(f"      - Message-IDs únicos: {len(set(e.get('message_id') for e in unique_emails if e.get('message_id')))}")
        print(f"   ✅ Ordenados DESC (más reciente primero)")
        print(f"{'='*60}\n")
        
        # Limpiar HTML del cuerpo antes de enviar al frontend
        import re
        from html import unescape
        
        for email in unique_emails:
            cuerpo = email.get('cuerpo', '')
            if cuerpo and ('<' in cuerpo or '&lt;' in cuerpo):
                cuerpo = unescape(cuerpo)
                cuerpo = re.sub(r'<br\s*/?>', '\n', cuerpo, flags=re.IGNORECASE)
                cuerpo = re.sub(r'</?(div|p|span)[^>]*>', '\n', cuerpo, flags=re.IGNORECASE)
                cuerpo = re.sub(r'<[^>]+>', '', cuerpo)
                cuerpo = unescape(cuerpo)
                cuerpo = re.sub(r'[ \t]+', ' ', cuerpo)
                cuerpo = re.sub(r'\n{3,}', '\n\n', cuerpo).strip()
                email['cuerpo'] = cuerpo
        
        return jsonify({"success": True, "messages": unique_emails})
    except Exception as e:
        print(f"❌ ERROR en api_get_thread_messages: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:deal_id>/thread-read", methods=["POST"])
@require_permission("crm")
def api_mark_thread_read(deal_id):
    """Mark all emails in a thread as read"""
    try:
        data = request.json
        thread_id = data.get('thread_id')
        if not thread_id:
            return jsonify({"success": False, "error": "Missing thread_id"}), 400
            
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            UPDATE email_history
            SET estado = 'leido'
            WHERE deal_id = ? AND thread_id = ? AND direccion = 'entrada'
        ''', (deal_id, thread_id))
        conn.commit()
        conn.close()
            
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error marking thread read: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/emails/<int:email_id>", methods=["GET"])
@require_permission("crm")
def api_get_email_detail(email_id):
    """Get details of a specific email"""
    try:
        email = get_email_by_id(email_id)
        if email:
            return jsonify({"success": True, "email": email})
        return jsonify({"success": False, "error": "Email no encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:deal_id>/email-content", methods=["GET", "POST"])
@require_permission("crm")
def api_deal_email_content(deal_id):
    """Get or Save personalized email message and signature for a deal and module"""
    try:
        if request.method == "GET":
            # GET: Retrieve saved message and signature
            module = request.args.get('module', '').lower()
            if not module:
                return jsonify({"success": False, "error": "Module required"}), 400
            
            mensaje = get_deal_email_content(deal_id, module, 'mensaje')
            firma = get_deal_email_content(deal_id, module, 'firma')
            
            return jsonify({
                "success": True,
                "mensaje": mensaje or '',
                "firma": firma or ''
            })
        else:
            # POST: Save message and signature
            data = request.json
            module = data.get('module', '').lower()  # 'ventas', 'finanzas', etc.
            if not module:
                puesto = session.get('puesto')
                module = get_current_module(puesto)
            
            mensaje = data.get('mensaje')
            firma = data.get('firma')
            
            # Save to deal_email_messages
            create_or_update_deal_email_message(deal_id, module, mensaje, firma)
            
            return jsonify({"success": True, "module": module})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/users/by-puesto/<puesto>", methods=["GET"])
@require_permission("crm")
def api_get_users_by_puesto(puesto):
    """Get users by puesto and return their signatures"""
    try:
        users = get_all_users()
        # Filter by puesto (case-insensitive)
        matching_users = [u for u in users if compare_ignore_case(u.get('puesto', ''), puesto)]
        
        # Return users with their signatures
        result = []
        for user in matching_users:
            result.append({
                'id': user.get('id'),
                'nombre': user.get('nombre'),
                'email': user.get('email'),
                'firma_email': user.get('firma_email', ''),
                'firma_imagen': user.get('firma_imagen'),
                'puesto': user.get('puesto')
            })
        
        return jsonify({"success": True, "users": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/email-template/<module>", methods=["GET"])
@require_permission("crm")
def api_get_email_template(module):
    """Get email template for a module (mensaje and firma)"""
    try:
        # Get templates from email_templates table
        template_mensaje = get_email_template(module, 'mensaje')
        template_firma = get_email_template(module, 'firma')
        
        # Extract content from templates
        mensaje_content = ''
        firma_content = ''
        
        if template_mensaje:
            mensaje_content = template_mensaje.get('default_content', '')
        
        if template_firma:
            firma_content = template_firma.get('default_content', '')
        
        return jsonify({
            "success": True,
            "mensaje": mensaje_content,
            "firma": firma_content
        })
    except Exception as e:
        print(f"Error getting email template: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

def _get_original_quote_subject(deal_id):
    """Obtener el asunto original del primer email de cotización enviado para este trato.
    Esto asegura que todos los correos subsecuentes usen el mismo asunto base."""
    try:
        from database import get_deal_emails, normalize_subject
        
        # Obtener todos los emails del trato
        emails = get_deal_emails(deal_id)
        
        # Buscar el primer email de cotización enviado (direccion='salida', tipo='cotizacion' o con cotizacion_id)
        # Ordenar por fecha (más antiguo primero)
        emails_sorted = sorted(emails, key=lambda x: x.get('created_at', '') or '')
        
        for email in emails_sorted:
            # Buscar el email original de cotización (el primero enviado)
            if email.get('direccion') == 'salida':
                # Verificar si es de cotización (tiene cotizacion_id o el asunto contiene "Cotización")
                cotizacion_id = email.get('cotizacion_id')
                asunto = email.get('asunto', '') or email.get('subject', '')
                
                if cotizacion_id or ('cotización' in asunto.lower() or 'cotizacion' in asunto.lower()):
                    # Normalizar el asunto (quitar "Re: Re: Re:" múltiples)
                    subject_norm = normalize_subject(asunto)
                    print(f"📧 Asunto original de cotización encontrado: {subject_norm[:80]}")
                    return subject_norm
        
        # Si no se encuentra email de cotización, buscar cualquier email enviado (fallback)
        for email in emails_sorted:
            if email.get('direccion') == 'salida':
                asunto = email.get('asunto', '') or email.get('subject', '')
                if asunto:
                    subject_norm = normalize_subject(asunto)
                    print(f"📧 Usando asunto del primer email enviado (fallback): {subject_norm[:80]}")
                    return subject_norm
        
        # Si no hay emails, retornar None (se usará el fallback del deal)
        return None
    except Exception as e:
        print(f"⚠️ Error obteniendo asunto original: {e}")
        return None

@app.route("/api/crm/deal/<int:deal_id>/send-reply", methods=["POST"])
@require_permission("crm")
def api_send_email_reply(deal_id):
    """Send email reply to client from CRM (supports multiple recipients and attachments)"""
    try:
        user_id = session.get("user_id")
        
        # Support both JSON (backward compat) and form-data (with files)
        if request.is_json:
            data = request.json
            parent_email_id = data.get('parent_email_id')
            mensaje = data.get('mensaje', '').strip()
            destinatario_manual = data.get('destinatario', '').strip()
            cc = data.get('cc', '').strip()
            files = []
        else:
            # Form data with files
            parent_email_id = request.form.get('parent_email_id')
            mensaje = request.form.get('mensaje', '').strip()
            destinatario_manual = request.form.get('destinatario', '').strip()
            cc = request.form.get('cc', '').strip()
            # Get files
            files = []
            file_keys = [k for k in request.files.keys() if k.startswith('attachment')]
            for key in file_keys:
                file_storage = request.files[key]
                if file_storage and file_storage.filename:
                    files.append(file_storage)
        
        # Convertir parent_email_id a int si viene como string
        if parent_email_id:
            try:
                parent_email_id = int(parent_email_id)
            except (ValueError, TypeError):
                parent_email_id = None
        
        if not mensaje:
            return jsonify({"success": False, "error": "Mensaje vacío"}), 400
        
        # Get deal info
        deal = get_deal_by_id(deal_id)
        if not deal:
            return jsonify({"success": False, "error": "Trato no encontrado"}), 404
        
        # Get parent email to know who to reply to
        parent_email = get_email_by_id(parent_email_id) if parent_email_id else None
        
        # DEBUG: Log para diagnosticar threading
        print(f"\n{'='*60}")
        print(f"📧 PREPARANDO RESPUESTA - Threading Debug")
        print(f"{'='*60}")
        print(f"   Deal ID: {deal_id}")
        print(f"   Parent email_id recibido: {parent_email_id}")
        if parent_email:
            print(f"   ✅ Parent email encontrado (ID: {parent_email.get('id')})")
            print(f"   Parent message_id en BD: {parent_email.get('message_id', 'NO TIENE')[:80] if parent_email.get('message_id') else 'NO TIENE'}")
            print(f"   Parent thread_id: {parent_email.get('thread_id', 'NO TIENE')[:50] if parent_email.get('thread_id') else 'NO TIENE'}")
        else:
            print(f"   ⚠️ Parent email NO encontrado o parent_email_id es None")
        print(f"{'='*60}\n")
        
        # Get parent message_id and build References chain for email threading (CRÍTICO para agrupar en bandeja personal)
        parent_message_id = None
        references_chain = None
        if parent_email:
            # Obtener message_id del padre
            parent_message_id_raw = parent_email.get('message_id', '').strip() if parent_email.get('message_id') else None
            if parent_message_id_raw:
                # Limpiar y formatear message_id del padre
                parent_message_id = parent_message_id_raw.replace(' ', '').replace('\n', '').replace('\r', '')
                if not parent_message_id.startswith('<'):
                    parent_message_id = f'<{parent_message_id}>'
                print(f"🔗 Parent message_id encontrado: {parent_message_id[:50]}")
            else:
                print(f"⚠️ Parent email NO tiene message_id (ID: {parent_email.get('id')})")
            
            # Construir References: obtener todos los message_ids del thread en orden cronológico
            # Esto es CRÍTICO para que los clientes de correo agrupen correctamente
            if parent_email.get('thread_id') and parent_message_id:
                from database import get_deal_emails
                thread_emails = get_deal_emails(deal_id)
                # Filtrar por thread_id y ordenar por fecha (más antiguo primero)
                thread_messages = [e for e in thread_emails 
                                 if e.get('thread_id') == parent_email.get('thread_id') 
                                 and e.get('message_id')]
                thread_messages.sort(key=lambda x: x.get('created_at', ''))
                
                print(f"🔗 Thread encontrado: {len(thread_messages)} mensajes con message_id")
                
                # Construir cadena de References con todos los message_ids del thread
                message_ids = []
                for msg in thread_messages:
                    msg_id = msg.get('message_id', '').strip()
                    if msg_id:
                        # Asegurar formato correcto con < >
                        if not msg_id.startswith('<'):
                            msg_id = f'<{msg_id}>'
                        # Limpiar si tiene espacios o caracteres inválidos
                        msg_id = msg_id.replace(' ', '').replace('\n', '').replace('\r', '')
                        if msg_id and msg_id not in message_ids:  # Evitar duplicados
                            message_ids.append(msg_id)
                
                if message_ids:
                    references_chain = ' '.join(message_ids)
                    print(f"🔗 References chain construida: {len(message_ids)} message_ids")
                    print(f"   Primeros IDs: {message_ids[:2] if len(message_ids) >= 2 else message_ids}")
                elif parent_message_id:
                    # Fallback: si no hay cadena pero sí hay padre, usar solo el padre
                    references_chain = parent_message_id
                    print(f"🔗 References fallback: solo padre (no hay cadena completa)")
            elif parent_message_id:
                # Si no hay thread_id pero sí hay parent_message_id, usar solo el padre
                references_chain = parent_message_id
                print(f"🔗 References: solo padre (no hay thread_id)")
        
        # CRÍTICO: Si no hay parent_message_id pero hay parent_email, intentar usar el thread_id
        # Esto es importante para emails antiguos que no tienen message_id
        if not parent_message_id and parent_email and parent_email.get('thread_id'):
            # Intentar obtener el message_id más reciente del thread como referencia
            from database import get_deal_emails
            thread_emails = get_deal_emails(deal_id)
            thread_messages = [e for e in thread_emails 
                             if e.get('thread_id') == parent_email.get('thread_id') 
                             and e.get('message_id')]
            if thread_messages:
                # Ordenar por fecha (más reciente primero) y tomar el primero
                thread_messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                latest_msg = thread_messages[0]
                if latest_msg.get('message_id'):
                    parent_message_id = latest_msg.get('message_id').strip()
                    if not parent_message_id.startswith('<'):
                        parent_message_id = f'<{parent_message_id}>'
                    # Construir References con todos los message_ids del thread
                    thread_messages.sort(key=lambda x: x.get('created_at', ''))  # Ordenar cronológicamente
                    message_ids = []
                    for msg in thread_messages:
                        msg_id = msg.get('message_id', '').strip()
                        if msg_id:
                            if not msg_id.startswith('<'):
                                msg_id = f'<{msg_id}>'
                            msg_id = msg_id.replace(' ', '').replace('\n', '').replace('\r', '')
                            if msg_id and msg_id not in message_ids:
                                message_ids.append(msg_id)
                    if message_ids:
                        references_chain = ' '.join(message_ids)
                        print(f"🔗 Threading recuperado desde thread_id: {len(message_ids)} message_ids")
                    else:
                        references_chain = parent_message_id
                        print(f"🔗 Threading recuperado: solo message_id más reciente del thread")
        
        # CRÍTICO: Si NO hay parent_email (nuevo mensaje desde chat), usar el email original de cotización para threading
        if not parent_email or not parent_message_id:
            from database import get_deal_emails
            all_deal_emails = get_deal_emails(deal_id)
            emails_sorted = sorted(all_deal_emails, key=lambda x: x.get('created_at', '') or '')
            
            # Buscar el email original de cotización
            original_quote_email = None
            for email in emails_sorted:
                if email.get('direccion') == 'salida':
                    cotizacion_id = email.get('cotizacion_id')
                    asunto_email = email.get('asunto', '') or email.get('subject', '')
                    if cotizacion_id or ('cotización' in asunto_email.lower() or 'cotizacion' in asunto_email.lower()):
                        original_quote_email = email
                        break
            
            if original_quote_email:
                # Usar el message_id del email original como parent para threading
                original_message_id = original_quote_email.get('message_id', '').strip() if original_quote_email.get('message_id') else None
                if original_message_id:
                    if not original_message_id.startswith('<'):
                        original_message_id = f'<{original_message_id}>'
                    
                    # Si no hay parent_message_id, usar el del email original
                    if not parent_message_id:
                        parent_message_id = original_message_id
                        print(f"🔗 Usando message_id del email original de cotización para threading: {original_message_id[:50]}")
                    
                    # Construir References con todos los emails del thread (usando thread_id o thread_root_id)
                    thread_id_to_use = original_quote_email.get('thread_id') or original_quote_email.get('thread_root_id')
                    if thread_id_to_use:
                        thread_emails = [e for e in all_deal_emails 
                                       if (e.get('thread_id') == thread_id_to_use or e.get('thread_root_id') == thread_id_to_use)
                                       and e.get('message_id')]
                        thread_emails.sort(key=lambda x: x.get('created_at', ''))
                        
                        message_ids = []
                        for msg in thread_emails:
                            msg_id = msg.get('message_id', '').strip()
                            if msg_id:
                                if not msg_id.startswith('<'):
                                    msg_id = f'<{msg_id}>'
                                msg_id = msg_id.replace(' ', '').replace('\n', '').replace('\r', '')
                                if msg_id and msg_id not in message_ids:
                                    message_ids.append(msg_id)
                        
                        if message_ids:
                            references_chain = ' '.join(message_ids)
                            print(f"🔗 References chain construida desde email original: {len(message_ids)} message_ids")
                        elif not references_chain:
                            references_chain = original_message_id
                            print(f"🔗 References usando solo message_id del email original")
        
        # Determine recipient - use manual input first
        recipient_email = destinatario_manual
        if not recipient_email:
            recipient_email = deal.get('email')
        if not recipient_email and parent_email:
            recipient_email = parent_email['remitente'] if parent_email['direccion'] == 'entrada' else parent_email['destinatario']
        
        if not recipient_email:
            return jsonify({"success": False, "error": "No se pudo determinar el destinatario"}), 400
        
        # Get current user info
        user = get_user_by_id(user_id)
        smtp_user = user.get('email_smtp')
        smtp_password = user.get('password_smtp')
        
        # Determine sender email - MUST match the SMTP account used
        if smtp_user and smtp_password:
            sender_email = smtp_user
        else:
            sender_email = user.get('email') or 'ervin.moj@gmail.com'
            
        sender_name = user.get('nombre', 'INAIR')
        smtp_password = user.get('password_smtp')
        firma_email = user.get('firma_email', '')
        firma_imagen = user.get('firma_imagen')
        
        # Build subject - SIEMPRE usar el asunto original de la cotización para mantener threading unificado
        original_subject = _get_original_quote_subject(deal_id)
        
        if original_subject:
            # Usar el asunto original de la cotización (normalizado, sin múltiples "Re:")
            # Agregar "Re: " solo una vez si no lo tiene
            if not original_subject.lower().startswith('re:'):
                asunto = f"Re: {original_subject}"
            else:
                # Si ya tiene "Re:", usar directamente (ya está normalizado)
                asunto = original_subject
            print(f"📧 Asunto final usando cotización original: {asunto[:80]}")
        elif parent_email:
            # Fallback: si no hay asunto original, usar el del parent pero normalizado
            from database import normalize_subject
            parent_subject_norm = normalize_subject(parent_email.get('asunto', ''))
            if not parent_subject_norm.lower().startswith('re:'):
                asunto = f"Re: {parent_subject_norm}"
            else:
                asunto = parent_subject_norm
            print(f"📧 Asunto usando parent (fallback): {asunto[:80]}")
        else:
            # Último fallback: usar el título del deal
            asunto = f"Seguimiento - {deal['titulo']}"
            print(f"📧 Asunto usando título del deal (fallback): {asunto[:80]}")
        
        # Process attachments if any
        saved_attachments = []
        attachment_metadata = []
        
        if files:
            # Validate attachments
            is_valid, error_msg, total_size = validate_attachments(files)
            if not is_valid:
                return jsonify({"success": False, "error": error_msg}), 400
            
            # Save attachments
            for file_storage in files:
                try:
                    att_data = save_attachment(file_storage, subfolder='emails')
                    saved_attachments.append({
                        'path': os.path.join('static', 'uploads', att_data['file_path']),  # Para enviar email
                        'absolute_path': att_data['absolute_path'],  # Path absoluto en disco
                        'filename': att_data['original_name'],
                        'file_path': att_data['file_path']  # Path relativo para BD: "attachments/emails/..."
                    })
                    attachment_metadata.append({
                        'filename': att_data['original_name'],
                        'size': att_data['size'],
                        'mime_type': att_data['mime_type']
                    })
                    print(f"   📎 Archivo guardado: {att_data['original_name']} ({format_file_size(att_data['size'])})")
                except Exception as e:
                    print(f"   ❌ Error guardando adjunto: {e}")
                    return jsonify({"success": False, "error": f"Error guardando adjunto: {str(e)}"}), 400
        
        # Send email with CC support and attachments
        from email_sender import send_generic_email
        result = send_generic_email(
            recipient_email=recipient_email,
            asunto=asunto,
            mensaje=mensaje,
            sender_email=sender_email,
            sender_name=sender_name,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            firma_vendedor=firma_email,
            firma_imagen=firma_imagen,
            cc=cc,
            attachments=saved_attachments if saved_attachments else None,
            parent_message_id=parent_message_id,  # Para threading en bandeja personal
            references_chain=references_chain  # Cadena completa de References para threading correcto
        )
        
        if result and result.get('success'):
            # Normalize subject (evitar "Re: Re: Re:")
            from database import normalize_subject
            subject_norm = normalize_subject(asunto)
            # Construir subject correcto: "Re: " + subject_norm (solo un "Re:")
            if parent_email:
                # Si es respuesta, usar subject normalizado con un solo "Re:"
                asunto_final = f"Re: {subject_norm}" if not asunto.lower().startswith('re:') else asunto
            else:
                asunto_final = asunto
            
            # Generate thread_id from normalized subject
            thread_id = subject_norm[:100]
            
            # Get message_id from result
            message_id = result.get('message_id', '')
            
            # Calcular thread_root_id según RFC - SIEMPRE apuntar al email original de cotización
            thread_root_id = None
            
            # Buscar el email original de cotización para obtener su message_id o thread_root_id
            from database import get_deal_emails
            all_deal_emails = get_deal_emails(deal_id)
            emails_sorted = sorted(all_deal_emails, key=lambda x: x.get('created_at', '') or '')
            
            # Buscar el primer email de cotización enviado
            original_quote_email = None
            for email in emails_sorted:
                if email.get('direccion') == 'salida':
                    cotizacion_id = email.get('cotizacion_id')
                    asunto_email = email.get('asunto', '') or email.get('subject', '')
                    if cotizacion_id or ('cotización' in asunto_email.lower() or 'cotizacion' in asunto_email.lower()):
                        original_quote_email = email
                        break
            
            if original_quote_email:
                # Usar el thread_root_id o message_id del email original de cotización
                thread_root_id = original_quote_email.get('thread_root_id') or original_quote_email.get('message_id')
                if thread_root_id:
                    thread_root_id = str(thread_root_id).strip('<>')[:200]
                    print(f"🔗 Thread root ID desde email original de cotización: {thread_root_id[:50]}")
            
            # Fallback: si no se encontró email original, usar el del parent o subject_norm
            if not thread_root_id:
                if parent_email:
                    # Si hay parent, usar su thread_root_id o message_id
                    thread_root_id = parent_email.get('thread_root_id') or parent_email.get('message_id')
                    if not thread_root_id and parent_message_id:
                        thread_root_id = parent_message_id.strip('<>')
                if not thread_root_id:
                    # Último fallback: usar subject_norm
                    thread_root_id = subject_norm[:100]
                    print(f"🔗 Thread root ID usando subject_norm (fallback): {thread_root_id[:50]}")
            
            # Construir references para guardar (cadena completa)
            references_to_save = None
            if references_chain:
                references_to_save = references_chain
            elif parent_message_id:
                references_to_save = parent_message_id
            
            # Prepare adjuntos JSON for email_history (backward compat)
            adjuntos_json = None
            if attachment_metadata:
                import json
                adjuntos_json = json.dumps(attachment_metadata)
            
            # Save to email history with RFC threading fields
            email_id = create_email_record(
                deal_id=deal_id,
                direccion='salida',
                tipo='respuesta',
                asunto=asunto_final,
                cuerpo=mensaje[:5000],  # Guardar más contenido, pero sin HTML de firma
                remitente=sender_email,
                destinatario=recipient_email,
                adjuntos=adjuntos_json,
                cotizacion_id=None,
                estado='enviado',
                cc=cc,
                thread_id=thread_id,
                message_id=message_id[:200] if message_id else None,
                in_reply_to=parent_message_id.strip('<>') if parent_message_id else None,
                references=references_to_save,
                subject_raw=asunto_final,
                subject_norm=subject_norm,
                thread_root_id=thread_root_id[:200] if thread_root_id else None,
                direction='outbound',
                provider='outlook_imap'
            )
            
            # Save attachment records linked to this email
            for att_data, att_meta in zip(saved_attachments, attachment_metadata):
                try:
                    # Usar el file_path relativo de save_attachment (sin 'static/uploads' prefix)
                    # att_data['path'] incluye 'static/uploads', pero necesitamos solo el relativo
                    relative_path = att_data.get('file_path')  # Ya viene como "attachments/emails/..."
                    if not relative_path:
                        # Fallback: extraer el path relativo desde 'path'
                        full_path = att_data.get('path', '')
                        if 'static/uploads/' in full_path:
                            relative_path = full_path.replace('static/uploads/', '')
                        else:
                            relative_path = full_path
                    
                    create_attachment(
                        owner_type='email',
                        owner_id=email_id,
                        filename=os.path.basename(att_data.get('absolute_path', att_data.get('path', ''))),
                        original_name=att_meta['filename'],
                        mime_type=att_meta['mime_type'],
                        size=att_meta['size'],
                        file_path=relative_path,  # Guardar path relativo
                        created_by=user_id
                    )
                except Exception as e:
                    print(f"   ⚠️ Error guardando registro de adjunto: {e}")
            
            # Save to CRM Email Log (crm_email_messages)
            try:
                from database import save_crm_email_message
                from datetime import datetime
                
                # Get last message info for threading
                last_message = None
                if parent_email:
                    last_message = parent_email
                else:
                    # Get last email from log
                    from database import get_crm_email_messages
                    existing_messages = get_crm_email_messages(deal_id)
                    if existing_messages:
                        last_message = existing_messages[-1]  # Last message
                
                # Prepare threading headers
                in_reply_to = None
                references_header = None
                if last_message:
                    if last_message.get('message_id'):
                        in_reply_to = last_message['message_id']
                        # Build references: existing references + new message_id
                        existing_refs = last_message.get('references_header', '')
                        if existing_refs:
                            references_header = f"{existing_refs} {in_reply_to}"
                        else:
                            references_header = in_reply_to
                
                # Save to email log
                email_log_id = save_crm_email_message(
                    deal_id=deal_id,
                    direction='outbound',
                    from_email=sender_email,
                    to_emails=', '.join(recipient_emails),
                    cc_emails=cc if cc else None,
                    subject_raw=asunto,
                    message_id=None,  # Will be set after sending if available
                    in_reply_to=in_reply_to,
                    references_header=references_header,
                    date_ts=datetime.now(),
                    snippet=mensaje[:200],
                    body_html=mensaje if '<' in mensaje else None,
                    body_text=mensaje if '<' not in mensaje else None,
                    provider_uid=None
                )
                print(f"✅ Correo guardado en Email Log (ID: {email_log_id})")
            except Exception as e:
                print(f"⚠️ Error guardando en Email Log: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"📧 Respuesta guardada en historial del trato #{deal_id} (thread_id: {thread_id[:50]}...)")
            return jsonify({
                "success": True,
                "message": f"Respuesta enviada exitosamente{' con ' + str(len(saved_attachments)) + ' adjunto(s)' if saved_attachments else ''}",
                "attachments_count": len(saved_attachments)
            })
        else:
            return jsonify({"success": False, "error": "Error al enviar"}), 500
            
    except Exception as e:
        print(f"❌ Error enviando respuesta: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attachments/<int:attachment_id>", methods=["GET"])
@require_permission("crm")
def api_download_attachment(attachment_id):
    """Download an attachment"""
    try:
        attachment = get_attachment_by_id(attachment_id)
        if not attachment:
            return jsonify({"success": False, "error": "Adjunto no encontrado"}), 404
        
        # Build full path - file_path puede venir con o sin 'static/uploads' prefix
        file_path = attachment['file_path']
        if not file_path.startswith('static'):
            file_path = os.path.join('static', 'uploads', file_path)
        if not os.path.exists(file_path):
            # Intentar con absolute_path si está disponible
            if attachment.get('absolute_path') and os.path.exists(attachment['absolute_path']):
                file_path = attachment['absolute_path']
            else:
                return jsonify({"success": False, "error": "Archivo no encontrado en disco"}), 404
        
        # Send file with proper headers
        return send_file(
            file_path,
            as_attachment=True,
            download_name=attachment['original_name'],
            mimetype=attachment.get('mime_type') or 'application/octet-stream'
        )
    except Exception as e:
        print(f"Error descargando adjunto: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attachments/<int:attachment_id>/preview", methods=["GET"])
@require_permission("crm")
def api_preview_attachment(attachment_id):
    """Preview an attachment (for images)"""
    try:
        attachment = get_attachment_by_id(attachment_id)
        if not attachment:
            return jsonify({"success": False, "error": "Adjunto no encontrado"}), 404
        
        # Only allow preview for images
        mime_type = attachment.get('mime_type', '')
        if not mime_type.startswith('image/'):
            return jsonify({"success": False, "error": "Solo se pueden previsualizar imágenes"}), 400
        
        # Build full path - file_path puede venir con o sin 'static/uploads' prefix
        file_path = attachment['file_path']
        if not file_path.startswith('static'):
            file_path = os.path.join('static', 'uploads', file_path)
        if not os.path.exists(file_path):
            # Intentar con absolute_path si está disponible
            if attachment.get('absolute_path') and os.path.exists(attachment['absolute_path']):
                file_path = attachment['absolute_path']
            else:
                return jsonify({"success": False, "error": "Archivo no encontrado en disco"}), 404
        
        # Send file for preview (not as attachment)
        return send_file(
            file_path,
            mimetype=mime_type
        )
    except Exception as e:
        print(f"Error previsualizando adjunto: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:deal_id>/sync-emails", methods=["POST"])
@require_permission("crm")
def api_sync_deal_emails(deal_id):
    """Sync client email responses for a deal using IMAP"""
    import time
    start_time = time.time()
    
    try:
        print(f"\n{'='*60}")
        print(f"🔄 INICIANDO SINCRONIZACIÓN - Deal #{deal_id}")
        print(f"{'='*60}")
        
        # Obtener el último email enviado del trato para usar las credenciales del remitente
        existing_emails = get_deal_emails(deal_id)
        print(f"📧 Total emails en historial: {len(existing_emails)}")
        
        sent_emails = [e for e in existing_emails if e.get('direccion') == 'salida']
        print(f"📧 Emails enviados (salida): {len(sent_emails)}")
        
        if sent_emails:
            print(f"📧 Tipos de emails enviados: {[e.get('tipo') for e in sent_emails]}")
            print(f"📧 Remitentes encontrados: {[e.get('remitente') for e in sent_emails[:3]]}")
        else:
            print(f"⚠️ NO HAY EMAILS ENVIADOS EN EL HISTORIAL - Usando fallback al usuario actual")
        
        smtp_user = None
        smtp_password = None
        sender_name = "Usuario"
        last_sent = None
        
        if sent_emails:
            # Usar las credenciales del último email enviado
            last_sent = sent_emails[0]  # Ya vienen ordenados DESC
            sender_email_raw = last_sent.get('remitente', '')
            print(f"\n{'='*60}")
            print(f"🔍 ANÁLISIS DE EMAILS ENVIADOS")
            print(f"{'='*60}")
            print(f"📧 Total emails enviados encontrados: {len(sent_emails)}")
            print(f"📧 Último email enviado desde (raw): '{sender_email_raw}'")
            print(f"📧 Tipo del último email: {last_sent.get('tipo', 'N/A')}")
            print(f"📧 Asunto del último email: {last_sent.get('asunto', 'N/A')[:50]}...")
            
            # Extraer email limpio (puede venir como "Nombre <email>" o solo "email")
            import re
            sender_email_match = re.search(r'<(.+?)>', sender_email_raw)
            if sender_email_match:
                sender_email = sender_email_match.group(1).lower().strip()
                print(f"📧 Email extraído (de formato 'Nombre <email>'): '{sender_email}'")
            else:
                sender_email = sender_email_raw.lower().strip()
                print(f"📧 Email extraído (formato directo): '{sender_email}'")
            
            print(f"📧 Email normalizado para búsqueda: '{sender_email}'")
            print(f"{'='*60}\n")
        else:
            # No hay emails enviados en historial, usar usuario actual como fallback
            sender_email = ''
            sender_email_raw = ''
            user_id = session.get("user_id")
            user = get_user_by_id(user_id) if user_id else None
            default_email = ''
            if user:
                default_email = (user.get('email_smtp') or user.get('email') or '').lower().strip()
                sender_email = default_email
                sender_name = user.get('nombre', 'Usuario')
                smtp_user = user.get('email_smtp')
                smtp_password = user.get('password_smtp')
            print(f"⚠️ NO HAY EMAILS ENVIADOS EN EL HISTORIAL - Usando fallback al usuario actual: '{default_email}'")
        
        # Si ya tenemos credenciales del usuario actual (fallback), saltar búsqueda
        if smtp_user and smtp_password:
            print("✅ Usando credenciales del usuario actual (fallback) para sincronizar")
        else:
            # Buscar usuario que tiene este email configurado (si lo tenemos)
            # IMPORTANTE: Si hay múltiples usuarios con el mismo email, probar cada uno
            print(f"🔍 BUSCANDO USUARIO CON EMAIL: '{sender_email}'")
            all_users = get_all_users()
            print(f"📋 Total usuarios en sistema: {len(all_users)}")
            
            # Primero, encontrar TODOS los usuarios que coinciden
            matching_users = []
            for idx, u in enumerate(all_users, 1):
                user_email_smtp = u.get('email_smtp', '').lower().strip() if u.get('email_smtp') else ''
                user_email = u.get('email', '').lower().strip() if u.get('email') else ''
                user_nombre = u.get('nombre', 'Sin nombre')
                
                print(f"   [{idx}] Usuario: {user_nombre}")
                print(f"       email_smtp='{user_email_smtp}'")
                print(f"       email='{user_email}'")
                
                # Comparación exacta (case-insensitive)
                match_smtp = sender_email == user_email_smtp
                match_email = sender_email == user_email
                
                if match_smtp or match_email:
                    matching_users.append(u)
                    match_type = "email_smtp" if match_smtp else "email"
                    print(f"       ✅ Coincidencia encontrada ({match_type})")
                else:
                    print(f"       ❌ No coincide")
            
            # Si hay múltiples usuarios con el mismo email, priorizar:
            # 1. El que tiene password_smtp configurada
            # 2. El que tiene puesto "Contador" (si el email es de factura)
            # 3. El primero encontrado
            if len(matching_users) > 1:
                print(f"\n⚠️ MÚLTIPLES USUARIOS ENCONTRADOS ({len(matching_users)}) con el mismo email")
                print(f"   Probando cada uno para encontrar el que tiene credenciales válidas...")
                
                # Priorizar usuarios con password configurada
                users_with_password = [u for u in matching_users if u.get('password_smtp')]
                if users_with_password:
                    matching_users = users_with_password
                    print(f"   ✅ Filtrando a {len(matching_users)} usuarios con password configurada")
                
                # Si el email es de una factura, priorizar Contador
                if last_sent and last_sent.get('tipo') == 'factura':
                    contador_users = [u for u in matching_users if compare_ignore_case(u.get('puesto', ''), 'Contador')]
                    if contador_users:
                        matching_users = contador_users
                        print(f"   ✅ Priorizando Contador para facturas: {[u.get('nombre') for u in matching_users]}")
            
            # Usar el primer usuario de la lista filtrada
            if matching_users:
                selected_user = matching_users[0]
                smtp_user = selected_user.get('email_smtp')
                smtp_password = selected_user.get('password_smtp')
                sender_name = selected_user.get('nombre', 'Usuario')
                print(f"\n✅ Usuario seleccionado: {sender_name} (ID: {selected_user.get('id')})")
                print(f"   ✅ email_smtp a usar: '{smtp_user}'")
                print(f"   ✅ password_smtp configurada: {'Sí' if smtp_password else 'No'}")
                print(f"   ✅ puesto: {selected_user.get('puesto', 'N/A')}")
            
            # Si no encontramos por comparación exacta, intentar búsqueda más flexible
            if (not smtp_user or not smtp_password) and sender_email:
                print(f"⚠️ No se encontró usuario con comparación exacta, intentando búsqueda flexible...")
                for u in all_users:
                    user_email_smtp = u.get('email_smtp', '').lower().strip() if u.get('email_smtp') else ''
                    user_email = u.get('email', '').lower().strip() if u.get('email') else ''
                    
                    # Búsqueda flexible: extraer solo la parte local del email (antes de @)
                    sender_local = sender_email.split('@')[0] if sender_email and '@' in sender_email else sender_email
                    user_smtp_local = user_email_smtp.split('@')[0] if '@' in user_email_smtp else user_email_smtp
                    user_email_local = user_email.split('@')[0] if '@' in user_email else user_email
                    
                    if sender_local == user_smtp_local or sender_local == user_email_local:
                        smtp_user = u.get('email_smtp')
                        smtp_password = u.get('password_smtp')
                        sender_name = u.get('nombre', 'Usuario')
                        print(f"✅ Usuario encontrado (búsqueda flexible): {sender_name} ({smtp_user})")
                        break
        
        # Si no encontramos credenciales del remitente, usar las del usuario actual
        if not smtp_user or not smtp_password:
            user_id = session.get("user_id")
            user = get_user_by_id(user_id)
            smtp_user = user.get('email_smtp')
            smtp_password = user.get('password_smtp')
            sender_name = user.get('nombre', 'Usuario')
            print(f"\n{'='*60}")
            print(f"⚠️ FALLBACK: No se encontró usuario con email '{sender_email}'")
            print(f"⚠️ Usando credenciales del usuario actual (quien está viendo el trato):")
            print(f"   Usuario actual: {sender_name} (ID: {user_id})")
            print(f"   email_smtp del usuario actual: '{smtp_user}'")
            print(f"   password_smtp configurada: {'Sí' if smtp_password else 'No'}")
            print(f"{'='*60}\n")
        
        print(f"👤 Usuario para sincronización: {sender_name}")
        print(f"📧 Cuenta SMTP: {smtp_user}")
        print(f"🔑 Password configurada: {'Sí' if smtp_password else 'No'}")
        
        # Verificar si es Gmail
        is_gmail_sync = smtp_user and '@gmail.com' in smtp_user.lower()
        if is_gmail_sync:
            print(f"📧 Email detectado como Gmail, se usará imap.gmail.com")
        else:
            print(f"📧 Email NO es Gmail, se usará servidor GoDaddy")
        
        if not smtp_user or not smtp_password:
            print("❌ Credenciales SMTP no configuradas")
            return jsonify({
                "success": False, 
                "error": "No se encontraron credenciales SMTP configuradas. El usuario que envió el email o el usuario actual deben tener credenciales SMTP configuradas."
            }), 400
        
        # Import sync function
        from email_reader import sync_client_responses, fetch_all_emails
        
        # Sync emails usando las credenciales del remitente
        try:
            synced_count = sync_client_responses(deal_id, smtp_user, smtp_password)
        except Exception as sync_error:
            # Si hay un error en la sincronización, pero es un error de conexión/autenticación
            # que no es crítico (ej: no hay nuevos correos), retornar success con count 0
            error_str = str(sync_error).lower()
            # Si el error es sobre conexión o autenticación, es un error real
            if 'authentication' in error_str or 'connection' in error_str or 'login' in error_str:
                # Error real de credenciales/conexión - retornar error
                elapsed = time.time() - start_time
                print(f"❌ Error crítico sincronizando emails: {sync_error}")
                print(f"⏱️ Tiempo antes del error: {elapsed:.2f} segundos")
                import traceback
                traceback.print_exc()
                return jsonify({"success": False, "error": f"Error de conexión o autenticación: {str(sync_error)}"}), 500
            else:
                # Otros errores (pueden ser temporales o no críticos) - retornar success con 0
                print(f"⚠️ Error no crítico en sincronización (continuando): {sync_error}")
                synced_count = 0
        
        elapsed = time.time() - start_time
        print(f"⏱️ Tiempo transcurrido: {elapsed:.2f} segundos")
        print(f"{'='*60}\n")
        
        # SIEMPRE retornar success: True, incluso si synced_count es 0
        # No hay nuevos correos NO es un error, es un estado normal
        return jsonify({
            "success": True, 
            "synced_count": synced_count,
            "message": f"Se sincronizaron {synced_count} emails nuevos",
            "elapsed": round(elapsed, 2)
        })
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error crítico sincronizando emails: {e}")
        print(f"⏱️ Tiempo antes del error: {elapsed:.2f} segundos")
        import traceback
        traceback.print_exc()
        # Solo retornar error si es un error crítico (no simplemente "no hay nuevos correos")
        error_str = str(e).lower()
        if 'no hay' in error_str or 'sin nuevos' in error_str or 'nada que sincronizar' in error_str:
            # Si el error es simplemente "no hay nuevos", retornar success con 0
            return jsonify({
                "success": True,
                "synced_count": 0,
                "message": "No hay nuevos correos para sincronizar",
                "elapsed": round(elapsed, 2)
            })
        else:
            # Error real - retornar error
            return jsonify({"success": False, "error": str(e)}), 500

# ==================== EMAIL CLIENT MODULE ====================

@app.route("/email")
@require_permission("crm")
def email_client():
    """DEPRECATED: Email module removed. Redirect to CRM."""
    return redirect(url_for("user_crm"))

# ==================== API ENDPOINTS: EMAIL CLIENT (BANDEJA COMPLETA) ====================

# ==================== CRM EMAIL LOG ENDPOINTS ====================

@app.route("/api/crm/deal/<int:deal_id>/first-email-draft", methods=["POST"])
@require_permission("crm")
def api_save_first_email_draft(deal_id):
    """Save first email draft for a deal"""
    try:
        from database import save_first_email_draft, get_deal_by_id
        
        # Verify deal exists
        deal = get_deal_by_id(deal_id)
        if not deal:
            return jsonify({"success": False, "error": "Trato no encontrado"}), 404
        
        data = request.json
        to = data.get('to', '').strip()
        cc = data.get('cc', '').strip() or None
        subject = data.get('subject', '').strip() or None
        body = data.get('body', '').strip() or None
        auto_send = data.get('auto_send_email', 1)
        
        if not to:
            return jsonify({"success": False, "error": "Email destinatario requerido"}), 400
        
        # Ensure token is in subject
        deal_token = f"[DEAL-{deal_id}]"
        if subject and deal_token not in subject:
            subject = f"{subject} {deal_token}"
        
        draft_id = save_first_email_draft(deal_id, to, cc, subject, body, auto_send)
        
        return jsonify({
            "success": True,
            "draft_id": draft_id,
            "message": "Borrador guardado correctamente"
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deals/<int:deal_id>/send_quote_email", methods=["POST"])
@require_permission("crm")
def api_send_quote_email(deal_id):
    """Send quote email from ERP (with PDF attachment) - prevents duplicates"""
    try:
        from database import (get_deal_by_id, get_user_by_id, save_email_log, 
                             is_first_quote_email_sent, mark_first_quote_email_sent)
        from email_sender import send_cotizacion_pdf
        
        # Get deal
        deal = get_deal_by_id(deal_id)
        if not deal:
            return jsonify({"success": False, "error": "Trato no encontrado"}), 404
        
        # Check if already sent (unless force=true)
        data = request.json or {}
        force = data.get('force', False)
        
        if not force and is_first_quote_email_sent(deal_id):
            sent_method = deal.get('first_quote_email_sent_method', 'unknown')
            if sent_method == 'erp':
                return jsonify({
                    "success": False,
                    "error": "Ya fue enviado desde ERP",
                    "already_sent": True,
                    "sent_at": deal.get('first_quote_email_sent_at')
                }), 400
        
        # Validate required fields (handle None values safely)
        to = (data.get('to') or '').strip()
        cc_str = data.get('cc') or ''
        cc = cc_str.strip() if cc_str else None
        subject = (data.get('subject') or '').strip()
        body = (data.get('body') or '').strip()
        
        if not to:
            return jsonify({"success": False, "error": "Email destinatario requerido"}), 400
        
        # Validar formato de emails antes de enviar
        from email_sender import validate_and_parse_emails
        
        to_valid, to_invalid, to_error = validate_and_parse_emails(to, "Para")
        if to_error or not to_valid:
            return jsonify({
                "success": False, 
                "error": to_error or "No hay emails válidos en el campo 'Para'"
            }), 400
        
        # IMPORTANTE: Usar la lista parseada y validada, no el string original
        to_clean = ', '.join(to_valid)
        print(f"📧 DEBUG api_send_quote_email: to original='{to}' -> to_valid={to_valid} -> to_clean='{to_clean}'")
        
        if cc:
            cc_valid, cc_invalid, cc_error = validate_and_parse_emails(cc, "CC")
            if cc_error:
                return jsonify({
                    "success": False,
                    "error": cc_error
                }), 400
            # Si hay CC inválidos pero también válidos, solo usar los válidos
            if cc_valid:
                cc = ', '.join(cc_valid)
            else:
                cc = None  # Si todos los CC son inválidos, no enviar CC
        
        # Check if there's a linked quotation
        if not deal.get('cotizaciones'):
            return jsonify({"success": False, "error": "No hay cotización vinculada al trato"}), 400
        
        cotizacion = deal['cotizaciones'][0]
        cotizacion_id = cotizacion['id']
        cotizacion_folio = cotizacion['folio']
        
        # Get vendor info
        vendedor_id = deal.get('vendedor_id')
        if not vendedor_id:
            return jsonify({"success": False, "error": "No hay vendedor asignado"}), 400
        
        vendedor = get_user_by_id(vendedor_id)
        if not vendedor:
            return jsonify({"success": False, "error": "Vendedor no encontrado"}), 404
        
        vendedor_email = vendedor.get('email')
        vendedor_nombre = vendedor.get('nombre', 'Vendedor INAIR')
        smtp_user = vendedor.get('email_smtp')
        smtp_password = vendedor.get('password_smtp')
        firma = deal.get('firma_vendedor')
        firma_imagen = vendedor.get('firma_imagen')
        
        # Send email with PDF
        error_msg = None
        try:
            send_cotizacion_pdf(
                cotizacion_id,
                to_clean,  # Usar la lista parseada y validada, no el string original
                vendedor_email=vendedor_email,
                vendedor_nombre=vendedor_nombre,
                firma_vendedor=firma,
                mensaje_personalizado=body,
                smtp_user=smtp_user,
                smtp_password=smtp_password,
                firma_imagen=firma_imagen,
                deal_id=deal_id,
                subject=subject,
                cc=cc  # Pasar CC al enviar
            )
            # Generate message_id
            import uuid
            domain = (vendedor_email or 'inair.com.mx').split('@')[1] if '@' in (vendedor_email or '') else 'inair.com.mx'
            message_id = f"<{uuid.uuid4()}@{domain}>"
        except Exception as e:
            error_msg = str(e)
            import traceback
            traceback.print_exc()
        
        if error_msg:
            return jsonify({"success": False, "error": error_msg}), 500
        
        # Mark as sent
        mark_first_quote_email_sent(deal_id, 'erp')
        
        # Save to email_log (don't fail if this errors)
        try:
            import hashlib
            message_content = f"{deal_id}|{cotizacion_id}|{to}|{subject}|{body}"
            message_hash = hashlib.md5(message_content.encode()).hexdigest()
            save_email_log(
                deal_id=deal_id,
                cotizacion_id=cotizacion_id,
                tipo='primer_correo',
                direction='sent',
                to=to,
                cc=cc,
                subject=subject,
                body=body,
                message_id=message_id,
                message_hash=message_hash,
                status='sent',
                error=None
            )
        except Exception as e:
            print(f"⚠️ Error saving to email_log: {e}")
            # Don't fail the request if logging fails
        
        # Mark as sent (don't fail if this errors)
        try:
            mark_first_quote_email_sent(deal_id, 'erp')
        except Exception as e:
            print(f"⚠️ Error marking email as sent: {e}")
            # Don't fail the request if marking fails
        
        return jsonify({
            "success": True,
            "message": "Correo enviado exitosamente",
            "cotizacion_adjunta": cotizacion_folio
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/deals/<int:deal_id>/send_first_email", methods=["POST"])
@require_permission("crm")
def api_send_first_email(deal_id):
    """Legacy endpoint - redirects to new send_quote_email"""
    return api_send_quote_email(deal_id)

@app.route("/crm/deals/<int:deal_id>/cotizacion.pdf", methods=["GET"])
@require_permission("crm")
def crm_deal_cotizacion_pdf(deal_id):
    """Download PDF of the linked quotation for a deal"""
    try:
        from database import get_deal_by_id
        
        # Get deal
        deal = get_deal_by_id(deal_id)
        if not deal:
            return "Trato no encontrado", 404
        
        # Check if there's a linked quotation
        if not deal.get('cotizaciones'):
            return "No hay cotización vinculada al trato", 404
        
        cotizacion = deal['cotizaciones'][0]
        cotizacion_id = cotizacion['id']
        
        # Redirect to existing PDF endpoint
        return redirect(url_for('admin_cotizaciones_pdf', id=cotizacion_id))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route("/api/crm/deals/<int:deal_id>/email_sync", methods=["POST"])
@require_permission("crm")
def api_crm_deal_email_sync(deal_id):
    """Sync emails for a deal and save to crm_email_messages"""
    try:
        from database import (get_deal_by_id, get_user_by_id, save_crm_email_message, 
                             get_crm_email_messages, normalize_subject, calculate_thread_key)
        from email_reader import fetch_all_emails
        
        # Get deal
        deal = get_deal_by_id(deal_id)
        if not deal:
            return jsonify({"success": False, "error": "Trato no encontrado"}), 404
        
        # Get vendor assigned to deal
        vendedor_id = deal.get('vendedor_id')
        if not vendedor_id:
            return jsonify({"success": False, "error": "No hay vendedor asignado al trato"}), 400
        
        vendedor = get_user_by_id(vendedor_id)
        if not vendedor:
            return jsonify({"success": False, "error": "Vendedor no encontrado"}), 404
        
        # Get email credentials
        email_account = vendedor.get('email_smtp') or vendedor.get('email')
        password = vendedor.get('password_smtp')
        
        if not email_account or not password:
            return jsonify({"success": False, "error": "Credenciales de correo no configuradas para el vendedor"}), 400
        
        # Get client email from deal
        cliente_email = deal.get('email', '').lower().strip()
        if not cliente_email:
            return jsonify({"success": False, "error": "No hay email del cliente configurado en el trato"}), 400
        
        # Get linked quotations folios for filtering
        cotizaciones = deal.get('cotizaciones', [])
        if not cotizaciones:
            # Fallback: query directly
            from database import get_db
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT cot.folio FROM cotizaciones cot
                        JOIN crm_deal_cotizaciones dc ON cot.id = dc.cotizacion_id
                        WHERE dc.deal_id = ?
                    ''', (deal_id,))
                    cotizaciones = [dict(row) for row in cursor.fetchall()]
            except:
                cotizaciones = []
        cotizacion_folios = [cot.get('folio', '') for cot in cotizaciones if cot.get('folio')]
        
        # Get existing message_ids from this deal's thread for threading
        existing_messages = get_crm_email_messages(deal_id)
        existing_message_ids = {msg.get('message_id') for msg in existing_messages if msg.get('message_id')}
        existing_thread_keys = {msg.get('thread_key') for msg in existing_messages if msg.get('thread_key')}
        
        print(f"🔄 Sincronizando correos para Deal #{deal_id}")
        print(f"   Vendedor: {vendedor.get('nombre')} ({email_account})")
        print(f"   Cliente: {cliente_email}")
        print(f"   Folios de cotizaciones: {cotizacion_folios}")
        print(f"   Thread keys existentes: {len(existing_thread_keys)}")
        
        synced_count = 0
        
        # Sync INBOX
        print("📥 Sincronizando INBOX...")
        inbox_emails = fetch_all_emails(email_account, password, folder='INBOX', limit=100, since_days=30)
        
        # Token del trato para filtrar
        deal_token = f"[DEAL-{deal_id}]"
        
        for email in inbox_emails:
            # Filter: only emails from/to the client AND related to this deal's thread
            from_email = email.get('from_email', '').lower().strip()
            to_email = email.get('to_email', '').lower().strip()
            subject = email.get('subject', '')
            body = email.get('body', '') or email.get('body_text', '') or email.get('body_html', '')
            subject_norm = normalize_subject(subject)
            message_id = email.get('message_id', '')
            in_reply_to = email.get('in_reply_to', '')
            references = email.get('references', '')
            
            # Check if email is from/to the client
            is_from_client = from_email == cliente_email
            is_to_client = cliente_email in to_email or cliente_email in email.get('to', '').lower()
            
            if not (is_from_client or is_to_client):
                continue  # Skip if not related to client
            
            # Check if email is related to this deal's thread
            is_related = False
            
            # Filter 1 (PRIORIDAD): Check if subject or body contains deal token
            if deal_token in subject or deal_token in body:
                is_related = True
                print(f"   ✅ Email relacionado por token: {deal_token}")
            
            # Filter 2: Check if subject contains any linked quotation folio
            if not is_related and cotizacion_folios:
                for folio in cotizacion_folios:
                    if folio and folio in subject_norm:
                        is_related = True
                        print(f"   ✅ Email relacionado por folio: {folio}")
                        break
            
            # Filter 3: Check if it's a reply to existing messages in this deal's thread
            if not is_related:
                if in_reply_to and in_reply_to in existing_message_ids:
                    is_related = True
                    print(f"   ✅ Email relacionado por in_reply_to")
                elif references:
                    # Check if any message_id in references exists in this deal
                    import re
                    ref_message_ids = re.findall(r'<([^>]+)>', references)
                    if any(mid in existing_message_ids for mid in ref_message_ids):
                        is_related = True
                        print(f"   ✅ Email relacionado por references")
            
            # Filter 4: If no existing thread, only include if subject matches folio or has token
            if not is_related and not existing_messages:
                # Only include if subject contains folio (first email of thread)
                if cotizacion_folios:
                    for folio in cotizacion_folios:
                        if folio and folio in subject_norm:
                            is_related = True
                            break
            
            if is_related:
                # Save as inbound using new body parts
                email_id = save_crm_email_message(
                    deal_id=deal_id,
                    direction='inbound',
                    from_email=email.get('from_email', ''),
                    to_emails=email.get('to', ''),
                    cc_emails=email.get('cc', ''),
                    subject_raw=email.get('subject', ''),
                    message_id=email.get('message_id', ''),
                    in_reply_to=email.get('in_reply_to', ''),
                    references_header=email.get('references', ''),
                    date_ts=email.get('date', datetime.now()) if isinstance(email.get('date'), datetime) else datetime.now(),
                    snippet=email.get('snippet', '') or email.get('body_text', '')[:250] or '',
                    body_html=email.get('body_html'),
                    body_text=email.get('body_text'),
                    provider_uid=str(email.get('uid', ''))
                )
                if email_id:
                    synced_count += 1
        
        # Sync SENT folder
        print("📤 Sincronizando SENT...")
        try:
            sent_emails = fetch_all_emails(email_account, password, folder='SENT', limit=100, since_days=30)
            
            for email in sent_emails:
                # Filter: only emails to the client AND related to this deal's thread
                to_email = email.get('to_email', '').lower().strip()
                to_emails_full = email.get('to', '').lower()
                subject = email.get('subject', '')
                body = email.get('body', '') or email.get('body_text', '') or email.get('body_html', '')
                subject_norm = normalize_subject(subject)
                message_id = email.get('message_id', '')
                in_reply_to = email.get('in_reply_to', '')
                references = email.get('references', '')
                
                if not (cliente_email in to_email or cliente_email in to_emails_full):
                    continue  # Skip if not to client
                
                # Check if email is related to this deal's thread
                is_related = False
                
                # Filter 1 (PRIORIDAD): Check if subject or body contains deal token
                if deal_token in subject or deal_token in body:
                    is_related = True
                    print(f"   ✅ Email relacionado por token: {deal_token}")
                
                # Filter 2: Check if subject contains any linked quotation folio
                if not is_related and cotizacion_folios:
                    for folio in cotizacion_folios:
                        if folio and folio in subject_norm:
                            is_related = True
                            break
                
                # Filter 3: Check if it's a reply to existing messages in this deal's thread
                if not is_related:
                    if in_reply_to and in_reply_to in existing_message_ids:
                        is_related = True
                    elif references:
                        import re
                        ref_message_ids = re.findall(r'<([^>]+)>', references)
                        if any(mid in existing_message_ids for mid in ref_message_ids):
                            is_related = True
                
                # Filter 4: If no existing thread, only include if subject matches folio or has token
                if not is_related and not existing_messages:
                    if cotizacion_folios:
                        for folio in cotizacion_folios:
                            if folio and folio in subject_norm:
                                is_related = True
                                break
                
                if is_related:
                    # Save as outbound using new body parts
                    email_id = save_crm_email_message(
                        deal_id=deal_id,
                        direction='outbound',
                        from_email=email.get('from_email', email_account),
                        to_emails=email.get('to', ''),
                        cc_emails=email.get('cc', ''),
                        subject_raw=email.get('subject', ''),
                        message_id=email.get('message_id', ''),
                        in_reply_to=email.get('in_reply_to', ''),
                        references_header=email.get('references', ''),
                        date_ts=email.get('date', datetime.now()) if isinstance(email.get('date'), datetime) else datetime.now(),
                        snippet=email.get('snippet', '') or email.get('body_text', '')[:250] or '',
                        body_html=email.get('body_html'),
                        body_text=email.get('body_text'),
                        provider_uid=str(email.get('uid', ''))
                    )
                    if email_id:
                        synced_count += 1
        except Exception as e:
            print(f"⚠️ Error sincronizando SENT: {e}")
        
        return jsonify({
            "success": True,
            "synced_count": synced_count,
            "message": f"Se sincronizaron {synced_count} correo(s)"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deals/<int:deal_id>/email_log", methods=["GET"])
@require_permission("crm")
def api_get_crm_email_log(deal_id):
    """Get email log for a deal"""
    try:
        from database import get_crm_email_messages, get_crm_email_attachments
        
        print(f"📧 Obteniendo email log para deal {deal_id}")
        
        messages = get_crm_email_messages(deal_id)
        print(f"📧 Encontrados {len(messages)} mensajes")
        
        # Enrich with attachments
        for msg in messages:
            try:
                msg['attachments'] = get_crm_email_attachments(msg['id'])
            except Exception as att_err:
                print(f"⚠️ Error obteniendo adjuntos para mensaje {msg['id']}: {att_err}")
                msg['attachments'] = []
        
        return jsonify({
            "success": True,
            "messages": messages,
            "count": len(messages)
        })
    except Exception as e:
        print(f"❌ Error en api_get_crm_email_log: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== DEPRECATED: EMAIL MODULE ENDPOINTS (DISABLED) ====================

@app.route("/api/email/inbox", methods=["GET"])
@require_permission("crm")
def api_get_email_inbox():
    """DEPRECATED: Email module removed. Use CRM email log instead."""
    return jsonify({"success": False, "error": "Módulo de correo eliminado. Use el Email Log del CRM."}), 410

@app.route("/api/email/send", methods=["POST"])
@require_permission("crm")
def api_send_email():
    """DEPRECATED: Email module removed. Use CRM email log instead."""
    return jsonify({"success": False, "error": "Módulo de correo eliminado. Use el Email Log del CRM."}), 410

@app.route("/api/email/sync", methods=["POST"])
@require_permission("crm")
def api_sync_email():
    """DEPRECATED: Email module removed. Use CRM email log instead."""
    return jsonify({"success": False, "error": "Módulo de correo eliminado. Use el Email Log del CRM."}), 410

@app.route("/api/crm/deal/<int:id>/message", methods=["GET", "POST"])
@require_permission("crm")
def api_crm_deal_message(id):
    """
    Get or Update deal message for a specific Module/Context.
    GET: ?module=X&context=Y
    POST: {module, context, subject, body, signature}
    """
    from database import get_deal_message, save_deal_message, get_deal_by_id
    
    try:
        # Verify deal exists
        deal = get_deal_by_id(id)
        if not deal:
            return jsonify({"success": False, "error": "Trato no encontrado"}), 404

        # Permission Check
        user_id = session.get("user_id")
        role = session.get("role")
        puesto = session.get("puesto")
        
        # Allow admin/directors or deal owner (logic from original function)
        if role != "admin" and not in_list_ignore_case(puesto, ["Director", "Gerente de Ventas", "Gerente de Servicios Técnicos"]):
            if deal.get('vendedor_id') != user_id:
                 return jsonify({"success": False, "error": "No autorizado"}), 403

        if request.method == "GET":
            module = request.args.get('module')
            context = request.args.get('context')
            
            if not module or not context:
                return jsonify({"success": False, "error": "Module and context required"}), 400
                
            print(f"📥 Loading message for Deal {id} [{module}/{context}]")
            msg = get_deal_message(id, module, context)
            return jsonify({"success": True, "message": msg})

        elif request.method == "POST":
            data = request.json
            module = data.get('module')
            context = data.get('context')
            subject = data.get('subject')
            body = data.get('body')
            signature = data.get('signature')
            
            if not module or not context:
                return jsonify({"success": False, "error": "Module and context required"}), 400

            print(f"💾 Saving message for Deal {id} [{module}/{context}]")
            if save_deal_message(id, module, context, body, signature, subject):
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Failed to save"}), 500
                
    except Exception as e:
        print(f"❌ Excepción en api_crm_deal_message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:id>/link-cotizacion", methods=["POST"])
@require_role("admin")
def api_crm_link_cotizacion(id):
    """Link cotizacion to deal"""
    data = request.json
    cotizacion_id = data.get('cotizacion_id')
    if cotizacion_id:
        link_cotizacion_to_deal(id, cotizacion_id)
        # Recalcular valor estimado automáticamente
        _update_deal_valor_estimado_from_cotizaciones(id)
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route("/api/crm/deal/<int:id>/unlink-cotizacion", methods=["POST"])
@require_role("admin")
def api_crm_unlink_cotizacion(id):
    """Unlink cotizacion from deal"""
    data = request.json
    cotizacion_id = data.get('cotizacion_id')
    if cotizacion_id:
        unlink_cotizacion_from_deal(id, cotizacion_id)
        # Recalcular valor estimado automáticamente
        _update_deal_valor_estimado_from_cotizaciones(id)
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

def _update_deal_valor_estimado_from_cotizaciones(deal_id):
    """Helper function to calculate and update deal valor_estimado from linked cotizaciones"""
    from database import get_deal_by_id
    deal = get_deal_by_id(deal_id)
    if not deal:
        return
    
    cotizaciones = deal.get('cotizaciones', [])
    if not cotizaciones:
        return
    
    # Sumar todos los totales de las cotizaciones
    total = sum(float(cot.get('total', 0) or 0) for cot in cotizaciones)
    
    # Actualizar el deal con el nuevo valor
    from database import update_deal
    update_deal(deal_id, {'valor_estimado': total})

@app.route("/api/crm/deal/<int:id>/link-reporte", methods=["POST"])
@require_role("admin")
def api_crm_link_reporte(id):
    """Link report to deal"""
    data = request.json
    folio = data.get('folio')
    if folio:
        link_reporte_to_deal(id, folio)
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

# ==================== SERVICE DEAL APIs (Equipments & Technicians) ====================

@app.route("/api/crm/deal/<int:deal_id>/tecnicos", methods=["GET"])
@require_permission("crm")
def api_get_deal_tecnicos(deal_id):
    """Get all technicians assigned to a deal"""
    try:
        tecnicos = get_tecnicos_by_deal(deal_id)
        return jsonify({"success": True, "tecnicos": tecnicos})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:deal_id>/timer/start", methods=["POST"])
@require_permission("crm")
def api_start_timer(deal_id):
    """Start timer for a service deal"""
    user_id = session.get("user_id")
    if not can_user_control_timer(deal_id, user_id):
        return jsonify({"success": False, "error": "No tienes permiso para iniciar el timer"}), 403
    
    timer_id = start_service_timer(deal_id, user_id)
    if timer_id:
        return jsonify({"success": True, "timer_id": timer_id})
    else:
        return jsonify({"success": False, "error": "El timer ya está iniciado"}), 400

@app.route("/api/crm/deal/<int:deal_id>/timer/stop", methods=["POST"])
@require_permission("crm")
def api_stop_timer(deal_id):
    """Stop timer for a service deal"""
    user_id = session.get("user_id")
    if not can_user_control_timer(deal_id, user_id):
        return jsonify({"success": False, "error": "Solo el técnico que inició el timer puede detenerlo"}), 403
    
    result = stop_service_timer(deal_id, user_id)
    if result is True:
        timer = get_service_timer(deal_id)
        return jsonify({"success": True, "timer": timer})
    elif result is False:
        return jsonify({"success": False, "error": "No tienes permiso para detener el timer"}), 403
    else:
        return jsonify({"success": False, "error": "No hay timer activo"}), 400

@app.route("/api/crm/deal/<int:deal_id>/timer", methods=["GET"])
@require_permission("crm")
def api_get_timer(deal_id):
    """Get timer status for a service deal"""
    timer = get_service_timer(deal_id)
    is_active = is_timer_active(deal_id)
    user_id = session.get("user_id")
    can_control = can_user_control_timer(deal_id, user_id)
    
    return jsonify({
        "timer": timer,
        "is_active": is_active,
        "can_control": can_control
    })

@app.route("/api/crm/deal/<int:deal_id>/equipos", methods=["GET"])
@require_permission("crm")
def api_get_deal_equipos(deal_id):
    """Get all equipments for a service deal"""
    try:
        equipos = get_equipos_by_deal(deal_id)
        return jsonify(equipos)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:deal_id>/equipo", methods=["POST"])
@require_permission("crm")
def api_add_deal_equipo(deal_id):
    """Add equipment to a service deal"""
    try:
        data = request.json
        equipo_id = add_equipo_to_deal(
            deal_id,
            data.get('tipo_equipo'),
            data.get('modelo', ''),
            data.get('serie', ''),
            data.get('descripcion_servicio', ''),
            data.get('detalles_adicionales', ''),
            data.get('orden', 0)
        )
        return jsonify({"success": True, "id": equipo_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/deal/equipo/<int:equipo_id>", methods=["PUT"])
@require_permission("crm")
def api_update_deal_equipo(equipo_id):
    """Update equipment details"""
    try:
        data = request.json
        success = update_equipo_deal(equipo_id, **data)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/deal/equipo/<int:equipo_id>", methods=["DELETE"])
@require_permission("crm")
def api_delete_deal_equipo(equipo_id):
    """Delete equipment from deal"""
    try:
        success = delete_equipo_deal(equipo_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/deal/<int:deal_id>/tecnico", methods=["POST"])
@require_permission("crm")
def api_assign_tecnico(deal_id):
    """Assign technician to a service deal"""
    try:
        data = request.json
        tecnico_id = data.get('tecnico_id')
        puntos = float(data.get('puntos', 0))
        user_id = session.get("user_id")
        
        assignment_id = assign_tecnico_to_deal(deal_id, tecnico_id, user_id, puntos)
        if assignment_id:
            return jsonify({"success": True, "id": assignment_id})
        return jsonify({"success": False, "error": "Técnico ya asignado"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/deal/<int:deal_id>/tecnico/<int:tecnico_id>", methods=["DELETE"])
@require_permission("crm")
def api_remove_tecnico(deal_id, tecnico_id):
    """Remove technician from a service deal"""
    try:
        success = remove_tecnico_from_deal(deal_id, tecnico_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/deal/<int:deal_id>/tecnico/<int:tecnico_id>/puntos", methods=["PUT"])
@require_permission("crm")
def api_update_tecnico_puntos(deal_id, tecnico_id):
    """Update technician points for a service"""
    try:
        data = request.json
        puntos = float(data.get('puntos', 0))
        success = update_tecnico_puntos(deal_id, tecnico_id, puntos)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/mis-servicios", methods=["GET"])
@require_permission("crm")
def api_my_services():
    """Get services assigned to current technician"""
    try:
        user_id = session.get("user_id")
        etapa = request.args.get('etapa')  # Optional filter
        servicios = get_deals_by_tecnico(user_id, tipo_deal='servicio', etapa=etapa)
        return jsonify({"success": True, "servicios": servicios})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/deal/<int:deal_id>/servicio", methods=["PUT"])
@require_permission("crm")
def api_update_deal_servicio(deal_id):
    """Update service-specific fields (fecha, tiempo estimado)"""
    try:
        data = request.json
        update_data = {
            'fecha_servicio': data.get('fecha_servicio'),
            'tiempo_estimado_horas': float(data.get('tiempo_estimado_horas', 0)) if data.get('tiempo_estimado_horas') else None
        }
        success = update_deal(deal_id, update_data)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ==================== Equipment Photos & Comments APIs ====================

@app.route("/api/crm/equipo/<int:equipo_id>/fotos", methods=["GET"])
@require_permission("crm")
def api_get_equipo_fotos(equipo_id):
    """Get all photos for an equipment"""
    try:
        fotos = get_equipo_fotos(equipo_id)
        return jsonify({"success": True, "fotos": fotos})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/equipo/<int:equipo_id>/foto", methods=["POST"])
@require_role("admin")
def api_add_equipo_foto(equipo_id):
    """Add photo to equipment (admin only, max 10)"""
    try:
        data = request.json
        user_id = session.get("user_id")
        foto_id = add_equipo_foto(
            equipo_id,
            data.get('foto_data'),
            data.get('descripcion', ''),
            user_id,
            data.get('orden', 0)
        )
        if foto_id:
            return jsonify({"success": True, "id": foto_id})
        return jsonify({"success": False, "error": "Máximo 10 fotos permitidas"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/equipo/foto/<int:foto_id>", methods=["DELETE"])
@require_role("admin")
def api_delete_equipo_foto(foto_id):
    """Delete equipment photo (admin only)"""
    try:
        success = delete_equipo_foto(foto_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/equipo/<int:equipo_id>/comentarios", methods=["GET"])
@require_permission("crm")
def api_get_equipo_comentarios(equipo_id):
    """Get all comments for an equipment"""
    try:
        comentarios = get_equipo_comentarios(equipo_id)
        return jsonify({"success": True, "comentarios": comentarios})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crm/equipo/<int:equipo_id>/comentario", methods=["POST"])
@require_permission("crm")
def api_add_equipo_comentario(equipo_id):
    """Add comment to equipment with mentions"""
    try:
        data = request.json
        user_id = session.get("user_id")
        comentario_id = add_equipo_comentario(
            equipo_id,
            user_id,
            data.get('mensaje'),
            data.get('imagen_data')
        )
        
        # Handle Mentions
        mensaje = data.get('mensaje', '')
        deal_id = data.get('deal_id')
        
        if mensaje and '@' in mensaje:
            mentions = re.findall(r'@(\w+)', mensaje)
            sender = get_user_by_id(user_id)
            sender_name = sender['username'] if sender else "Usuario"
            
            # Get equipment info for context
            equipment = get_equipment_by_id(equipo_id)
            equip_name = f"{equipment['tipo_equipo']} {equipment['modelo']}" if equipment else "Equipo"
            
            processed_users = set()
            for username in mentions:
                if username in processed_users: continue
                
                target_user = get_user_by_username(username)
                if target_user and target_user['id'] != user_id:
                    create_notification(
                        user_id=target_user['id'],
                        tipo='mention',
                        titulo=f"Mención en {equip_name}",
                        mensaje=f"{sender_name} te mencionó: {mensaje}",
                        deal_id=deal_id
                    )
                    processed_users.add(username)
                    
        return jsonify({"success": True, "id": comentario_id})
    except Exception as e:
        print(f"Error adding comment: {e}") # Log error
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/equipo/comentario/<int:comentario_id>", methods=["DELETE"])
@require_role("admin")
def api_delete_equipo_comentario(comentario_id):
    """Delete equipment comment (admin only)"""
    try:
        success = delete_equipo_comentario(comentario_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ==================== CRM STAGES ADMIN ====================

@app.route("/admin/crm/etapas")
@require_role("admin")
def admin_crm_etapas():
    """Admin page to manage CRM stages for all puestos"""
    all_stages = get_all_puesto_stages()
    
    # Group stages by puesto
    stages_by_puesto = {}
    for stage in all_stages:
        puesto = stage['puesto']
        if puesto not in stages_by_puesto:
            stages_by_puesto[puesto] = []
        stages_by_puesto[puesto].append(stage)
    
    # Sort stages within each puesto by orden
    for puesto in stages_by_puesto:
        stages_by_puesto[puesto].sort(key=lambda x: x['orden'])
    
    # Get all triggers
    triggers = get_stage_triggers()
    
    return render_template("admin_crm_etapas.html", 
                          stages_by_puesto=stages_by_puesto,
                          triggers=triggers)

@app.route("/api/crm/etapa/<int:id>", methods=["PUT"])
@require_role("admin")
def api_crm_etapa_update(id):
    """Update a CRM stage name or color"""
    data = request.json
    stage_name = data.get('stage_name')
    color = data.get('color')
    orden = data.get('orden')
    
    # Get old stage name for updating deals
    from database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT stage_name, puesto FROM crm_puesto_stages WHERE id = ?", (id,))
        old = cursor.fetchone()
        if old:
            old_stage_name = old['stage_name']
            puesto = old['puesto']
    
    success = update_puesto_stage(id, stage_name=stage_name, color=color, orden=orden)
    
    if success and stage_name and old_stage_name != stage_name:
        # Update deals that are in this stage
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE crm_deals SET etapa = ? WHERE etapa = ?", (stage_name, old_stage_name))
            # Update triggers that reference this stage
            cursor.execute("""
                UPDATE crm_stage_triggers 
                SET source_stage = ? WHERE source_puesto = ? AND source_stage = ?
            """, (stage_name, puesto, old_stage_name))
            cursor.execute("""
                UPDATE crm_stage_triggers 
                SET target_stage = ? WHERE target_puesto = ? AND target_stage = ?
            """, (stage_name, puesto, old_stage_name))
    
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Could not update stage"}), 400

@app.route("/api/crm/etapa/<int:id>", methods=["DELETE"])
@require_role("admin")
def api_crm_etapa_delete(id):
    """Delete a CRM stage"""
    # Get stage info before deleting
    from database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT stage_name, puesto FROM crm_puesto_stages WHERE id = ?", (id,))
        stage = cursor.fetchone()
        
        if stage:
            stage_name = stage['stage_name']
            puesto = stage['puesto']
            
            # Check if there are deals in this stage
            cursor.execute("SELECT COUNT(*) as count FROM crm_deals WHERE etapa = ?", (stage_name,))
            deal_count = cursor.fetchone()['count']
            
            if deal_count > 0:
                return jsonify({
                    "success": False, 
                    "error": f"No se puede eliminar: hay {deal_count} tratos en esta etapa. Muévelos primero."
                }), 400
            
            # Delete related triggers
            cursor.execute("""
                DELETE FROM crm_stage_triggers 
                WHERE (source_puesto = ? AND source_stage = ?) 
                   OR (target_puesto = ? AND target_stage = ?)
            """, (puesto, stage_name, puesto, stage_name))
    
    success = delete_puesto_stage(id)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Could not delete stage"}), 400

@app.route("/api/crm/etapa", methods=["POST"])
@require_role("admin")
def api_crm_etapa_create():
    """Create a new CRM stage"""
    data = request.json
    puesto = data.get('puesto')
    stage_name = data.get('stage_name')
    color = data.get('color', '#6c757d')
    orden = data.get('orden', 0)
    
    if not puesto or not stage_name:
        return jsonify({"success": False, "error": "Puesto y nombre son requeridos"}), 400
    
    stage_id = add_puesto_stage(puesto, stage_name, orden, color)
    if stage_id:
        return jsonify({"success": True, "id": stage_id})
    return jsonify({"success": False, "error": "Ya existe una etapa con ese nombre"}), 400

@app.route("/api/crm/etapas/reorder", methods=["POST"])
@require_role("admin")
def api_crm_etapas_reorder():
    """Reorder stages for a puesto"""
    from database import get_db
    data = request.json
    puesto = data.get('puesto')
    order = data.get('order', [])  # List of stage IDs in new order
    
    if not puesto or not order:
        return jsonify({"success": False, "error": "Puesto y orden son requeridos"}), 400
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            for idx, stage_id in enumerate(order):
                cursor.execute(
                    "UPDATE crm_puesto_stages SET orden = ? WHERE id = ? AND puesto = ?",
                    (idx, stage_id, puesto)
                )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ==================== TRIGGERS MANAGEMENT ====================

@app.route("/api/crm/trigger", methods=["POST"])
@require_role("admin")
def api_crm_trigger_create():
    """Create a new CRM trigger"""
    from database import get_db
    data = request.json
    source_puesto = data.get('source_puesto')
    source_stage = data.get('source_stage')
    target_puesto = data.get('target_puesto')
    target_stage = data.get('target_stage')
    
    if not all([source_puesto, source_stage, target_puesto, target_stage]):
        return jsonify({"success": False, "error": "Todos los campos son requeridos"}), 400
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Check if trigger already exists
            cursor.execute("""
                SELECT id FROM crm_stage_triggers 
                WHERE source_puesto = ? AND source_stage = ?
            """, (source_puesto, source_stage))
            if cursor.fetchone():
                return jsonify({"success": False, "error": "Ya existe un trigger para esta etapa origen"}), 400
            
            cursor.execute("""
                INSERT INTO crm_stage_triggers (source_puesto, source_stage, target_puesto, target_stage, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (source_puesto, source_stage, target_puesto, target_stage))
            return jsonify({"success": True, "id": cursor.lastrowid})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/trigger/<int:id>", methods=["PUT"])
@require_role("admin")
def api_crm_trigger_update(id):
    """Update a CRM trigger"""
    from database import get_db
    data = request.json
    target_puesto = data.get('target_puesto')
    target_stage = data.get('target_stage')
    is_active = data.get('is_active')
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if target_puesto is not None:
                updates.append("target_puesto = ?")
                params.append(target_puesto)
            if target_stage is not None:
                updates.append("target_stage = ?")
                params.append(target_stage)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)
            
            if updates:
                params.append(id)
                cursor.execute(f"UPDATE crm_stage_triggers SET {', '.join(updates)} WHERE id = ?", params)
                return jsonify({"success": True})
        return jsonify({"success": False, "error": "Nada que actualizar"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/trigger/<int:id>", methods=["DELETE"])
@require_role("admin")
def api_crm_trigger_delete(id):
    """Delete a CRM trigger"""
    from database import get_db
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM crm_stage_triggers WHERE id = ?", (id,))
            if cursor.rowcount > 0:
                return jsonify({"success": True})
            return jsonify({"success": False, "error": "Trigger no encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/crm/triggers", methods=["GET"])
@require_role("admin")
def api_crm_triggers_list():
    """Get all triggers"""
    triggers = get_stage_triggers()
    return jsonify({"success": True, "triggers": triggers})

# ==================== FINANZAS API ROUTES ====================

@app.route("/api/cotizaciones/detalle/<int:id>")
@require_permission("cotizaciones")
def api_cotizacion_detalle(id):
    """Get quote details including items"""
    cotizacion = get_cotizacion_by_id(id)
    if cotizacion:
        # Check if items are included in cotizacion dict, if not we might need to fetch them
        # Usually get_cotizacion_by_id returns them 'items' key if configured, let's verify database.py or just return it
        # Assuming existing structure supports it. If not, frontend will just get empty items.
        return jsonify(dict(cotizacion))
    return jsonify({"error": "Cotizacion not found"}), 404

@app.route("/api/finanzas/cliente/<int:cliente_id>", methods=["GET"])
@require_permission("finanzas")
def api_get_cliente_info(cliente_id):
    """Get client information"""
    cliente = get_client_by_id(cliente_id)
    if cliente:
        return jsonify({"success": True, "cliente": cliente})
    return jsonify({"success": False, "error": "Cliente no encontrado"}), 404

@app.route("/api/finanzas/cotizaciones/<int:cliente_id>", methods=["GET"])
@require_permission("cotizaciones")
def api_get_cotizaciones_cliente(cliente_id):
    """Get available cotizaciones for a client"""
    cotizaciones = get_cotizaciones_by_client(cliente_id)
    return jsonify({"success": True, "cotizaciones": cotizaciones})

@app.route("/api/finanzas/cotizacion/<int:cotizacion_id>/partidas", methods=["GET"])
@require_permission("cotizaciones")
def api_get_cotizacion_partidas(cotizacion_id):
    """Get partidas (line items) from a cotizacion"""
    try:
        cotizacion = get_cotizacion_by_id(cotizacion_id)
        if not cotizacion:
            return jsonify({"success": False, "error": "Cotización no encontrada"}), 404
        
        # Get items from cotizacion (they are stored in cotizacion_items table)
        partidas = []
        if cotizacion.get('items'):
            # Transform cotizacion items to factura partidas format
            for item in cotizacion['items']:
                try:
                    partida = {
                        'codigo': str(item.get('numero_parte', '') or 'N/A'),
                        'descripcion': str(item.get('descripcion', '') or 'Sin descripción'),
                        'cantidad': float(item.get('cantidad') or 1),
                        'unidad': str(item.get('unidad', '') or 'SER'),
                        'precio_unitario': float(item.get('precio_unitario') or 0),
                        'subtotal': float(item.get('importe') or 0)
                    }
                    partidas.append(partida)
                except (ValueError, TypeError) as e:
                    print(f"Error procesando partida: {e}, item: {item}")
                    continue
        
        # Convert IVA from decimal to percentage if needed
        iva = float(cotizacion.get('iva_porcentaje') or 16)
        if iva < 1:  # If it's in decimal format (0.16), convert to percentage
            iva = iva * 100
        
        return jsonify({
            "success": True,
            "partidas": partidas,
            "iva_porcentaje": iva,
            "total_partidas": len(partidas)
        })
    except Exception as e:
        print(f"Error en api_get_cotizacion_partidas: {e}")
        return jsonify({"success": False, "error": f"Error al cargar partidas: {str(e)}"}), 500

# ==================== FINANZAS ROUTES ====================

@app.route("/admin/finanzas")
@require_permission("finanzas")
def admin_finanzas():
    """Financial dashboard - overview of invoices, payments, and expenses"""
    stats = get_finanzas_stats()
    return render_template("admin_finanzas_dashboard.html", stats=stats)

@app.route("/admin/finanzas/facturas")
@require_permission("finanzas")
def admin_facturas():
    """Invoice management page"""
    facturas = get_all_facturas()
    por_cobrar = get_cuentas_por_cobrar()
    return render_template("admin_facturas.html", facturas=facturas, por_cobrar=por_cobrar)

@app.route("/admin/finanzas/solicitudes-factura")
@require_permission("finanzas")
def admin_finanzas_solicitudes_factura():
    """Vista de solicitudes de factura"""
    return render_template("finanzas_solicitudes_factura.html")

@app.route("/admin/compras/requisiciones")
@require_permission("compras")
def admin_compras_requisiciones():
    """Vista de requisiciones de compra (faltantes OCu)"""
    return render_template("compras_requisiciones.html")

@app.route("/admin/finanzas/facturas/nueva", methods=["GET", "POST"])
@require_permission("finanzas")
def admin_factura_nueva():
    """Create new invoice"""
    if request.method == "POST":
        try:
            # Generate automatic folio
            numero_factura = get_next_factura_folio()
            
            fecha_emision = request.form.get("fecha_emision")
            cliente_nombre = request.form.get("cliente_nombre")
            cliente_rfc = request.form.get("cliente_rfc", "")
            iva_porcentaje = float(request.form.get("iva_porcentaje", 16))
            fecha_vencimiento = request.form.get("fecha_vencimiento")
            metodo_pago = request.form.get("metodo_pago")
            notas = request.form.get("notas")
            
            # Optional foreign keys
            cliente_id = request.form.get("cliente_id")
            if cliente_id:
                cliente_id = int(cliente_id)
            
            cotizacion_id = request.form.get("cotizacion_id")
            if cotizacion_id:
                cotizacion_id = int(cotizacion_id)
            
            # Get partidas from form (JSON string)
            import json
            partidas_json = request.form.get("partidas_json", "[]")
            partidas = json.loads(partidas_json)
            
            # Calculate totals from partidas
            subtotal = sum(float(p['subtotal']) for p in partidas)
            
            factura_id = create_factura(
                numero_factura=numero_factura,
                fecha_emision=fecha_emision,
                cliente_nombre=cliente_nombre,
                cliente_rfc=cliente_rfc,
                subtotal=subtotal,
                iva_porcentaje=iva_porcentaje,
                cliente_id=cliente_id,
                cotizacion_id=cotizacion_id,
                fecha_vencimiento=fecha_vencimiento,
                metodo_pago=metodo_pago,
                notas=notas,
                partidas=partidas
            )
            
            # NOTA: El descuento de almacén ahora se hace manualmente mediante
            # la ruta /api/facturas/<factura_id>/aplicar-salida-almacen
            # que llama a apply_invoice_inventory_salida()
            
            return redirect(url_for("admin_factura_detalle", id=factura_id))
        except Exception as e:
            return f"Error al crear factura: {str(e)}", 400
    
    # GET request - show form
    clientes = get_all_clients()
    # Preview next folio for display (doesn't increment)
    next_folio = preview_next_factura_folio()
    return render_template("admin_factura_nueva.html", clientes=clientes, next_folio=next_folio)

@app.route("/admin/finanzas/facturas/<int:id>")
@require_permission("finanzas")
def admin_factura_detalle(id):
    """View invoice details with payments"""
    factura = get_factura_by_id(id)
    if not factura:
        return "Factura no encontrada", 404
    
    # Check if inventory salida has been applied
    salida_aplicada = has_invoice_been_applied(id)
    movements = get_inventory_movements_by_invoice(id) if salida_aplicada else []
    
    return render_template("admin_factura_detalle.html", 
                         factura=factura, 
                         salida_aplicada=salida_aplicada,
                         movements=movements)

@app.route("/admin/finanzas/facturas/<int:id>/pago", methods=["POST"])
@require_permission("finanzas")
def admin_factura_agregar_pago(id):
    """Add payment to invoice"""
    try:
        fecha_pago = request.form.get("fecha_pago")
        monto = float(request.form.get("monto"))
        metodo = request.form.get("metodo")
        referencia = request.form.get("referencia")
        notas = request.form.get("notas")
        
        create_pago(
            factura_id=id,
            fecha_pago=fecha_pago,
            monto=monto,
            metodo=metodo,
            referencia=referencia,
            notas=notas
        )
        
        return redirect(url_for("admin_factura_detalle", id=id))
    except Exception as e:
        return f"Error al registrar pago: {str(e)}", 400

@app.route("/api/facturas/<int:factura_id>/aplicar-salida-almacen", methods=["POST"])
@require_permission("finanzas")
def api_aplicar_salida_almacen(factura_id):
    """Apply inventory salida (outgoing) for invoice items"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "error": "Usuario no autenticado"}), 401
        
        # Import here to avoid circular dependency
        from database import apply_invoice_inventory_salida
        success, errors, movements = apply_invoice_inventory_salida(factura_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Salida de almacén aplicada correctamente. {len(movements)} movimiento(s) registrado(s).",
                "movements": movements
            })
        else:
            return jsonify({
                "success": False,
                "errors": errors
            }), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== REMISIONES MODULE ROUTES ====================

@app.route("/admin/remisiones")
@require_permission("finanzas")
def admin_remisiones():
    """List all remisiones"""
    remisiones = get_all_remisiones()
    return render_template("admin_remisiones.html", remisiones=remisiones)

@app.route("/admin/remisiones/nueva", methods=["GET", "POST"])
@require_permission("finanzas")
def admin_remision_nueva():
    """Create new remision"""
    if request.method == "POST":
        try:
            cliente_id = request.form.get("cliente_id")
            cliente_id = int(cliente_id) if cliente_id else None
            cliente_nombre = request.form.get("cliente_nombre", "").strip()
            fecha = request.form.get("fecha")
            notas = request.form.get("notas", "").strip()
            
            # Optional links
            factura_id = request.form.get("factura_id")
            factura_id = int(factura_id) if factura_id else None
            cotizacion_id = request.form.get("cotizacion_id")
            cotizacion_id = int(cotizacion_id) if cotizacion_id else None
            trato_id = request.form.get("trato_id")
            trato_id = int(trato_id) if trato_id else None
            oc_cliente_id = request.form.get("oc_cliente_id", "").strip()
            
            user_id = session.get("user_id")
            
            remision_id = create_remision(
                cliente_id=cliente_id,
                cliente_nombre=cliente_nombre,
                fecha=fecha,
                estado='draft',
                factura_id=factura_id,
                cotizacion_id=cotizacion_id,
                trato_id=trato_id,
                oc_cliente_id=oc_cliente_id if oc_cliente_id else None,
                notas=notas,
                created_by=user_id
            )

            # Guardar items (si fueron enviados desde el formulario)
            item_descr = request.form.getlist("item_descripcion[]")
            item_cant = request.form.getlist("item_cantidad[]")
            item_unid = request.form.getlist("item_unidad[]")
            item_numpar = request.form.getlist("item_numero_parte[]")
            if remision_id and item_descr:
                for idx, desc in enumerate(item_descr):
                    desc = desc.strip()
                    if not desc:
                        continue
                    cantidad = float(item_cant[idx]) if idx < len(item_cant) and item_cant[idx] else 0
                    unidad = item_unid[idx] if idx < len(item_unid) else 'PZA'
                    num_parte = item_numpar[idx] if idx < len(item_numpar) else None
                    add_remision_item(remision_id, desc, cantidad, unidad, numero_parte=num_parte)

            if remision_id:
                return redirect(url_for("admin_remision_detalle", id=remision_id))
            else:
                return "Error al crear remisión", 400
        except Exception as e:
            return f"Error al crear remisión: {str(e)}", 400
    
    # GET request - show form
    clientes = get_all_clients()
    facturas = get_all_facturas()
    cotizaciones = get_all_cotizaciones()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template("admin_remision_nueva.html", 
                         clientes=clientes, 
                         facturas=facturas,
                         cotizaciones=cotizaciones,
                         today=today)

@app.route("/admin/remisiones/<int:id>")
@require_permission("finanzas")
def admin_remision_detalle(id):
    """View remision details"""
    remision = get_remision_by_id(id)
    if not remision:
        return "Remisión no encontrada", 404
    
    # Check if salida has been applied
    salida_aplicada = has_remision_been_confirmed(id)
    movements = get_inventory_movements_by_remision(id) if salida_aplicada else []
    
    return render_template("admin_remision_detalle.html", 
                         remision=remision,
                         salida_aplicada=salida_aplicada,
                         movements=movements)

@app.route("/admin/remisiones/<int:id>/editar", methods=["GET", "POST"])
@require_permission("finanzas")
def admin_remision_editar(id):
    """Edit remision"""
    remision = get_remision_by_id(id)
    if not remision:
        return "Remisión no encontrada", 404
    
    if remision['estado'] == 'confirmed':
        return "No se puede editar una remisión confirmada", 400
    
    if request.method == "POST":
        try:
            cliente_id = request.form.get("cliente_id")
            cliente_id = int(cliente_id) if cliente_id else None
            cliente_nombre = request.form.get("cliente_nombre", "").strip()
            fecha = request.form.get("fecha")
            notas = request.form.get("notas", "").strip()
            
            update_remision(
                id,
                cliente_id=cliente_id,
                cliente_nombre=cliente_nombre,
                fecha=fecha,
                notas=notas
            )
            
            return redirect(url_for("admin_remision_detalle", id=id))
        except Exception as e:
            return f"Error al actualizar remisión: {str(e)}", 400
    
    # GET request
    clientes = get_all_clients()
    return render_template("admin_remision_editar.html", remision=remision, clientes=clientes)

@app.route("/api/remisiones/<int:remision_id>/items", methods=["POST"])
@require_permission("finanzas")
def api_add_remision_item(remision_id):
    """Add item to remision"""
    try:
        data = request.json
        descripcion = data.get("descripcion", "").strip()
        cantidad = float(data.get("cantidad", 0))
        unidad = data.get("unidad", "PZA")
        numero_parte = data.get("numero_parte", "").strip()
        refaccion_id = data.get("refaccion_id")
        
        if not descripcion or cantidad <= 0:
            return jsonify({"success": False, "error": "Descripción y cantidad requeridas"}), 400
        
        # If numero_parte provided, try to find refaccion_id
        if numero_parte and not refaccion_id:
            from database import get_refaccion_by_numero_parte
            refaccion = get_refaccion_by_numero_parte(numero_parte)
            if refaccion:
                refaccion_id = refaccion['id']
        
        item_id = add_remision_item(
            remision_id=remision_id,
            descripcion=descripcion,
            cantidad=cantidad,
            unidad=unidad,
            refaccion_id=refaccion_id,
            numero_parte=numero_parte if numero_parte else None
        )
        
        if item_id:
            return jsonify({"success": True, "item_id": item_id})
        return jsonify({"success": False, "error": "Error al agregar item"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/remisiones/items/<int:item_id>", methods=["DELETE"])
@require_permission("finanzas")
def api_delete_remision_item(item_id):
    """Delete remision item"""
    try:
        success = delete_remision_item(item_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/remisiones/<int:remision_id>/confirmar-salida", methods=["POST"])
@require_permission("finanzas")
def api_confirmar_salida_remision(remision_id):
    """Confirm salida (apply inventory) for remision"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "error": "Usuario no autenticado"}), 401
        
        success, errors, movements = apply_remision_inventory_salida(remision_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Salida de almacén aplicada correctamente. {len(movements)} movimiento(s) registrado(s).",
                "movements": movements
            })
        else:
            return jsonify({
                "success": False,
                "errors": errors
            }), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/cotizaciones/<int:cotizacion_id>/items", methods=["GET"])
@require_permission("cotizaciones")
def api_get_cotizacion_items(cotizacion_id):
    """Return cotizacion items for linking into remisiones"""
    try:
        items = get_cotizacion_items(cotizacion_id)
        return jsonify({"success": True, "items": items})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin/remisiones/<int:id>/pdf")
@require_permission("finanzas")
def admin_remision_pdf(id):
    """Generate PDF for remision"""
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    
    remision = get_remision_by_id(id)
    if not remision:
        return "Remisión no encontrada", 404
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=80)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=8, leading=10)
    style_cell = ParagraphStyle('CellWrap', parent=styles['Normal'], fontSize=7, leading=9)
    style_right = ParagraphStyle('Right', parent=styles['Normal'], fontSize=8, alignment=TA_RIGHT)
    style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, textColor=colors.HexColor('#D20000'))
    
    # Header with logo and accent bar
    # Use official INAIR logo if available
    logo_path = os.path.join(app.static_folder, 'img', 'logo_inair.png')
    if os.path.exists(logo_path):
        logo = RLImage(logo_path, width=120, height=55)
        header_left = logo
    else:
        header_left = Paragraph("<b>INAIR</b>", style_title)
    
    header_right = Paragraph(f"""
        <b style="color:#D20000;">REMISIÓN</b><br/>
        <font size="16" color="#D20000"><b>Folio {remision['folio']}</b></font><br/>
        <font size="9">Tijuana, B.C., {remision['fecha']}</font>
    """, style_right)
    
    header_table = Table([[header_left, header_right]], colWidths=[320, 210])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    
    # Accent separator
    elements.append(Spacer(1, 6))
    accent = Table([[Paragraph('', style_normal)]], colWidths=[530])
    accent.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#D20000')),
        ('LINEBELOW', (0,0), (-1,-1), 0, colors.white),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    elements.append(accent)
    elements.append(Spacer(1, 12))
    
    # Client info
    elements.append(Paragraph("<b>Entregado a:</b>", style_normal))
    client_info = f"""
        <b>{remision['cliente_nombre']}</b><br/>
    """
    if remision.get('oc_cliente_id'):
        client_info += f"OC Cliente: {remision['oc_cliente_id']}<br/>"
    client_table = Table([[Paragraph(client_info, style_normal)]], colWidths=[530])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f6f8fb')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#dce3f0')),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 16))
    
    # Items table
    table_header = ['Descripción', 'Cant.', 'Unidad', 'Número de Parte']
    data = [table_header]
    
    for item in remision.get('items', []):
        data.append([
            Paragraph(item.get('descripcion', ''), style_cell),
            f"{item.get('cantidad', 0):.2f}",
            item.get('unidad', 'PZA'),
            item.get('numero_parte', '-')
        ])
    
    items_table = Table(data, colWidths=[220, 60, 70, 120])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D20000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (2, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cfd8e3')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f6f8fb')]),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # Notes if any
    if remision.get('notas'):
        elements.append(Paragraph(f"<b>Notas:</b> {remision['notas']}", style_normal))
        elements.append(Spacer(1, 10))
    
    # Acceptance block (bottom-left)
    acceptance_text = """
    <b>Recibo Refacciones a mi entera Satisfacción:</b><br/><br/>
    Nombre: ____________________________________________<br/><br/>
    Puesto o Cargo: _____________________________________<br/><br/>
    Fecha: ____________________   Firma: ________________
    """
    acceptance_table = Table([[Paragraph(acceptance_text, style_normal)]], colWidths=[530])
    acceptance_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f6f8fb')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#dce3f0')),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(Spacer(1, 16))
    elements.append(acceptance_table)
    elements.append(Spacer(1, 12))

    # Footer
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#E74C3C'))
        canvas.setLineWidth(1.5)
        canvas.line(40, 70, A4[0] - 40, 70)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(40, 55, "INGENIERÍA EN AIRE SA DE CV  RFC: IAI160525B06")
        canvas.setFont('Helvetica', 6)
        canvas.drawString(40, 45, "Avenida Alfonso Vidal y Planas #445, Interior S/N, Colonia Nueva Tijuana, Tijuana, Baja California, México, Cp: 22435")
        canvas.drawString(40, 35, "Tel: (664) 250-0022 | pedidos@inair.com.mx | www.inair.com.mx")
        canvas.setFont('Helvetica', 6)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(A4[0] - 40, 55, f"Estado: {remision['estado'].upper()}")
        canvas.drawRightString(A4[0] - 40, 47, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        canvas.restoreState()
    
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    
    is_preview = request.args.get('preview') == 'true'
    return send_file(buffer, as_attachment=not is_preview, 
                     mimetype='application/pdf',
                     download_name=f"Remision_{remision['folio']}.pdf" if not is_preview else None)

@app.route("/admin/finanzas/gastos")
@require_permission("finanzas")
def admin_gastos():
    """Expenses management page"""
    gastos = get_all_gastos()
    return render_template("admin_gastos.html", gastos=gastos)

@app.route("/admin/finanzas/gastos/nuevo", methods=["POST"])
@require_permission("finanzas")
def admin_gasto_nuevo():
    """Create new expense"""
    try:
        fecha = request.form.get("fecha")
        categoria = request.form.get("categoria")
        concepto = request.form.get("concepto")
        monto = float(request.form.get("monto"))
        proveedor = request.form.get("proveedor")
        metodo_pago = request.form.get("metodo_pago")
        referencia = request.form.get("referencia")
        notas = request.form.get("notas")
        
        create_gasto(
            fecha=fecha,
            categoria=categoria,
            concepto=concepto,
            monto=monto,
            proveedor=proveedor,
            metodo_pago=metodo_pago,
            referencia=referencia,
            notas=notas
        )
        
        return redirect(url_for("admin_gastos"))
    except Exception as e:
        return f"Error al crear gasto: {str(e)}", 400

@app.route("/admin/finanzas/flujo-caja")
@require_permission("finanzas")
def admin_flujo_caja():
    """Cash flow report"""
    # Default to current month
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    
    if not fecha_inicio or not fecha_fin:
        # Get first and last day of current month
        today = datetime.now()
        fecha_inicio = today.replace(day=1).strftime("%Y-%m-%d")
        if today.month == 12:
            fecha_fin = today.replace(day=31).strftime("%Y-%m-%d")
        else:
            fecha_fin = (today.replace(month=today.month + 1, day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    flujo = get_flujo_caja(fecha_inicio, fecha_fin)
    gastos = get_gastos_by_periodo(fecha_inicio, fecha_fin)
    
    return render_template("admin_flujo_caja.html", 
                          flujo=flujo, 
                          gastos=gastos,
                          fecha_inicio=fecha_inicio,
                          fecha_fin=fecha_fin)

def num_a_letras(numero):
    """Convert number to words in Spanish (simplified but robust)"""
    unidades = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
    especiales = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISEIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE']
    decenas = ['', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
    centenas = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']
    
    entero = int(numero)
    
    if entero == 0:
        return "CERO"
    
    # Handle millions
    if entero >= 1000000:
        millones = entero // 1000000
        resto = entero % 1000000
        if millones == 1:
            resultado = "UN MILLON"
        else:
            resultado = f"{num_a_letras(millones)} MILLONES"
        if resto > 0:
            resultado += f" {num_a_letras(resto)}"
        return resultado.strip()
    
    # Handle thousands
    if entero >= 1000:
        miles = entero // 1000
        resto = entero % 1000
        if miles == 1:
            resultado = "MIL"
        else:
            resultado = f"{num_a_letras(miles)} MIL"
        if resto > 0:
            resultado += f" {num_a_letras(resto)}"
        return resultado.strip()
    
    # Handle hundreds
    resultado = ""
    if entero >= 100:
        if entero == 100:
            return "CIEN"
        resultado += centenas[entero // 100]
        entero = entero % 100
        if entero > 0:
            resultado += " "
    
    # Handle tens and units
    if entero >= 10 and entero < 20:
        resultado += especiales[entero - 10]
    elif entero >= 20:
        resultado += decenas[entero // 10]
        if entero % 10 > 0:
            resultado += f" Y {unidades[entero % 10]}"
    elif entero > 0:
        resultado += unidades[entero]
    
    return resultado.strip()

@app.route("/admin/finanzas/facturas/<int:id>/pdf")
@require_permission("finanzas")
def admin_factura_pdf(id):
    """Generate professional PDF for invoice with auto-wrapping"""
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    
    factura = get_factura_by_id(id)
    if not factura:
        return "Factura no encontrada", 404
    
    # Create PDF with SimpleDocTemplate for better layout
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=80)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=8, leading=10)
    style_cell = ParagraphStyle('CellWrap', parent=styles['Normal'], fontSize=7, leading=9)
    style_right = ParagraphStyle('Right', parent=styles['Normal'], fontSize=8, alignment=TA_RIGHT)
    
    HEADER_BG = colors.HexColor("#4472C4")
    
    # ====== HEADER ======
    logo_path = os.path.join("static", "img", "logo_inair.png")
    if os.path.exists(logo_path):
        logo = RLImage(logo_path, width=120, height=50)
    else:
        logo = Paragraph("<b>INAIR</b>", style_normal)
    
    company_info_text = Paragraph("""
        <para align="right" fontSize="7" leading="9">
        <b>INGENIERÍA EN AIRE</b><br/>
        RFC: IAM140525BG4<br/>
        AVENIDA ALFONSO VIDAL Y PLANAS # 435, INT. 5-A, NUEVA TIJUANA,<br/>
        DEL TIJUANA<br/>
        TIJUANA, BAJA CALIFORNIA, MEXICO CP 22435<br/>
        601 - GENERAL DE LEY PERSONAS MORALES
        </para>
    """, style_right)
    
    header_table = Table([[logo, company_info_text]], colWidths=[150, 365])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    
    # ====== FACTURA INFO BOX ======
    iva_percent = factura.get('iva_porcentaje', 16)
    if iva_percent < 1:
        iva_percent = iva_percent * 100
    
    factura_info = Paragraph(f"""
        <para align="right" fontSize="8" backColor="#E8F4F8" leftIndent="10" rightIndent="10" spaceBefore="8" spaceAfter="8">
        <b>Factura: {factura['numero_factura']}</b><br/>
        Fecha: {factura['fecha_emision']}<br/>
        Fecha vencimiento: {factura.get('fecha_vencimiento') or 'N/A'}<br/>
        F.C.: 1.0<br/>
        Comprobante: I- Ingreso<br/>
        Moneda: {factura.get('moneda', 'MXN')} Pesos
        </para>
    """, style_right)
    
    info_table = Table([[Spacer(1,1), factura_info]], colWidths=[315, 210])
    elements.append(info_table)
    elements.append(Spacer(1, 15))
    
    # ====== CLIENT SECTION ======
    # Get client details from database
    cliente_info = None
    if factura.get('cliente_id'):
        cliente_info = get_client_by_id(factura['cliente_id'])
    
    client_text = f"<b>Contacto:</b><br/><br/><b>{factura['cliente_nombre']}</b><br/>"
    
    if cliente_info:
        if cliente_info.get('direccion'):
            client_text += f"{cliente_info['direccion']}<br/>"
        if cliente_info.get('telefono'):
            client_text += f"Tel: {cliente_info['telefono']}<br/>"
    
    if factura.get('cliente_rfc'):
        client_text += f"RFC: {factura['cliente_rfc']}<br/>"
    
    if cliente_info and cliente_info.get('referencia'):
        client_text += f"Su referencia: {cliente_info['referencia']}"
    
    elements.append(Paragraph(client_text, style_normal))
    elements.append(Spacer(1, 15))
    
    # ====== ITEMS TABLE ======
    table_header = ['No.', 'Código', 'Descripción', 'Cantidad', 'Unidad', 'Precio unitario', 'Importe']
    data = [table_header]
    
    item_number = 1
    for partida in factura.get('partidas', []):
        # Wrap description and codigo in Paragraph for auto line break
        desc_paragraph = Paragraph(partida['descripcion'] or '', style_cell)
        codigo_paragraph = Paragraph(partida.get('codigo', 'N/A') or 'N/A', style_cell)
        
        data.append([
            str(item_number),
            codigo_paragraph,
            desc_paragraph,
            f"{partida['cantidad']:.2f}",
            partida.get('unidad', 'SER'),
            f"$ {partida['precio_unitario']:,.2f}",
            f"$ {partida['subtotal']:,.2f}"
        ])
        item_number += 1
    
    # Column widths: No., Código, Descripción, Cantidad, Unidad, Precio, Importe
    col_widths = [30, 75, 190, 50, 40, 70, 70]
    items_table = Table(data, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Body
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # No.
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Cantidad
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Unidad
        ('ALIGN', (5, 1), (6, -1), 'RIGHT'),   # Precios
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),   # TOP for multi-line text
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))
    
    # ====== TOTALS ======
    totals_data = [
        ['Subtotal', f"$ {factura['subtotal']:,.2f}"],
        [f"IVA {iva_percent:.0f}%", f"$ {factura['iva_monto']:,.2f}"],
        ['Total', f"$ {factura['total']:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[100, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 11),
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    # Right-align totals table
    totals_wrapper = Table([[Spacer(1,1), totals_table]], colWidths=[325, 200])
    elements.append(totals_wrapper)
    elements.append(Spacer(1, 15))
    
    # ====== PAYMENT CONDITIONS TEXT ======
    payment_conditions = f"""
    <para fontSize="7" leading="9" alignment="justify">
    POR ESTE PAGARÉ ME(NOS) OBLIGO(AMOS) A PAGAR INCONDICIONALMENTE A LA ORDEN DE INGENIERÍA EN AIRE S.A. DE C.V. 
    POR LA CANTIDAD DE: MXN $ {factura['total']:,.2f} - {num_a_letras(factura['total'])} PESOS M.N. EN LA CIUDAD DE TIJUANA, 
    BAJA CALIFORNIA AL VENCIMIENTO DE ESTE TÍTULO. LA SUMA QUE AMPARA ESTE PAGARÉ CAUSARÁ INTERESES MORATORIOS A RAZÓN DEL 5% 
    MENSUAL A PARTIR DE LA FECHA DE SU VENCIMIENTO. EN CASO DE COBRO JUDICIAL PAGARÉ LOS GASTOS QUE SE OCASIONEN, 
    RENUNCIANDO A MI AFUERO DOMICILIARIO.
    </para>
    """
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(payment_conditions, style_normal))
    elements.append(Spacer(1, 10))
    
    # Signature line
    signature_line = Paragraph("<para alignment='center'>_______________________________________<br/>Nombre y firma</para>", style_normal)
    elements.append(signature_line)
    elements.append(Spacer(1, 15))
    
    # ====== GENERATE QR CODE AND FISCAL INFO ======
    # Generate placeholder UUID (Folio Fiscal)
    import uuid
    folio_fiscal = str(uuid.uuid4()).upper()
    
    # Generate QR for SAT/CFDI compliance
    try:
        import qrcode
        from io import BytesIO as QRBuffer
        
        # QR content with fiscal information (SAT format)
        qr_content = f"""https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?id={folio_fiscal}&re=IAI160525B06&rr={factura.get('cliente_rfc', 'XAXX010101000')}&tt={factura['total']:.6f}&fe={factura['numero_factura'][-8:]}"""
        
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(qr_content)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR to buffer
        qr_buffer = QRBuffer()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # QR image (larger)
        qr_image = RLImage(qr_buffer, width=120, height=120)
        
    except Exception as e:
        print(f"Error generating QR: {e}")
        qr_image = Paragraph("<i>QR no disponible</i>", style_cell)
    
    # ====== DIGITAL SEALS (SELLOS) ======
    # Placeholder seals (would come from PAC in production)
    sello_emisor = "DWXYHCYjywWZLTtHrjr59T67gRexsq0LduDdkKhgpfL4GplkqzrhkBvpDrpsDnjhYstE6aSaJmS0thwr/BbUlYBc4uY6oQaQz+180+ovk3z8UlkcQJXhoIcWEmTtXDMxVaQj..."
    sello_sat = "QNQHZSYXNWYt0+5dt+ENE0IRY/YUAIEIks8R0ZSoQCPwF/+ONzH+NWT+oZ3aSt1+g8RlKYdR/dHfEiXgwtHyEOtShr/0HCKRvsfcPRt+TzW6IKhICN6kcsHN0XEFy..."
    cadena_original = "||1.1|05A40679-2B1E-5517-8272-C77760E03572|2025-09-08 18:02:09|IAI160525B06|" + sello_emisor[:50] + "...|00001000000707310321||"
    
    # Build fiscal information section
    fiscal_info_left = f"""
    <para fontSize="6" leading="7">
    <b>Sello digital del emisor:</b><br/>
    {sello_emisor}<br/><br/>
    <b>Sello digital del SAT:</b><br/>
    {sello_sat}<br/><br/>
    <b>Cadena original del complemento de certificación digital del SAT:</b><br/>
    {cadena_original}
    </para>
    """
    
    fecha_emision_dt = datetime.strptime(factura['fecha_emision'], '%Y-%m-%d') if isinstance(factura['fecha_emision'], str) else datetime.now()
    fecha_certificacion = fecha_emision_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    fiscal_info_right = f"""
    <para fontSize="6" leading="8">
    <b>Información Extra</b><br/>
    Certificado del emisor: 00001000000707923758 | Certificado SAT: 00001000000707310321<br/>
    Lugar de expedición: 22435 | Régimen Fiscal:601<br/>
    Fecha de Emisión: {fecha_certificacion} | Fecha de Certificación: {fecha_certificacion}<br/><br/>
    
    <b>Uso del CFDI:</b> {factura.get('uso_cfdi', 'Gastos en general')}<br/>
    <b>Condiciones de pago:</b> {factura.get('condiciones_pago', '30 días')}<br/>
    <b>Método de pago:</b> {factura.get('metodo_pago', 'PPD')}<br/>
    <b>Forma de pago:</b> {factura.get('forma_pago', 'Por definir')}<br/><br/>
    
    <b>Folio SAT:</b> {folio_fiscal}<br/>
    <b>Lugar de expedición:</b> 22435 - TIJUANA, BAJA CALIFORNIA<br/>
    <b>Fecha de certificación:</b> {fecha_certificacion}<br/>
    <b>Certificado emisor:</b> 00001000000707923758<br/>
    <b>Certificado SAT:</b> 00001000000707310321<br/>
    </para>
    """
    
    # Create table with QR and fiscal info
    fiscal_table_data = [
        [qr_image, Paragraph(fiscal_info_right, style_cell)]
    ]
    fiscal_table = Table(fiscal_table_data, colWidths=[130, 395])
    fiscal_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
    ]))
    
    elements.append(Paragraph(fiscal_info_left, style_cell))
    elements.append(Spacer(1, 10))
    elements.append(fiscal_table)
    elements.append(Spacer(1, 10))
    
    # Final text
    cfdi_text = Paragraph("<para alignment='center' fontSize='7'><b>Este documento es una representación impresa del CFDI</b></para>", style_normal)
    elements.append(cfdi_text)
    
    # ====== FOOTER FUNCTION ======
    def add_footer(canvas, doc):
        canvas.saveState()
        # Footer line (similar to quotation style)
        canvas.setStrokeColor(colors.HexColor('#E74C3C'))
        canvas.setLineWidth(1.5)
        canvas.line(40, 70, A4[0] - 40, 70)
        
        # Company info in grey (more subtle)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(40, 55, "INGENIERÍA EN AIRE SA DE CV  RFC: IAI160525B06")
        canvas.setFont('Helvetica', 6)
        canvas.drawString(40, 45, "Avenida Alfonso Vidal y Planas #445, Interior S/N, Colonia Nueva Tijuana, Tijuana, Baja California, México, Cp: 22435")
        canvas.drawString(40, 35, "Tel: (664) 250-0022 | pedidos@inair.com.mx | www.inair.com.mx")
        
        # Status and date on right
        canvas.setFont('Helvetica', 6)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(A4[0] - 40, 55, f"Estado: {factura['estado_pago']}")
        canvas.drawRightString(A4[0] - 40, 47, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        canvas.restoreState()
    
    # Build PDF
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    
    # Return PDF - check if preview mode
    is_preview = request.args.get('preview') == 'true'
    return send_file(buffer, mimetype='application/pdf', 
                     as_attachment=not is_preview, 
                     download_name=f"Factura_{factura['numero_factura']}.pdf" if not is_preview else None)

@app.route("/admin/finanzas/facturas/<int:factura_id>/complemento-pago/pdf")
@require_permission("finanzas")
def admin_complemento_pago_pdf(factura_id):
    """Generate professional payment complement PDF"""
    from reportlab.lib import colors
    
    factura = get_factura_by_id(factura_id)
    if not factura:
        return "Factura no encontrada", 404
    
    if not factura.get('pagos'):
        return "No hay pagos registrados para esta factura", 400
    
    # Create PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # ====== HEADER SECTION ======
    # Logo
    try:
        logo_path = os.path.join("static", "img", "logo_inair.png")
        if os.path.exists(logo_path):
            p.drawImage(logo_path, 40, height - 90, width=140, height=70, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"Error loading logo: {e}")
    
    # Company info (right side of header)
    y = height - 45
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.HexColor('#333333'))
    
    company_info = [
        "INGENIERÍA EN AIRE",
        "RFC: IAM140525BG4",
        "AVENIDA ALFONSO VIDAL Y PLANAS # 435, INT. 5-A, NUEVA TIJUANA,",
        "DEL TIJUANA",
        "TIJUANA, BAJA CALIFORNIA, MEXICO CP 22435"
    ]
    
    for line in company_info:
        p.drawRightString(width - 40, y, line)
        y -= 10
    
    # ====== DOCUMENT TITLE ======
    y = height - 140
    p.setFillColor(colors.HexColor('#4472C4'))
    p.rect(40, y - 25, width - 80, 25, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, y - 15, "COMPLEMENTO DE PAGO")
    
    # ====== INFO BOX ======
    y -= 45
    p.setFillColor(colors.HexColor('#E8F4F8'))
    p.rect(40, y - 60, width - 80, 60, fill=1, stroke=0)
    
    p.setFillColor(colors.HexColor('#000000'))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y - 15, "Factura Relacionada:")
    p.setFont("Helvetica", 9)
    p.drawString(180, y - 15, factura['numero_factura'])
    
    p.setFont("Helvetica", 8)
    y_info = y - 30
    p.drawString(50, y_info, f"Fecha de Factura: {factura['fecha_emision']}")
    p.drawString(300, y_info, f"Total Factura: ${factura['total']:,.2f}")
    y_info -= 15
    p.drawString(50, y_info, f"Cliente: {factura['cliente_nombre']}")
    y_info -= 15
    if factura.get('cliente_rfc'):
        p.drawString(50, y_info, f"RFC: {factura['cliente_rfc']}")
    
    # ====== PAYMENTS TABLE ======
    y -= 90
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.HexColor('#000000'))
    p.drawString(40, y, "Pagos Realizados:")
    
    y -= 20
    # Table header
    p.setFillColor(colors.HexColor('#4472C4'))
    p.rect(40, y - 15, width - 80, 15, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 8)
    p.drawString(50, y - 10, "Fecha de Pago")
    p.drawString(160, y - 10, "Método")
    p.drawString(280, y - 10, "Referencia")
    p.drawRightString(width - 50, y - 10, "Monto")
    
    y -= 20
    
    # Payment rows
    p.setFillColor(colors.HexColor('#000000'))
    p.setFont("Helvetica", 8)
    
    row_color_toggle = True
    total_pagado = 0
    
    for pago in factura['pagos']:
        if y < 150:  # New page if needed
            p.showPage()
            y = height - 60
            p.setFont("Helvetica", 8)
        
        # Alternate row colors
        if row_color_toggle:
            p.setFillColor(colors.HexColor('#F2F2F2'))
            p.rect(40, y - 15, width - 80, 15, fill=1, stroke=0)
        row_color_toggle = not row_color_toggle
        
        p.setFillColor(colors.HexColor('#000000'))
        p.drawString(50, y - 10, pago['fecha_pago'])
        p.drawString(160, y - 10, pago.get('metodo', '-'))
        p.drawString(280, y - 10, pago.get('referencia', '-')[:30])
        p.drawRightString(width - 50, y - 10, f"${pago['monto']:,.2f}")
        
        total_pagado += pago['monto']
        y -= 20
    
    # ====== TOTALS ======
    y -= 10
    p.setFillColor(colors.HexColor('#4472C4'))
    p.rect(width - 250, y - 25, 210, 25, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(width - 240, y - 15, "TOTAL PAGADO:")
    p.drawRightString(width - 50, y - 15, f"${total_pagado:,.2f}")
    
    # ====== STATUS INFO ======
    y -= 50
    p.setFillColor(colors.HexColor('#000000'))
    p.setFont("Helvetica", 9)
    
    saldo = factura['saldo_pendiente']
    estado_color = colors.HexColor('#27ae60') if saldo == 0 else colors.HexColor('#e74c3c')
    
    p.setFillColor(estado_color)
    p.drawString(40, y, f"Estado: {factura['estado_pago']}")
    p.drawString(40, y - 15, f"Saldo Pendiente: ${saldo:,.2f}")
    
    # ====== FOOTER ======
    p.setFont("Helvetica", 6)
    p.setFillColor(colors.HexColor('#666666'))
    footer_text = f"Este documento certifica los pagos realizados | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    p.drawCentredString(width / 2, 30, footer_text)
    
    p.save()
    buffer.seek(0)
    
    # Return PDF - check if preview mode
    is_preview = request.args.get('preview') == 'true'
    return send_file(buffer, mimetype='application/pdf', 
                     as_attachment=not is_preview, 
                     download_name=f"Complemento_Pago_{factura['numero_factura']}.pdf" if not is_preview else None)





# ==================== COMPRAS MODULE ROUTES ====================



# ----- PROVEEDORES ROUTES -----



@app.route("/admin/proveedores")
@require_permission("compras")
def admin_proveedores():

    """Manage Suppliers"""

    proveedores = get_all_proveedores()

    return render_template("admin_proveedores.html", proveedores=proveedores)



@app.route("/admin/proveedores/nuevo", methods=["POST"])
@require_permission("compras")
def admin_proveedores_nuevo():

    """Create new Supplier"""

    data = {

        'nombre_empresa': request.form.get('nombre_empresa'),

        'contacto_nombre': request.form.get('contacto_nombre'),

        'telefono': request.form.get('telefono'),

        'email': request.form.get('email'),

        'direccion': request.form.get('direccion'),

        'rfc': request.form.get('rfc')

    }

    create_proveedor(data)

    return redirect(url_for("admin_proveedores"))



@app.route("/admin/proveedores/editar/<int:id>", methods=["POST"])
@require_permission("compras")
def admin_proveedores_editar(id):

    """Update Supplier"""

    data = {

        'nombre_empresa': request.form.get('nombre_empresa'),

        'contacto_nombre': request.form.get('contacto_nombre'),

        'telefono': request.form.get('telefono'),

        'email': request.form.get('email'),

        'direccion': request.form.get('direccion'),

        'rfc': request.form.get('rfc')

    }

    update_proveedor(id, data)

    return redirect(url_for("admin_proveedores"))



@app.route("/admin/proveedores/eliminar/<int:id>", methods=["POST"])

@require_role("admin")

def admin_proveedores_eliminar(id):

    """Delete Supplier"""

    delete_proveedor(id)

    return redirect(url_for("admin_proveedores"))



# ----- COMPRAS (PURCHASE ORDERS) ROUTES -----



@app.route("/admin/compras")
@require_permission("compras")
def admin_compras():

    """Purchases Dashboard"""

    compras = get_all_compras()

    return render_template("admin_compras.html", compras=compras)



@app.route("/admin/compras/nueva", methods=["GET", "POST"])
@require_permission("compras")
def admin_compras_nueva():

    """Create new Purchase Order"""

    if request.method == "POST":

        data = {

            'proveedor_id': request.form.get('proveedor_id'),

            'fecha_emision': request.form.get('fecha_emision'),

            'fecha_entrega_estimada': request.form.get('fecha_entrega_estimada'),

            'estado': 'Borrador',

            'moneda': request.form.get('moneda'),

            'subtotal': float(request.form.get('subtotal') or 0),

            'iva': float(request.form.get('iva') or 0),

            'total': float(request.form.get('total') or 0),

            'notas': request.form.get('notas')

        }

        

        # Process items

        items = []

        numeros_parte = request.form.getlist('numero_parte[]')

        descripciones = request.form.getlist('descripcion[]')

        cantidades = request.form.getlist('cantidad[]')

        unidades = request.form.getlist('unidad[]')

        precios = request.form.getlist('precio_unitario[]')

        importes = request.form.getlist('importe[]')

        

        for i in range(len(numeros_parte)):

            if numeros_parte[i] or descripciones[i]:

                items.append({

                    'linea': i+1,

                    'numero_parte': numeros_parte[i],

                    'descripcion': descripciones[i],

                    'cantidad': float(cantidades[i] or 0),

                    'unidad': unidades[i],

                    'precio_unitario': float(precios[i] or 0),

                    'importe': float(importes[i] or 0)

                })

        

        user_id = session.get('user_id')

        create_compra(data, items, user_id)

        return redirect(url_for("admin_compras"))

        

    proveedores = get_all_proveedores()

    folio = get_next_compra_folio()

    fecha_hoy = datetime.now().strftime('%Y-%m-%d')

    return render_template("admin_compra_form.html", proveedores=proveedores, folio=folio, fecha_hoy=fecha_hoy)



@app.route("/admin/compras/editar/<int:id>", methods=["GET", "POST"])
@require_permission("compras")
def admin_compras_editar(id):

    """Edit Purchase Order"""

    compra = get_compra_by_id(id)

    if not compra:

        return "Orden de Compra no encontrada", 404



    if request.method == "POST":

        data = {

            'proveedor_id': request.form.get('proveedor_id'),

            'fecha_emision': request.form.get('fecha_emision'),

            'fecha_entrega_estimada': request.form.get('fecha_entrega_estimada'),

            'estado': request.form.get('estado'),

            'moneda': request.form.get('moneda'),

            'subtotal': float(request.form.get('subtotal') or 0),

            'iva': float(request.form.get('iva') or 0),

            'total': float(request.form.get('total') or 0),

            'notas': request.form.get('notas')

        }

        

        items = []

        numeros_parte = request.form.getlist('numero_parte[]')

        descripciones = request.form.getlist('descripcion[]')

        cantidades = request.form.getlist('cantidad[]')

        unidades = request.form.getlist('unidad[]')

        precios = request.form.getlist('precio_unitario[]')

        importes = request.form.getlist('importe[]')

        

        for i in range(len(numeros_parte)):

             if numeros_parte[i] or descripciones[i]:

                items.append({

                    'linea': i+1,

                    'numero_parte': numeros_parte[i],

                    'descripcion': descripciones[i],

                    'cantidad': float(cantidades[i] or 0),

                    'unidad': unidades[i],

                    'precio_unitario': float(precios[i] or 0),

                    'importe': float(importes[i] or 0)

                })

        

        update_compra(id, data, items)

        return redirect(url_for("admin_compras"))

        

    proveedores = get_all_proveedores()

    return render_template("admin_compra_form.html", compra=compra, proveedores=proveedores)



@app.route("/admin/compras/pdf/<int:id>")
@require_permission("compras")
def admin_compras_pdf(id):

    """Generate PDF for Purchase Order"""

    compra = get_compra_by_id(id)

    if not compra:

        return "Orden de Compra no encontrada", 404

        

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=80)

    elements = []

    styles = getSampleStyleSheet()

    

    # Colors

    INAIR_RED = colors.HexColor("#D20000")

    

    # Header

    logo_path = os.path.join(app.root_path, 'static', 'img', 'logo_inair.png')

    if os.path.exists(logo_path):

        logo = Image(logo_path, width=120, height=40)

        header_left = logo

    else:

        header_left = Paragraph("<b>INAIR</b>", styles['Heading1'])

        

    header_right = Paragraph(f"""

        <b>ORDEN DE COMPRA</b><br/>

        <font size="14" color="#D20000"><b>{compra['folio']}</b></font><br/>

        Fecha: {compra['fecha_emision']}<br/>

        Entrega: {compra['fecha_entrega_estimada'] or 'Por definir'}

    """, ParagraphStyle('Right', parent=styles['Normal'], alignment=2))

    

    header_table = Table([[header_left, header_right]], colWidths=[300, 230])

    elements.append(header_table)

    elements.append(Spacer(1, 20))

    

    # Supplier Info

    proveedor_info = f"""

        <b>PROVEEDOR:</b><br/>

        {compra['proveedor_nombre']}<br/>

        {compra['proveedor_direccion'] or ''}<br/>

        RFC: {compra['proveedor_rfc'] or 'N/A'}<br/>

        Contacto: {compra['proveedor_contacto'] or ''} ({compra['proveedor_telefono'] or ''})

    """

    elements.append(Paragraph(proveedor_info, styles['Normal']))

    elements.append(Spacer(1, 15))

    

    # Items Table

    data = [['Parte', 'Descripción', 'Cant.', 'Unidad', 'P. Unit.', 'Importe']]

    for item in compra['items']:

        data.append([

            item['numero_parte'],

            Paragraph(item['descripcion'], styles['Normal']),

            f"{item['cantidad']}",

            item['unidad'],

            f"${item['precio_unitario']:,.2f}",

            f"${item['importe']:,.2f}"

        ])

    

    table = Table(data, colWidths=[80, 200, 50, 50, 70, 80])

    table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),

        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

    ]))

    elements.append(table)

    elements.append(Spacer(1, 15))

    

    # Totals

    totals = f"""

        <b>Subtotal:</b> ${compra['subtotal']:,.2f} {compra['moneda']}<br/>

        <b>IVA:</b> ${compra['iva']:,.2f} {compra['moneda']}<br/>

        <font size="12" color="#D20000"><b>Total: ${compra['total']:,.2f} {compra['moneda']}</b></font>

    """

    elements.append(Paragraph(totals, ParagraphStyle('RightTotals', parent=styles['Normal'], alignment=2)))

    

    if compra['notas']:

        elements.append(Spacer(1, 20))

        elements.append(Paragraph(f"<b>Notas:</b> {compra['notas']}", styles['Normal']))

    

    doc.build(elements)

    buffer.seek(0)

    return send_file(buffer, mimetype='application/pdf', as_attachment=False, download_name=f"{compra['folio']}.pdf")




# ==================== ALMACEN API ROUTES ====================

@app.route("/api/almacen/detalles/<int:id>")
@require_permission("almacen")
def api_almacen_detalles(id):
    """Get refaccion details including reservations"""
    try:
        refaccion = get_refaccion_by_id(id)
        if not refaccion:
            return jsonify({"success": False, "error": "Refacción no encontrada"}), 404
            
        reservas = get_reservas_by_refaccion(id)
        
        # Calculate availability
        total_qty = refaccion.get('cantidad', 0)
        reserved_qty = sum(r.get('cantidad', 0) for r in reservas)
        available_qty = total_qty - reserved_qty
        
        return jsonify({
            "success": True,
            "refaccion": refaccion,
            "reservas": reservas,
            "stats": {
                "total": total_qty,
                "reserved": reserved_qty,
                "available": available_qty
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/almacen/reservar", methods=["POST"])
@require_permission("almacen")
def api_almacen_reservar():
    """Create a reservation"""
    try:
        data = request.json
        refaccion_id = data.get('refaccion_id')
        cliente_id = data.get('cliente_id')
        cantidad = int(data.get('cantidad', 0))
        orden_compra = data.get('orden_compra', '')
        
        if not refaccion_id or cantidad <= 0:
            return jsonify({"success": False, "error": "Datos inválidos"}), 400
            
        # Optional: check availability before reserving? 
        # For now, allow over-reservation but warn in UI? 
        # Let's just create it.
        
        create_reserva(refaccion_id, cliente_id, cantidad, orden_compra)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/almacen/reservar/eliminar/<int:id>", methods=["POST"])
@require_permission("almacen")
def api_almacen_eliminar_reserva(id):
    """Cancel a reservation"""
    try:
        if delete_reserva(id):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "No se pudo eliminar"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== GESTION DE PI (PROFORMA INVOICES) ROUTES ====================

@app.route("/admin/pi")
@require_permission("pi")
def admin_pis():
    """List Proforma Invoices"""
    pis = get_all_pis()
    user_puesto = session.get('puesto', '')
    can_edit = has_permission('pi_edit')
    return render_template("admin_pi_list.html", pis=pis, user_puesto=user_puesto, can_edit=can_edit)

@app.route("/admin/pi/nueva", methods=["GET", "POST"])
@require_permission("pi")
def admin_pi_nueva():
    """Create new Proforma Invoice"""
    if request.method == "POST":
        try:
            # Generate folio
            folio = get_next_pi_folio()
            
            data = {
                'folio': folio,
                'fecha': request.form.get('fecha'),
                'proveedor_id': request.form.get('proveedor_id'),
                'proveedor_nombre': request.form.get('proveedor_nombre'),
                'atencion_a': request.form.get('atencion_a'),
                'referencia': request.form.get('referencia'),
                'orden_compra_id': request.form.get('orden_compra_id') or None,
                'cotizacion_id': request.form.get('cotizacion_id') or None,
                'cliente_id': request.form.get('cliente_id') or None,
                'cliente_nombre': request.form.get('cliente_nombre'),
                'moneda': request.form.get('moneda', 'USD'),
                'tipo_cambio': float(request.form.get('tipo_cambio', 1.0)),
                'tiempo_entrega': request.form.get('tiempo_entrega'),
                'condiciones_pago': request.form.get('condiciones_pago'),
                'notas': request.form.get('notas'),
                'created_by': session.get('user_id')
            }
            
            # Process Items
            items = []
            lineas = request.form.getlist('item_linea[]')
            if lineas:
                cantidades = request.form.getlist('item_cantidad[]')
                unidades = request.form.getlist('item_unidad[]')
                partes = request.form.getlist('item_numero_parte[]')
                descripciones = request.form.getlist('item_descripcion[]')
                estatus_list = request.form.getlist('item_estatus[]') # New field
                tiempos = request.form.getlist('item_tiempo_entrega[]')
                precios = request.form.getlist('item_precio_unitario[]')
                
                for i in range(len(lineas)):
                    qty = float(cantidades[i] or 0)
                    price = float(precios[i] or 0)
                    items.append({
                        'linea': i + 1,
                        'cantidad': qty,
                        'unidad': unidades[i],
                        'numero_parte': partes[i],
                        'descripcion': descripciones[i],
                        'estatus': estatus_list[i] if i < len(estatus_list) else 'Pendiente',
                        'tiempo_entrega_item': tiempos[i],
                        'precio_unitario': price,
                        'importe': qty * price
                    })
            
            # Calculate Totals
            subtotal = sum(item['importe'] for item in items)
            iva_pct = float(request.form.get('iva_porcentaje', 16))
            iva_monto = subtotal * (iva_pct / 100)
            total = subtotal + iva_monto
            
            
            data['subtotal'] = subtotal
            data['iva_porcentaje'] = iva_pct
            data['iva_monto'] = iva_monto
            data['total'] = total
            data['solicitado_por'] = request.form.get('solicitado_por')
            
            pi_id = create_pi(data, items)
            
            if pi_id:
                # Link to Deal if provided
                deal_id = request.form.get('deal_id')
                if deal_id:
                    link_pi_to_deal(deal_id, pi_id)
                flash("PI creada correctamente", "success")
                return redirect(url_for('admin_pis'))
            else:
                 return "Error creating PI", 500
            
        except Exception as e:
            return f"Error creating PI: {e}", 400

    # GET
    proveedores = get_all_proveedores()
    next_folio = get_next_pi_folio()
    compras_list = get_all_compras() # For linking to existing POs
    users = get_all_users()
    clients = get_all_clients()
    
    # Capture deal params
    deal_id = request.args.get('deal_id')
    cliente_id_arg = request.args.get('cliente_id')
    
    return render_template("admin_pi_form.html", pi=None, suppliers=proveedores, next_folio=next_folio, compras=compras_list, users=users, clients=clients, deal_id=deal_id, cliente_id_arg=cliente_id_arg)

@app.route("/admin/pi/editar/<int:id>", methods=["GET", "POST"])
@require_permission("pi_edit")
def admin_pi_editar(id):
    """Edit Proforma Invoice"""
    if request.method == "POST":
        try:
            data = {
                'fecha': request.form.get('fecha'),
                'proveedor_id': request.form.get('proveedor_id'),
                'proveedor_nombre': request.form.get('proveedor_nombre'),
                'atencion_a': request.form.get('atencion_a'),
                'referencia': request.form.get('referencia'),
                'orden_compra_id': request.form.get('orden_compra_id') or None,
                'cotizacion_id': request.form.get('cotizacion_id') or None,
                'cliente_id': request.form.get('cliente_id') or None,
                'cliente_nombre': request.form.get('cliente_nombre'),
                'moneda': request.form.get('moneda', 'USD'),
                'tipo_cambio': float(request.form.get('tipo_cambio', 1.0)),
                'tiempo_entrega': request.form.get('tiempo_entrega'),
                'condiciones_pago': request.form.get('condiciones_pago'),
                'notas': request.form.get('notas')
            }
            
            # Process Items (Same logic as create)
            items = []
            lineas = request.form.getlist('item_linea[]')
            if lineas:
                cantidades = request.form.getlist('item_cantidad[]')
                unidades = request.form.getlist('item_unidad[]')
                partes = request.form.getlist('item_numero_parte[]')
                descripciones = request.form.getlist('item_descripcion[]')
                estatus_list = request.form.getlist('item_estatus[]')
                tiempos = request.form.getlist('item_tiempo_entrega[]')
                precios = request.form.getlist('item_precio_unitario[]')
                
                for i in range(len(lineas)):
                    qty = float(cantidades[i] or 0)
                    price = float(precios[i] or 0)
                    items.append({
                        'linea': i + 1,
                        'cantidad': qty,
                        'unidad': unidades[i],
                        'numero_parte': partes[i],
                        'descripcion': descripciones[i],
                        'estatus': estatus_list[i] if i < len(estatus_list) else 'Pendiente',
                        'tiempo_entrega_item': tiempos[i],
                        'precio_unitario': price,
                        'importe': qty * price
                    })
            
            subtotal = sum(item['importe'] for item in items)
            iva_pct = float(request.form.get('iva_porcentaje', 16))
            iva_monto = subtotal * (iva_pct / 100)
            total = subtotal + iva_monto
            
            data['subtotal'] = subtotal
            data['iva_porcentaje'] = iva_pct
            data['iva_monto'] = iva_monto
            data['total'] = total
            data['solicitado_por'] = request.form.get('solicitado_por')
            
            update_pi(id, data, items)
            return redirect(url_for('admin_pis'))
            
        except Exception as e:
            return f"Error updating PI: {e}", 400
            
    # GET
    pi = get_pi_by_id(id)
    if not pi: return "PI Not Found", 404
    proveedores = get_all_proveedores()
    compras_list = get_all_compras()
    users = get_all_users()
    clients = get_all_clients()
    return render_template("admin_pi_form.html", pi=pi, suppliers=proveedores, next_folio=pi['folio'], compras=compras_list, users=users, clients=clients)

@app.route("/admin/pi/eliminar/<int:id>", methods=["POST"])
@require_permission("pi_edit")
def admin_pi_eliminar(id):
    delete_pi(id)
    return redirect(url_for('admin_pis'))

@app.route("/admin/pi/pdf/<int:id>")
@require_permission("pi")
def admin_pi_pdf(id):
    """Generate Professional PDF for PI"""
    pi = get_pi_by_id(id)
    if not pi: return "PI Not Found", 404
    
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # --- Header ---
    # Logo
    logo_path = os.path.join(APP_ROOT, 'static', 'img', 'logo_inair.png')
    if os.path.exists(logo_path):
        try:
            # Draw logo simple
            c.drawImage(logo_path, 40, height - 100, width=180, height=50, preserveAspectRatio=True, mask='auto', anchor='nw')
        except Exception as e:
            print(f"Error drawing logo: {e}")
            pass # Fallback

    # Company Info / PI Title
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(width - 50, height - 60, f"PROFORMA INVOICE")
    c.setFont("Helvetica", 12)
    c.drawRightString(width - 50, height - 80, f"{pi['folio']}")
    
    # --- Info Block ---
    y = height - 130
    c.setStrokeColor(colors.lightgrey)
    c.line(40, y + 10, width - 40, y + 10)
    
    # Left Column (Client/Provider)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Proveedor:")
    c.setFont("Helvetica", 10)
    c.drawString(110, y, pi['proveedor_nombre'])
    
    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Atención A:")
    c.setFont("Helvetica", 10)
    c.drawString(110, y, pi['atencion_a'] or "")

    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Cliente:")
    c.setFont("Helvetica", 10)
    c.drawString(110, y, pi['cliente_nombre'] or "N/A")

    # Right Column (Dates/Refs)
    y_right = height - 130
    c.setFont("Helvetica-Bold", 10)
    c.drawString(350, y_right, "Fecha:")
    c.setFont("Helvetica", 10)
    c.drawString(430, y_right, pi['fecha'])
    
    y_right -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(350, y_right, "Referencia:")
    c.setFont("Helvetica", 10)
    c.drawString(430, y_right, pi['referencia'] or "N/A")
    
    y_right -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(350, y_right, "Solicitado Por:")
    c.setFont("Helvetica", 10)
    c.drawString(430, y_right, pi.get('solicitado_por') or "N/A")
    
    y -= 30
    
    # --- Items Table ---
    # Headers
    c.setFillColor(colors.whitesmoke)
    c.rect(40, y - 5, width - 80, 20, fill=1, stroke=0)
    c.setFillColor(colors.black)
    
    header_y = y
    c.setFont("Helvetica-Bold", 9)
    c.drawString(45, header_y, "Ln")
    c.drawString(70, header_y, "Cant")
    c.drawString(110, header_y, "Parte / Descripción")
    c.drawString(380, header_y, "Entrega")
    c.drawString(440, header_y, "Status")
    c.drawRightString(width - 45, header_y, "Importe")
    
    y -= 20
    
    c.setFont("Helvetica", 9)
    moneda_symbol = "$" if pi['moneda'] == 'USD' else "MXN "
    
    for item in pi['items']:
        # Check page break
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)
            
        c.drawString(45, y, str(item['linea']))
        c.drawString(70, y, f"{item['cantidad']} {item['unidad']}")
        
        # Description (Wrapped or Truncated)
        desc_text = f"{item['numero_parte']} - {item['descripcion']}"
        if len(desc_text) > 55:
            desc_text = desc_text[:52] + "..."
        c.drawString(110, y, desc_text)
        
        c.drawString(380, y, item['tiempo_entrega_item'] or "")
        
        # Status
        status = item['estatus']
        # Simple color coding for status text (optional)
        if status == 'Recibido': c.setFillColor(colors.green)
        elif status == 'Cancelado': c.setFillColor(colors.red)
        elif status == 'En Tránsito': c.setFillColor(colors.blue)
        else: c.setFillColor(colors.black)
        
        c.drawString(440, y, status)
        c.setFillColor(colors.black) # Reset
        
        c.drawRightString(width - 45, y, f"{moneda_symbol}{item['importe']:,.2f}")
        
        y -= 15

    c.line(40, y+5, width - 40, y+5)
    y -= 20

    # --- Totals & Notes ---
    
    # Notes (Left side)
    notes_y = y
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, notes_y, "Notas:")
    c.setFont("Helvetica", 9)
    text_object = c.beginText(40, notes_y - 15)
    # Simple formatting for notes
    notas = pi.get('notas') or "Sin notas adicionales."
    # Wrap notes simple
    max_char = 60
    for line in notas.split('\n'):
        while len(line) > max_char:
            text_object.textLine(line[:max_char])
            line = line[max_char:]
        text_object.textLine(line)
    c.drawText(text_object)
    
    # Totals (Right side)
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 120, y, "Subtotal:")
    c.drawRightString(width - 45, y, f"{moneda_symbol}{pi['subtotal']:,.2f}")
    
    y -= 15
    c.drawRightString(width - 120, y, f"IVA ({pi['iva_porcentaje']}%):")
    c.drawRightString(width - 45, y, f"{moneda_symbol}{pi['iva_monto']:,.2f}")
    
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 120, y, f"Total {pi['moneda']}:")
    c.drawRightString(width - 45, y, f"{moneda_symbol}{pi['total']:,.2f}")

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawCentredString(width/2, 30, "Documento generado internamente por INAIR REPORTES")

    c.save()
    buffer.seek(0)
    # Removed as_attachment=True to enable browser preview
    return send_file(buffer, mimetype='application/pdf')

@app.route("/admin/pi/excel/<int:id>")
@require_permission("pi")
def admin_pi_excel(id):
    """Generate simple CSV/Excel dump"""
    pi = get_pi_by_id(id)
    if not pi: return "PI Not Found", 404
    
    # Simple CSV construction
    output = io.StringIO()
    output.write("Folio,Fecha,Proveedor,Referencia,Moneda,Total\n")
    output.write(f"{pi['folio']},{pi['fecha']},{pi['proveedor_nombre']},{pi['referencia']},{pi['moneda']},{pi['total']}\n")
    output.write("\nItems\n")
    output.write("Cantidad,Parte,Descripcion,Estatus,Precio,Importe\n")
    for item in pi['items']:
        desc = (item['descripcion'] or "").replace(",", " ")
        output.write(f"{item['cantidad']},{item['numero_parte']},{desc},{item['estatus']},{item['precio_unitario']},{item['importe']}\n")
        
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(mem, as_attachment=True, download_name=f"{pi['folio']}.csv", mimetype='text/csv')


@app.route("/api/pi/item/<int:item_id>/status", methods=["POST"])
@require_permission("cotizaciones")
def api_update_pi_item_status(item_id):
    """Update single PI item status"""
    try:
        data = request.get_json()
        status = data.get('status')
        if update_pi_item_status(item_id, status):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Database error"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/pi/<int:pi_id>/status-all", methods=["POST"])
@require_permission("cotizaciones")
def api_update_pi_bulk_status(pi_id):
    """Update ALL items in a PI"""
    try:
        data = request.get_json()
        status = data.get('status')
        if update_pi_items_bulk(pi_id, status):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Database error"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":

    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
