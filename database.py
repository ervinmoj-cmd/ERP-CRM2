import sqlite3
import os
from datetime import datetime, timedelta

DB_NAME = "inair_reportes.db"

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with tables"""
    with get_db() as conn:
        cursor = conn.cursor()

        def column_exists(table, column):
            cursor.execute(f"PRAGMA table_info({table})")
            return any(row['name'] == column for row in cursor.fetchall())
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre TEXT NOT NULL,
                prefijo TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'technician',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Clients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                contacto TEXT,
                telefono TEXT,
                email TEXT,
                direccion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Client Equipment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                tipo_equipo TEXT NOT NULL,
                modelo TEXT,
                serie TEXT,
                marca TEXT,
                potencia TEXT,
                ultimo_servicio DATE,
                frecuencia_meses INTEGER DEFAULT 1,
                proximo_servicio DATE,
                kit_2000 TEXT,
                kit_4000 TEXT,
                kit_6000 TEXT,
                kit_8000 TEXT,
                kit_16000 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
            )
        ''')
        
        # Reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio TEXT UNIQUE NOT NULL,
                fecha DATE NOT NULL,
                cliente TEXT NOT NULL,
                tipo_equipo TEXT NOT NULL,
                modelo TEXT,
                serie TEXT,
                marca TEXT,
                potencia TEXT,
                tipo_servicio TEXT NOT NULL,
                descripcion_servicio TEXT,
                tecnico TEXT NOT NULL,
                localidad TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Folios table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS folios (
                prefijo TEXT PRIMARY KEY,
                ultimo_numero INTEGER DEFAULT 0
            )
        ''')
        
        # Draft reports table - stores complete drafts with images and signatures
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS draft_reports (
                folio TEXT PRIMARY KEY,
                form_data TEXT NOT NULL,
                foto1_data TEXT,
                foto2_data TEXT,
                foto3_data TEXT,
                foto4_data TEXT,
                firma_tecnico_data TEXT,
                firma_cliente_data TEXT,
                pdf_preview BLOB,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Service timer table - tracks timer start/stop for service deals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_service_timer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                tecnico_inicio_id INTEGER NOT NULL,
                tecnico_fin_id INTEGER,
                fecha_inicio TIMESTAMP NOT NULL,
                fecha_fin TIMESTAMP,
                tiempo_segundos INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals(id) ON DELETE CASCADE,
                FOREIGN KEY (tecnico_inicio_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (tecnico_fin_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')
        
        # Almacen (Inventory) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS almacen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_parte TEXT NOT NULL UNIQUE,
                descripcion TEXT NOT NULL,
                unidad TEXT,
                cantidad INTEGER DEFAULT 0,
                ubicacion TEXT,
                ubicacion_especifica TEXT,
                detalles_importacion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Almacen Reservas (Apartados) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS almacen_reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                refaccion_id INTEGER NOT NULL,
                cliente_id INTEGER,
                cliente_nombre TEXT,
                orden_compra TEXT,
                cantidad INTEGER DEFAULT 0,
                fecha_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active', -- active, fulfilled, cancelled
                FOREIGN KEY (refaccion_id) REFERENCES almacen (id) ON DELETE CASCADE,
                FOREIGN KEY (cliente_id) REFERENCES clients (id) ON DELETE SET NULL
            )
        ''')
        
        # Inventory Movements (Kardex) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                remision_id INTEGER,
                refaccion_id INTEGER NOT NULL,
                numero_parte TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                tipo TEXT NOT NULL, -- 'salida', 'entrada'
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER,
                notas TEXT,
                FOREIGN KEY (invoice_id) REFERENCES facturas (id) ON DELETE SET NULL,
                FOREIGN KEY (remision_id) REFERENCES remisiones (id) ON DELETE SET NULL,
                FOREIGN KEY (refaccion_id) REFERENCES almacen (id) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES users (id) ON DELETE SET NULL
            )
        ''')
        
        # Remisiones (Delivery/Remission) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remisiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio TEXT UNIQUE NOT NULL,
                cliente_id INTEGER,
                cliente_nombre TEXT NOT NULL,
                fecha DATE NOT NULL,
                estado TEXT DEFAULT 'draft', -- 'draft', 'confirmed', 'cancelled'
                factura_id INTEGER,
                cotizacion_id INTEGER,
                trato_id INTEGER,
                oc_cliente_id TEXT,
                notas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (cliente_id) REFERENCES clients (id) ON DELETE SET NULL,
                FOREIGN KEY (factura_id) REFERENCES facturas (id) ON DELETE SET NULL,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones (id) ON DELETE SET NULL,
                FOREIGN KEY (trato_id) REFERENCES crm_deals (id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
            )
        ''')
        
        # Remision Items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remision_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remision_id INTEGER NOT NULL,
                refaccion_id INTEGER,
                numero_parte TEXT,
                descripcion TEXT NOT NULL,
                cantidad REAL DEFAULT 1,
                unidad TEXT DEFAULT 'PZA',
                orden INTEGER DEFAULT 0,
                FOREIGN KEY (remision_id) REFERENCES remisiones (id) ON DELETE CASCADE,
                FOREIGN KEY (refaccion_id) REFERENCES almacen (id) ON DELETE SET NULL
            )
        ''')

        # Proveedores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_empresa TEXT NOT NULL,
                contacto_nombre TEXT,
                telefono TEXT,
                email TEXT,
                direccion TEXT,
                rfc TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Compras (Purchase Orders) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio TEXT UNIQUE NOT NULL,
                proveedor_id INTEGER,
                fecha_emision DATE NOT NULL,
                fecha_entrega_estimada DATE,
                estado TEXT DEFAULT 'Borrador',
                moneda TEXT DEFAULT 'MXN',
                subtotal REAL DEFAULT 0,
                iva REAL DEFAULT 0,
                total REAL DEFAULT 0,
                notas TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores (id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
            )
        ''')

        # Compra Items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compra_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id INTEGER NOT NULL,
                linea INTEGER,
                numero_parte TEXT,
                descripcion TEXT,
                cantidad REAL DEFAULT 0,
                unidad TEXT,
                precio_unitario REAL DEFAULT 0,
                importe REAL DEFAULT 0,
                FOREIGN KEY (compra_id) REFERENCES compras (id) ON DELETE CASCADE
            )
        ''')

        # Puestos table - stores all available puestos (positions)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS puestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                permisos TEXT DEFAULT 'formulario',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize default puestos if table is empty
        cursor.execute("SELECT COUNT(*) FROM puestos")
        if cursor.fetchone()[0] == 0:
            default_puestos = [
                ('Administrador', 'clientes,usuarios,historial,equipos,formulario,almacen,cotizaciones,crm,finanzas'),
                ('Técnico de Servicio', 'formulario,historial'),
                ('Vendedor', 'clientes,cotizaciones,crm'),
                ('Gerente de Ventas', 'clientes,cotizaciones,crm,historial'),
                ('Gerente de Servicios Técnicos', 'equipos,historial,crm'),
                ('Cotizador', 'cotizaciones,clientes,crm'),
                ('Almacenista', 'almacen'),
                ('Contador', 'cotizaciones,historial,finanzas,crm'),
                ('Recursos Humanos', 'usuarios'),
                ('Director', 'clientes,usuarios,historial,equipos,almacen,cotizaciones,crm,finanzas'),
            ]
            cursor.executemany('''
                INSERT INTO puestos (nombre, permisos) VALUES (?, ?)
            ''', default_puestos)
        
        # Facturas table - invoices linked to cotizaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_factura TEXT UNIQUE NOT NULL,
                fecha_emision DATE NOT NULL,
                cliente_id INTEGER,
                cliente_nombre TEXT NOT NULL,
                cliente_rfc TEXT,
                cotizacion_id INTEGER,
                subtotal REAL DEFAULT 0,
                iva_porcentaje REAL DEFAULT 16,
                iva_monto REAL DEFAULT 0,
                total REAL DEFAULT 0,
                moneda TEXT DEFAULT 'MXN',
                tipo_cambio REAL DEFAULT 1,
                estado_pago TEXT DEFAULT 'Pendiente',
                fecha_vencimiento DATE,
                metodo_pago TEXT,
                notas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clients (id) ON DELETE SET NULL,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones (id) ON DELETE SET NULL
            )
        ''')
        
        # Pagos table - payment tracking for invoices
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pagos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factura_id INTEGER NOT NULL,
                fecha_pago DATE NOT NULL,
                monto REAL NOT NULL,
                metodo TEXT,
                referencia TEXT,
                notas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (factura_id) REFERENCES facturas (id) ON DELETE CASCADE
            )
        ''')
        
        # Factura Partidas table - invoice line items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS factura_partidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factura_id INTEGER NOT NULL,
                codigo TEXT,
                descripcion TEXT NOT NULL,
                cantidad REAL DEFAULT 1,
                unidad TEXT DEFAULT 'SER',
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                orden INTEGER DEFAULT 0,
                FOREIGN KEY (factura_id) REFERENCES facturas (id) ON DELETE CASCADE
            )
        ''')
        
        # Migration: Add codigo column if it doesn't exist
        try:
            cursor.execute("SELECT codigo FROM factura_partidas LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE factura_partidas ADD COLUMN codigo TEXT")
            except sqlite3.OperationalError:
                pass

        # Migration: Add remision_id to inventory_movements if missing
        try:
            cursor.execute("SELECT remision_id FROM inventory_movements LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE inventory_movements ADD COLUMN remision_id INTEGER")
                print("✅ Added remision_id to inventory_movements")
            except sqlite3.OperationalError:
                pass

        # Migration: Add ocu_id to crm_deals if missing
        try:
            cursor.execute("SELECT ocu_id FROM crm_deals LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE crm_deals ADD COLUMN ocu_id INTEGER")
                print("✅ Added ocu_id to crm_deals")
            except sqlite3.OperationalError:
                pass

        # Migration: Add ocu_id to almacen_reservas if missing
        try:
            cursor.execute("SELECT ocu_id FROM almacen_reservas LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE almacen_reservas ADD COLUMN ocu_id INTEGER")
                print("✅ Added ocu_id to almacen_reservas")
            except sqlite3.OperationalError:
                pass
        
        # Migration: Add ocu_id to notifications if missing
        try:
            cursor.execute("SELECT ocu_id FROM notifications LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE notifications ADD COLUMN ocu_id INTEGER")
                print("✅ Added ocu_id to notifications")
            except sqlite3.OperationalError:
                pass
        
        # Migration: Add oc_cliente_file_path to crm_deals if missing
        try:
            cursor.execute("SELECT oc_cliente_file_path FROM crm_deals LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE crm_deals ADD COLUMN oc_cliente_file_path TEXT")
                print("✅ Added oc_cliente_file_path to crm_deals")
            except sqlite3.OperationalError:
                pass
        
        # Migration: Add folio to crm_deals if missing
        try:
            cursor.execute("SELECT folio FROM crm_deals LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE crm_deals ADD COLUMN folio TEXT")
                print("✅ Added folio to crm_deals")
            except sqlite3.OperationalError:
                pass

        # Create OC Cliente table (customer PO)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oc_cliente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio_cliente TEXT,
                cliente_id INTEGER,
                cliente_nombre TEXT,
                notas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(folio_cliente, cliente_id)
            )
        ''')

        # Create Orden de Cumplimiento (OCu) master table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ocu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oc_cliente_id INTEGER,
                cliente_id INTEGER,
                cliente_nombre TEXT,
                estado TEXT DEFAULT 'open', -- open, ready_to_invoice, partial_waiting_purchase, waiting_purchase, cancelled
                notas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (oc_cliente_id) REFERENCES oc_cliente (id) ON DELETE SET NULL,
                FOREIGN KEY (cliente_id) REFERENCES clients (id) ON DELETE SET NULL
            )
        ''')

        # OCu items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ocu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ocu_id INTEGER NOT NULL,
                numero_parte TEXT,
                descripcion TEXT,
                unidad TEXT,
                cantidad REAL DEFAULT 0,
                reservado REAL DEFAULT 0,
                faltante REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ocu_id) REFERENCES ocu (id) ON DELETE CASCADE
            )
        ''')

        # Purchase requisitions table (if not exists)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_requisitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ocu_id INTEGER,
                cliente_id INTEGER,
                cliente_nombre TEXT,
                folio_ocu TEXT,
                numero_parte TEXT,
                descripcion TEXT,
                cantidad REAL DEFAULT 0,
                status TEXT DEFAULT 'open', -- open, ordered, received, cancelled
                notas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ocu_id) REFERENCES ocu (id) ON DELETE CASCADE
            )
        ''')
        if not column_exists('purchase_requisitions', 'cliente_id'):
            try:
                cursor.execute("ALTER TABLE purchase_requisitions ADD COLUMN cliente_id INTEGER")
            except sqlite3.OperationalError:
                pass
        if not column_exists('purchase_requisitions', 'cliente_nombre'):
            try:
                cursor.execute("ALTER TABLE purchase_requisitions ADD COLUMN cliente_nombre TEXT")
            except sqlite3.OperationalError:
                pass
        if not column_exists('purchase_requisitions', 'folio_ocu'):
            try:
                cursor.execute("ALTER TABLE purchase_requisitions ADD COLUMN folio_ocu TEXT")
            except sqlite3.OperationalError:
                pass
        if not column_exists('purchase_requisitions', 'descripcion'):
            try:
                cursor.execute("ALTER TABLE purchase_requisitions ADD COLUMN descripcion TEXT")
            except sqlite3.OperationalError:
                pass

        # Finance requests table (solicitud de factura)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finance_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ocu_id INTEGER,
                cliente_id INTEGER,
                cliente_nombre TEXT,
                folio_ocu TEXT,
                status TEXT DEFAULT 'pending', -- pending, in_progress, done, cancelled
                notas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ocu_id) REFERENCES ocu (id) ON DELETE CASCADE
            )
        ''')
        if not column_exists('finance_requests', 'cliente_id'):
            try:
                cursor.execute("ALTER TABLE finance_requests ADD COLUMN cliente_id INTEGER")
            except sqlite3.OperationalError:
                pass
        if not column_exists('finance_requests', 'cliente_nombre'):
            try:
                cursor.execute("ALTER TABLE finance_requests ADD COLUMN cliente_nombre TEXT")
            except sqlite3.OperationalError:
                pass
        if not column_exists('finance_requests', 'folio_ocu'):
            try:
                cursor.execute("ALTER TABLE finance_requests ADD COLUMN folio_ocu TEXT")
            except sqlite3.OperationalError:
                pass

        # Migration: Add ocu_id to facturas if missing
        if not column_exists('facturas', 'ocu_id'):
            try:
                cursor.execute("ALTER TABLE facturas ADD COLUMN ocu_id INTEGER")
            except sqlite3.OperationalError:
                pass
        
        # Migration: Add unidad column if it doesn't exist
        try:
            cursor.execute("SELECT unidad FROM factura_partidas LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE factura_partidas ADD COLUMN unidad TEXT DEFAULT 'SER'")
            except sqlite3.OperationalError:
                pass
        
        # Migration: Add fiscal fields to facturas
        try:
            cursor.execute("SELECT uso_cfdi FROM facturas LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE facturas ADD COLUMN uso_cfdi TEXT DEFAULT 'G03'")
            except sqlite3.OperationalError:
                pass
        
        try:
            cursor.execute("SELECT condiciones_pago FROM facturas LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE facturas ADD COLUMN condiciones_pago TEXT DEFAULT '30 días'")
            except sqlite3.OperationalError:
                pass
        
        try:
            cursor.execute("SELECT forma_pago FROM facturas LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE facturas ADD COLUMN forma_pago TEXT DEFAULT '99'")
            except sqlite3.OperationalError:
                pass
        
        # Migration: Update Contador permissions to include CRM
        try:
            cursor.execute('''
                UPDATE puestos 
                SET permisos = 'cotizaciones,historial,finanzas,crm'
                WHERE nombre = 'Contador' AND permisos NOT LIKE '%crm%'
            ''')
        except sqlite3.OperationalError:
            pass
        
        # Gastos table - expenses and egresos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                categoria TEXT NOT NULL,
                concepto TEXT NOT NULL,
                monto REAL NOT NULL,
                proveedor TEXT,
                metodo_pago TEXT,
                referencia TEXT,
                notas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cuentas por pagar table - accounts payable
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cuentas_por_pagar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_emision DATE NOT NULL,
                proveedor TEXT NOT NULL,
                concepto TEXT NOT NULL,
                monto_total REAL NOT NULL,
                monto_pagado REAL DEFAULT 0,
                estado TEXT DEFAULT 'Pendiente',
                fecha_vencimiento DATE,
                notas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # CRM Puesto Stages table - stores which stages each puesto can see
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_puesto_stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                puesto TEXT NOT NULL,
                stage_name TEXT NOT NULL,
                orden INTEGER DEFAULT 0,
                color TEXT DEFAULT '#6c757d',
                UNIQUE(puesto, stage_name)
            )
        ''')
        
        # CRM Stage Triggers table - defines automatic transitions between puestos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_stage_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_puesto TEXT NOT NULL,
                source_stage TEXT NOT NULL,
                target_puesto TEXT NOT NULL,
                target_stage TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Initialize default puesto stages if table is empty
        cursor.execute("SELECT COUNT(*) FROM crm_puesto_stages")
        if cursor.fetchone()[0] == 0:
            default_stages = [
                # Vendedor stages (original CRM stages)
                ('Vendedor', 'Prospecto', 0, '#17a2b8'),
                ('Vendedor', 'Contacto Inicial', 1, '#6c757d'),
                ('Vendedor', 'Solicitud de Cotización', 2, '#ffc107'),
                ('Vendedor', 'Cotización Lista para Enviar', 3, '#007bff'),
                ('Vendedor', 'Negociación', 4, '#fd7e14'),
                ('Vendedor', 'Ganado', 5, '#28a745'),
                ('Vendedor', 'Pedido', 6, '#6f42c1'),
                ('Vendedor', 'Solicitud de Factura', 7, '#dc3545'),
                # Cotizador stages
                ('Cotizador', 'Pendiente por Cotizar', 0, '#ffc107'),
                ('Cotizador', 'Cotizado', 1, '#28a745'),
                # Gerente de Servicios Técnicos stages
                ('Gerente de Servicios Técnicos', 'Programado', 0, '#17a2b8'),
                ('Gerente de Servicios Técnicos', 'Realizado', 1, '#28a745'),
                ('Gerente de Servicios Técnicos', 'Requiere Cotización', 2, '#ffc107'),
                ('Gerente de Servicios Técnicos', 'Cotizado', 3, '#007bff'),
                # Contador/Finanzas stages - CRM para proceso de facturación y cobro
                ('Contador', 'Solicitud de Factura', 0, '#ffc107'),
                ('Contador', 'En Proceso', 1, '#17a2b8'),
                ('Contador', 'Facturado', 2, '#007bff'),
                ('Contador', 'Enviado al Cliente', 3, '#6f42c1'),
                ('Contador', 'Por Cobrar', 4, '#fd7e14'),
                ('Contador', 'Pago Parcial', 5, '#e83e8c'),
                ('Contador', 'Pagado', 6, '#28a745'),
                ('Contador', 'Vencido', 7, '#dc3545'),
                ('Contador', 'En Cobranza', 8, '#c82333'),
                ('Contador', 'Cancelado', 9, '#6c757d'),
            ]
            cursor.executemany('''
                INSERT INTO crm_puesto_stages (puesto, stage_name, orden, color)
                VALUES (?, ?, ?, ?)
            ''', default_stages)
            
            # Initialize default triggers
            default_triggers = [
                # Vendedor "Solicitud de Cotización" -> Cotizador "Pendiente por Cotizar"
                ('Vendedor', 'Solicitud de Cotización', 'Cotizador', 'Pendiente por Cotizar'),
                # Cotizador "Cotizado" -> Vendedor "Cotización Lista para Enviar"
                ('Cotizador', 'Cotizado', 'Vendedor', 'Cotización Lista para Enviar'),
                # Ger. Servicios "Requiere Cotización" -> Cotizador "Pendiente por Cotizar"
                ('Gerente de Servicios Técnicos', 'Requiere Cotización', 'Cotizador', 'Pendiente por Cotizar'),
                # Vendedor "Solicitud de Factura" -> Contador "Solicitud de Factura"
                ('Vendedor', 'Solicitud de Factura', 'Contador', 'Solicitud de Factura'),
            ]
            cursor.executemany('''
                INSERT INTO crm_stage_triggers (source_puesto, source_stage, target_puesto, target_stage)
                VALUES (?, ?, ?, ?)
            ''', default_triggers)

        # Migration: Rename "Cotización Enviada" to "Cotización Lista para Enviar"
        try:
            # Update stage name in crm_puesto_stages
            cursor.execute('''
                UPDATE crm_puesto_stages 
                SET stage_name = 'Cotización Lista para Enviar' 
                WHERE stage_name = 'Cotización Enviada' AND puesto = 'Vendedor'
            ''')
            # Update trigger target stage
            cursor.execute('''
                UPDATE crm_stage_triggers 
                SET target_stage = 'Cotización Lista para Enviar' 
                WHERE target_stage = 'Cotización Enviada'
            ''')
            # Update any existing deals in that stage
            cursor.execute('''
                UPDATE crm_deals 
                SET etapa = 'Cotización Lista para Enviar' 
                WHERE etapa = 'Cotización Enviada'
            ''')
        except sqlite3.OperationalError:
            pass  # Tables might not exist yet

        # Migration: Normalize "Gerente de Servicios Técnicos" (allow both singular and plural)
        try:
            # First, update users table - normalize puesto name
            cursor.execute('''
                UPDATE users 
                SET puesto = 'Gerente de Servicios Técnicos' 
                WHERE (puesto LIKE 'Gerente de Servicio Técnico%' 
                OR puesto LIKE 'GERENTE DE SERVICIO TÉCNICO%'
                OR puesto LIKE 'Gerente de Servicio Tecnico%')
                AND puesto != 'Gerente de Servicios Técnicos'
            ''')
            
            # For puestos table: simply delete all variants that are not the correct one
            # The correct one already exists from default_puestos
            cursor.execute('''
                DELETE FROM puestos 
                WHERE (nombre LIKE 'Gerente de Servicio Técnico%'
                OR nombre LIKE 'GERENTE DE SERVICIO TÉCNICO%'
                OR nombre LIKE 'Gerente de Servicio Tecnico%')
                AND nombre != 'Gerente de Servicios Técnicos'
            ''')
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            pass  # Tables might not exist yet or constraint error

        # Migration: Add finanzas permission to existing puestos
        try:
            cursor.execute('''
                UPDATE puestos 
                SET permisos = permisos || ',finanzas'
                WHERE nombre IN ('Administrador', 'Contador', 'Director')
                AND permisos NOT LIKE '%finanzas%'
            ''')
        except sqlite3.OperationalError:
            pass  # Table might not exist yet

        # Check if ubicacion_especifica exists in almacen (migration)
        try:
            cursor.execute("SELECT ubicacion_especifica FROM almacen LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("ALTER TABLE almacen ADD COLUMN ubicacion_especifica TEXT")
            except sqlite3.OperationalError:
                pass
        
        # Check if new columns exist (for migration)
        try:
            cursor.execute("SELECT ultimo_servicio FROM client_equipment LIMIT 1")
        except sqlite3.OperationalError:
            # Columns don't exist, add them
            alter_commands = [
                "ALTER TABLE client_equipment ADD COLUMN ultimo_servicio DATE",
                "ALTER TABLE client_equipment ADD COLUMN frecuencia_meses INTEGER DEFAULT 1",
                "ALTER TABLE client_equipment ADD COLUMN proximo_servicio DATE",
                "ALTER TABLE client_equipment ADD COLUMN kit_2000 TEXT",
                "ALTER TABLE client_equipment ADD COLUMN kit_4000 TEXT",
                "ALTER TABLE client_equipment ADD COLUMN kit_6000 TEXT",
                "ALTER TABLE client_equipment ADD COLUMN kit_8000 TEXT",
                "ALTER TABLE client_equipment ADD COLUMN kit_16000 TEXT"
            ]
            for cmd in alter_commands:
                try:
                    cursor.execute(cmd)
                except sqlite3.OperationalError:
                    pass 
        
        # ==================== FASE 1: MENSAJES INTERNOS Y NOTIFICACIONES ====================
        
        # Deal Messages table - internal messages within deals (mentions @usuario)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deal_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                mensaje TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Attachments table - for email replies and internal messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_type TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                mime_type TEXT,
                size INTEGER,
                file_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_attachments_owner 
            ON attachments(owner_type, owner_id)
        ''')
        
        # Notifications table - notifications for mentioned users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                mensaje TEXT,
                deal_id INTEGER,
                deal_message_id INTEGER,
                leido INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (deal_id) REFERENCES crm_deals (id) ON DELETE CASCADE,
                FOREIGN KEY (deal_message_id) REFERENCES deal_messages (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== FASE 2: EMAIL HISTORY ====================
        
        # Email History table - track all emails sent/received with clients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER,
                direccion TEXT NOT NULL,
                tipo TEXT NOT NULL,
                asunto TEXT NOT NULL,
                cuerpo TEXT,
                remitente TEXT,
                destinatario TEXT,
                cc TEXT,
                thread_id TEXT,
                message_id TEXT,
                adjuntos TEXT,
                cotizacion_id INTEGER,
                estado TEXT DEFAULT 'enviado',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals (id) ON DELETE SET NULL,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones (id) ON DELETE SET NULL
            )
        ''')
        
        # Add new columns to email_history if they don't exist (SQLite-safe with PRAGMA)
        def column_exists(table, column):
            cursor.execute(f"PRAGMA table_info({table})")
            return any(row['name'] == column for row in cursor.fetchall())
        
        columns_to_add = [
            ('cc', 'TEXT'),
            ('thread_id', 'TEXT'),
            ('message_id', 'TEXT'),
            ('in_reply_to', 'TEXT'),
            ('references', 'TEXT'),
            ('subject_raw', 'TEXT'),
            ('subject_norm', 'TEXT'),
            ('thread_root_id', 'TEXT'),
            ('direction', 'TEXT'),
            ('provider', 'TEXT')
        ]
        
        for col_name, col_type in columns_to_add:
            if not column_exists('email_history', col_name):
                try:
                    # Escapar palabra reservada 'references' con comillas dobles
                    if col_name == 'references':
                        cursor.execute(f'ALTER TABLE email_history ADD COLUMN "{col_name}" {col_type}')
                    else:
                        cursor.execute(f'ALTER TABLE email_history ADD COLUMN {col_name} {col_type}')
                    conn.commit()  # CRÍTICO: Hacer commit después de cada ALTER TABLE
                    print(f"✅ Columna {col_name} agregada a email_history")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ Error agregando columna {col_name}: {e}")
        
        # Crear índice único para message_id si no existe (para deduplicación)
        try:
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_email_message_id ON email_history(message_id) WHERE message_id IS NOT NULL')
        except:
            pass

        conn.commit()
        
        # Create default users if none exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("No users found. Creating default users...")
            
            # Create default admin
            cursor.execute('''
                INSERT INTO users (username, password, role, nombre, prefijo)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', 'admin123', 'admin', 'Administrador', 'ADM'))
            
            # Create default technicians
            default_techs = [
                ('fernando', 'fernando123', 'technician', 'Fernando', 'F'),
                ('cesar', 'cesar123', 'technician', 'César', 'C'),
                ('hiorvard', 'hiorvard123', 'technician', 'Hiorvard', 'H')
            ]
            
            for username, password, role, nombre, prefijo in default_techs:
                cursor.execute('''
                    INSERT INTO users (username, password, role, nombre, prefijo)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password, role, nombre, prefijo))
            
            conn.commit()
            print("Default users created:")
            print("  - admin / admin123 (Administrator)")
            print("  - fernando / fernando123 (Technician)")
            print("  - cesar / cesar123 (Technician)")
            print("  - hiorvard / hiorvard123 (Technician)")
        
        # Run migrations
        run_migrations()

# ==================== MIGRATIONS ====================
def run_migrations():
    """Run database migrations for schema updates"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Migration: Generate folios for existing deals that don't have one
        # Skip this migration if database is locked (will retry on next startup)
        try:
            cursor.execute('''
                SELECT id, tipo_deal FROM crm_deals WHERE folio IS NULL OR folio = ''
            ''')
            deals_without_folio = cursor.fetchall()
            
            if deals_without_folio:
                for deal_row in deals_without_folio:
                    deal_id = deal_row[0]
                    tipo_deal = deal_row[1] or 'venta'
                    try:
                        folio = get_next_deal_folio(tipo_deal)
                        cursor.execute('UPDATE crm_deals SET folio = ? WHERE id = ?', (folio, deal_id))
                    except Exception as e:
                        print(f"⚠️ Error generating folio for deal {deal_id}: {e}")
                        continue
                
                conn.commit()
                print(f"✅ Generated folios for {len(deals_without_folio)} existing deals")
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                print(f"⚠️ Database locked, skipping folio generation. Will retry on next startup.")
            else:
                print(f"⚠️ Error generating folios for existing deals: {e}")
        except Exception as e:
            print(f"⚠️ Error generating folios for existing deals: {e}")
        
        # Migration: Add email, firma_vendedor, mensaje_envio to crm_deals
        try:
            cursor.execute("ALTER TABLE crm_deals ADD COLUMN email TEXT")
            print("✅ Added 'email' column to crm_deals")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute("ALTER TABLE crm_deals ADD COLUMN firma_vendedor TEXT")
            print("✅ Added 'firma_vendedor' column to crm_deals")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE crm_deals ADD COLUMN mensaje_envio TEXT")
            print("✅ Added 'mensaje_envio' column to crm_deals")
        except sqlite3.OperationalError:
            pass
        
        # Add auto_send_email toggle (1 = ON, 0 = OFF, default 1)
        try:
            cursor.execute("ALTER TABLE crm_deals ADD COLUMN auto_send_email INTEGER DEFAULT 1")
            print("✅ Added 'auto_send_email' column to crm_deals")
        except sqlite3.OperationalError:
            pass
        
        # Add first_quote_email_sent tracking columns
        try:
            cursor.execute("ALTER TABLE crm_deals ADD COLUMN first_quote_email_sent INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE crm_deals ADD COLUMN first_quote_email_sent_at TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE crm_deals ADD COLUMN first_quote_email_sent_method TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Add email_provider to users (outlook, gmail, other)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email_provider TEXT")
            print("✅ Added 'email_provider' column to users")
        except sqlite3.OperationalError:
            pass
        
        # Migration: Add SMTP credentials to users table
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email_smtp TEXT")
            print("✅ Added 'email_smtp' column to users")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password_smtp TEXT")
            print("✅ Added 'password_smtp' column to users")
        except sqlite3.OperationalError:
            pass
        
        # Migration: Add email signature to users table
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN firma_email TEXT")
            print("✅ Added 'firma_email' column to users")
        except sqlite3.OperationalError:
            pass
        
        # Migration: Add signature image (base64) to users table
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN firma_imagen TEXT")
            print("✅ Added 'firma_imagen' column to users")
        except sqlite3.OperationalError:
            pass
        
        # ==================== EMAIL TEMPLATES AND MODULE MESSAGES ====================
        # Create email_templates table (templates por módulo)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL,
                template_type TEXT NOT NULL,
                default_content TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(module, template_type)
            )
        ''')
        
        # Create first_email_drafts table (primer correo de cotización)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS first_email_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL UNIQUE,
                to_email TEXT NOT NULL,
                cc TEXT,
                subject TEXT,
                body TEXT,
                auto_send_email INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals (id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_first_email_drafts_deal_id ON first_email_drafts(deal_id)')
        print("✅ Tabla first_email_drafts creada/verificada")
        
        # Create email_log table (trazabilidad de correos enviados)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                cotizacion_id INTEGER,
                tipo TEXT DEFAULT 'primer_correo',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                direction TEXT NOT NULL DEFAULT 'sent',
                to_email TEXT NOT NULL,
                cc TEXT,
                subject TEXT,
                body TEXT,
                message_id TEXT,
                message_hash TEXT,
                status TEXT DEFAULT 'sent',
                error TEXT,
                FOREIGN KEY (deal_id) REFERENCES crm_deals (id) ON DELETE CASCADE,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones (id) ON DELETE SET NULL
            )
        ''')
        
        # Add columns if they don't exist (migration) - MUST BE BEFORE INDEXES
        try:
            cursor.execute("ALTER TABLE email_log ADD COLUMN cotizacion_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE email_log ADD COLUMN tipo TEXT DEFAULT 'primer_correo'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE email_log ADD COLUMN message_hash TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Create indexes AFTER migrations
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_log_deal_id ON email_log(deal_id)')
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_log_cotizacion_id ON email_log(cotizacion_id)')
        except sqlite3.OperationalError:
            pass  # Column might not exist yet
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_log_tipo ON email_log(tipo)')
        except sqlite3.OperationalError:
            pass  # Column might not exist yet
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_log_message_hash ON email_log(message_hash)')
        except sqlite3.OperationalError:
            pass  # Column might not exist yet
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_log_created_at ON email_log(created_at)')
        
        print("✅ Tabla email_log creada/verificada")
        
        # Create deal_email_messages table (mensajes personalizados por trato + módulo)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deal_email_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                module TEXT NOT NULL,
                mensaje TEXT,
                firma TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals (id) ON DELETE CASCADE,
                UNIQUE(deal_id, module)
            )
        ''')
        
        # Add module and tipo_documento columns to email_history (opcional, para filtrado)
        try:
            cursor.execute("ALTER TABLE email_history ADD COLUMN module TEXT")
            print("✅ Added 'module' column to email_history")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE email_history ADD COLUMN tipo_documento TEXT")
            print("✅ Added 'tipo_documento' column to email_history")
        except sqlite3.OperationalError:
            pass
        
        # Email drafts table (borradores de correos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                tipo_documento TEXT NOT NULL,  -- 'cotizacion', 'factura', 'pi', etc.
                documento_id INTEGER,  -- ID de la cotización/factura/PI
                mensaje TEXT,
                asunto TEXT,
                adjuntos TEXT,  -- JSON array de archivos adjuntos
                created_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals (id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
            )
        ''')
        print("✅ Tabla email_drafts creada/verificada")
        
        # Initialize default templates if they don't exist
        default_templates = [
            # Ventas
            ('ventas', 'mensaje', 'Hola, buen día\n\nAdjunto encontrará la cotización solicitada.\n\nQuedamos a sus órdenes para cualquier duda o aclaración.', 'Mensaje por defecto para envío de cotizaciones (Ventas)'),
            ('ventas', 'firma', 'Saludos cordiales,', 'Firma por defecto para Ventas'),
            # Finanzas
            ('finanzas', 'mensaje', 'Estimado cliente,\n\nAdjunto encontrará la factura correspondiente.\n\nAgradecemos su preferencia.', 'Mensaje por defecto para envío de facturas (Finanzas)'),
            ('finanzas', 'firma', 'Saludos cordiales,\n\nDepartamento de Finanzas', 'Firma por defecto para Finanzas'),
            # Compras
            ('compras', 'mensaje', 'Buen día,\n\nAdjunto encontrará la orden de compra correspondiente.\n\nQuedamos a sus órdenes.', 'Mensaje por defecto para envío de órdenes de compra'),
            ('compras', 'firma', 'Saludos cordiales,\n\nDepartamento de Compras', 'Firma por defecto para Compras'),
            # Servicios
            ('servicios', 'mensaje', 'Estimado cliente,\n\nAdjunto encontrará el reporte de servicio técnico.\n\nQuedamos a sus órdenes para cualquier aclaración.', 'Mensaje por defecto para envío de reportes de servicio'),
            ('servicios', 'firma', 'Saludos cordiales,\n\nDepartamento de Servicios Técnicos', 'Firma por defecto para Servicios'),
            # Cotización
            ('cotizacion', 'mensaje', 'Hola, buen día\n\nAdjunto encontrará la cotización solicitada.\n\nQuedamos a sus órdenes para cualquier duda o aclaración.', 'Mensaje por defecto para Cotizador'),
            ('cotizacion', 'firma', 'Saludos cordiales,', 'Firma por defecto para Cotizador'),
        ]
        
        for module, template_type, content, description in default_templates:
            cursor.execute('''
                INSERT OR IGNORE INTO email_templates (module, template_type, default_content, description)
                VALUES (?, ?, ?, ?)
            ''', (module, template_type, content, description))
        
        print("✅ Email templates tables created and initialized")
        
        # Migrate existing messages from crm_deals to deal_email_messages
        try:
            cursor.execute('''
                SELECT id, firma_vendedor, mensaje_envio 
                FROM crm_deals 
                WHERE firma_vendedor IS NOT NULL OR mensaje_envio IS NOT NULL
            ''')
            existing_deals = cursor.fetchall()
            
            migrated_count = 0
            for deal_row in existing_deals:
                deal_id = deal_row[0]
                firma = deal_row[1]
                mensaje = deal_row[2]
                
                # Check if already migrated
                cursor.execute('''
                    SELECT id FROM deal_email_messages 
                    WHERE deal_id = ? AND module = 'ventas'
                ''', (deal_id,))
                if cursor.fetchone():
                    continue  # Already migrated
                
                # Migrate to deal_email_messages with module='ventas'
                cursor.execute('''
                    INSERT INTO deal_email_messages (deal_id, module, mensaje, firma)
                    VALUES (?, 'ventas', ?, ?)
                ''', (deal_id, mensaje, firma))
                migrated_count += 1
            
            if migrated_count > 0:
                print(f"✅ Migrated {migrated_count} existing messages to deal_email_messages (module='ventas')")
        except Exception as e:
            print(f"⚠️ Error during migration: {e}")
        
        # ========== CRM EMAIL LOG TABLES ==========
        # Create crm_email_messages table (Email Log por Trato)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_email_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('inbound', 'outbound')),
                from_email TEXT NOT NULL,
                to_emails TEXT,
                cc_emails TEXT,
                subject_raw TEXT,
                subject_norm TEXT,
                message_id TEXT,
                in_reply_to TEXT,
                references_header TEXT,
                thread_key TEXT,
                date_ts TIMESTAMP NOT NULL,
                snippet TEXT,
                body_html TEXT,
                body_text TEXT,
                provider_uid TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES crm_deals (id) ON DELETE CASCADE
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crm_email_deal_id ON crm_email_messages(deal_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crm_email_thread_key ON crm_email_messages(thread_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crm_email_message_id ON crm_email_messages(message_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crm_email_date_ts ON crm_email_messages(date_ts)')
        
        # Create crm_email_attachments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_email_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                mime TEXT,
                size INTEGER,
                storage_path TEXT,
                hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES crm_email_messages (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crm_email_attachments_email_id ON crm_email_attachments(email_id)')
        
        print("✅ CRM Email Log tables created")
        
        conn.commit()

# ========== User Functions ==========

def get_all_users():
    """Get all users"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY role, username")
        return [dict(row) for row in cursor.fetchall()]

def get_user_by_username(username):
    """Get user by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id):
    """Get user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_user(username, password, nombre, prefijo, role='technician', puesto=None, telefono=None, email=None, email_smtp=None, password_smtp=None, firma_email=None, firma_imagen=None):
    """Create a new user"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, nombre, prefijo, role, puesto, telefono, email, email_smtp, password_smtp, firma_email, firma_imagen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, nombre, prefijo, role, puesto, telefono, email, email_smtp, password_smtp, firma_email, firma_imagen))
            return True
    except sqlite3.IntegrityError:
        return False

def update_user(user_id, data):
    """Update an existing user"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Build update query dynamically based on provided data
        fields = []
        values = []
        
        if 'nombre' in data:
            fields.append('nombre=?')
            values.append(data['nombre'])
        if 'prefijo' in data:
            fields.append('prefijo=?')
            values.append(data['prefijo'])
        if 'role' in data:
            fields.append('role=?')
            values.append(data['role'])
        if 'puesto' in data:
            fields.append('puesto=?')
            values.append(data['puesto'])
        if 'telefono' in data:
            fields.append('telefono=?')
            values.append(data['telefono'])
        if 'email' in data:
            fields.append('email=?')
            values.append(data['email'])
        if 'email_smtp' in data:
            fields.append('email_smtp=?')
            values.append(data['email_smtp'])
        if 'password_smtp' in data:
            fields.append('password_smtp=?')
            values.append(data['password_smtp'])
        if 'firma_email' in data:
            fields.append('firma_email=?')
            values.append(data['firma_email'])
        if 'firma_imagen' in data:
            fields.append('firma_imagen=?')
            values.append(data['firma_imagen'])
        if 'password' in data and data['password']:
            fields.append('password=?')
            values.append(data['password'])
        
        if fields:
            values.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", values)
            return cursor.rowcount > 0
        return False

def delete_user(user_id):
    """Delete a user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0

# ========== Client Functions ==========

def get_all_clients():
    """Get all clients from database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients ORDER BY nombre")
        return [dict(row) for row in cursor.fetchall()]

def get_client_by_id(client_id):
    """Get client by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_client(nombre, contacto='', telefono='', email='', direccion='', rfc='', vendedor_nombre='', vendedor_email='', vendedor_telefono=''):
    """Create a new client"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clients (nombre, contacto, telefono, email, direccion, rfc, vendedor_nombre, vendedor_email, vendedor_telefono)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nombre, contacto, telefono, email, direccion, rfc, vendedor_nombre, vendedor_email, vendedor_telefono))
        return cursor.lastrowid

def update_client(client_id, nombre, contacto='', telefono='', email='', direccion='', rfc='', vendedor_nombre='', vendedor_email='', vendedor_telefono=''):
    """Update client information"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE clients
            SET nombre = ?, contacto = ?, telefono = ?, email = ?, direccion = ?, rfc = ?, vendedor_nombre = ?, vendedor_email = ?, vendedor_telefono = ?
            WHERE id = ?
        ''', (nombre, contacto, telefono, email, direccion, rfc, vendedor_nombre, vendedor_email, vendedor_telefono, client_id))
        return cursor.rowcount > 0

def delete_client(client_id):
    """Delete a client by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        cursor.execute("DELETE FROM client_contacts WHERE client_id = ?", (client_id,))
        return cursor.rowcount > 0

def add_client_contact(client_id, nombre, email='', telefono='', puesto=''):
    """Add a contact for a client"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO client_contacts (client_id, nombre, email, telefono, puesto)
            VALUES (?, ?, ?, ?, ?)
        ''', (client_id, nombre, email, telefono, puesto))
        return cursor.lastrowid

def get_client_contacts(client_id):
    """Get all contacts for a client"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM client_contacts WHERE client_id = ?", (client_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_client_contacts(client_id):
    """Delete all contacts for a client (used before re-adding)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM client_contacts WHERE client_id = ?", (client_id,))
        return cursor.rowcount

# ========== Report Functions ==========

def save_report(folio, fecha, cliente, tipo_equipo, modelo, serie, marca, potencia,
                tipo_servicio, descripcion_servicio, tecnico, localidad):
    """Save report metadata to database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO reports 
            (folio, fecha, cliente, tipo_equipo, modelo, serie, marca, potencia,
             tipo_servicio, descripcion_servicio, tecnico, localidad)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (folio, fecha, cliente, tipo_equipo, modelo, serie, marca, potencia,
              tipo_servicio, descripcion_servicio, tecnico, localidad))
        return cursor.lastrowid

def get_all_reports():
    """Get all reports from database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_report_by_folio(folio):
    """Get report by folio"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports WHERE folio = ?", (folio,))
        row = cursor.fetchone()
        return dict(row) if row else None

def search_reports(search_term='', tipo_servicio='', fecha_inicio='', fecha_fin=''):
    """Search reports with filters"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM reports WHERE 1=1"
        params = []
        
        if search_term:
            query += " AND (folio LIKE ? OR cliente LIKE ? OR tecnico LIKE ?)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        if tipo_servicio:
            query += " AND tipo_servicio = ?"
            params.append(tipo_servicio)
        
        if fecha_inicio:
            query += " AND fecha >= ?"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND fecha <= ?"
            params.append(fecha_fin)
        
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

# ========== Folio Functions ==========

def get_next_folio(prefijo):
    """Get next folio number for a prefix"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO folios (prefijo, ultimo_numero)
            VALUES (?, 0)
        ''', (prefijo,))
        
        cursor.execute('''
            UPDATE folios
            SET ultimo_numero = ultimo_numero + 1
            WHERE prefijo = ?
        ''', (prefijo,))
        
        cursor.execute("SELECT ultimo_numero FROM folios WHERE prefijo = ?", (prefijo,))
        row = cursor.fetchone()
        numero = row['ultimo_numero'] if row else 1
        
        # Use 5 digits for IA (invoices), 4 for others
        digits = 5 if prefijo == "IA" else 4
        return f"{prefijo}-{numero:0{digits}d}"

def get_next_deal_folio(tipo_deal='venta'):
    """Generate next folio for a deal based on tipo_deal (S-00001 for servicios, V-00001 for ventas)"""
    prefijo = 'S' if tipo_deal == 'servicio' else 'V'
    return get_next_folio(prefijo)

# ========== Statistics Functions ==========

def get_dashboard_stats():
    """Get statistics for admin dashboard"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM clients")
        total_clients = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM reports")
        total_reports = cursor.fetchone()['count']
        
        # Count equipment instead of plans
        cursor.execute("SELECT COUNT(*) as count FROM client_equipment")
        active_plans = cursor.fetchone()['count']
        
        # Count inventory items
        try:
            cursor.execute("SELECT COUNT(*) as count FROM almacen")
            total_refacciones = cursor.fetchone()['count']
        except sqlite3.OperationalError:
            total_refacciones = 0
        
        return {
            'total_clients': total_clients,
            'total_users': total_users,
            'total_reports': total_reports,
            'active_plans': active_plans,
            'total_refacciones': total_refacciones
        }

# ========== Client Equipment Functions ==========

def add_client_equipment(client_id, tipo_equipo, modelo='', serie='', marca='', potencia='', 
                        ultimo_servicio=None, frecuencia_meses=1, proximo_servicio=None,
                        kit_2000=None, kit_4000=None, kit_6000=None, kit_8000=None, kit_16000=None):
    """Add equipment to a client with maintenance info"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO client_equipment 
            (client_id, tipo_equipo, modelo, serie, marca, potencia, 
             ultimo_servicio, frecuencia_meses, proximo_servicio,
             kit_2000, kit_4000, kit_6000, kit_8000, kit_16000)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (client_id, tipo_equipo, modelo, serie, marca, potencia,
              ultimo_servicio, frecuencia_meses, proximo_servicio,
              kit_2000, kit_4000, kit_6000, kit_8000, kit_16000))
        return cursor.lastrowid

def get_client_equipment(client_id):
    """Get all equipment for a client from equipos_calendario"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Query equipos_calendario using cliente_id
        cursor.execute('''
            SELECT 
                id,
                cliente_id,
                serie,
                tipo_equipo,
                modelo,
                marca,
                potencia,
                frecuencia_meses
            FROM equipos_calendario
            WHERE cliente_id = ?
            ORDER BY tipo_equipo, modelo
        ''', (client_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # If no results, fallback to client_equipment
        if not results:
            cursor.execute('''
                SELECT * FROM client_equipment
                WHERE client_id = ?
                ORDER BY tipo_equipo, modelo
            ''', (client_id,))
            results = [dict(row) for row in cursor.fetchall()]
        
        return results

def get_equipment_by_id(equipment_id):
    """Get specific equipment by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM client_equipment
            WHERE id = ?
        ''', (equipment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_client_equipment(equipment_id, tipo_equipo, modelo='', serie='', marca='', potencia='',
                           ultimo_servicio=None, frecuencia_meses=1, proximo_servicio=None,
                           kit_2000=None, kit_4000=None, kit_6000=None, kit_8000=None, kit_16000=None):
    """Update equipment information"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE client_equipment
            SET tipo_equipo = ?, modelo = ?, serie = ?, marca = ?, potencia = ?,
                ultimo_servicio = ?, frecuencia_meses = ?, proximo_servicio = ?,
                kit_2000 = ?, kit_4000 = ?, kit_6000 = ?, kit_8000 = ?, kit_16000 = ?
            WHERE id = ?
        ''', (tipo_equipo, modelo, serie, marca, potencia, 
              ultimo_servicio, frecuencia_meses, proximo_servicio,
              kit_2000, kit_4000, kit_6000, kit_8000, kit_16000,
              equipment_id))
        return cursor.rowcount > 0

def delete_client_equipment(equipment_id):
    """Delete equipment by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM client_equipment WHERE id = ?", (equipment_id,))
        return cursor.rowcount > 0

def get_equipment_types_by_client(client_id):
    """Get unique equipment types for a client"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT tipo_equipo
            FROM client_equipment
            WHERE client_id = ?
            ORDER BY tipo_equipo
        ''', (client_id,))
        return [row['tipo_equipo'] for row in cursor.fetchall()]

def get_models_by_client_and_type(client_id, tipo_equipo):
    """Get equipment models for a specific client and equipment type"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, modelo, serie, marca, potencia
            FROM client_equipment
            WHERE client_id = ? AND tipo_equipo = ?
            ORDER BY modelo
        ''', (client_id, tipo_equipo))
        return [dict(row) for row in cursor.fetchall()]

# ========== Draft Report Functions ==========

def save_draft_report(folio, form_data, foto1=None, foto2=None, foto3=None, foto4=None,
                      firma_tecnico=None, firma_cliente=None, pdf_preview=None, deal_id=None):
    """Save or update draft report with all data including images as Base64"""
    import json
    from datetime import datetime
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if draft exists
        cursor.execute("SELECT folio FROM draft_reports WHERE folio = ?", (folio,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing draft
            cursor.execute('''
                UPDATE draft_reports
                SET form_data = ?,
                    foto1_data = ?,
                    foto2_data = ?,
                    foto3_data = ?,
                    foto4_data = ?,
                    firma_tecnico_data = ?,
                    firma_cliente_data = ?,
                    pdf_preview = ?,
                    deal_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE folio = ?
            ''', (json.dumps(form_data) if isinstance(form_data, dict) else form_data,
                  foto1, foto2, foto3, foto4,
                  firma_tecnico, firma_cliente,
                  pdf_preview, deal_id, folio))
        else:
            # Insert new draft
            cursor.execute('''
                INSERT INTO draft_reports
                (folio, form_data, foto1_data, foto2_data, foto3_data, foto4_data,
                 firma_tecnico_data, firma_cliente_data, pdf_preview, status, deal_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?)
            ''', (folio,
                  json.dumps(form_data) if isinstance(form_data, dict) else form_data,
                  foto1, foto2, foto3, foto4,
                  firma_tecnico, firma_cliente,
                  pdf_preview, deal_id))
        
        # If deal_id is provided, link the report to the deal
        if deal_id:
            try:
                link_reporte_to_deal(deal_id, folio)
            except:
                pass  # Ignore if already linked
        
        return True

def get_draft_by_folio(folio):
    """Get complete draft report by folio"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM draft_reports WHERE folio = ?", (folio,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_drafts(status=None):
    """Get all draft reports, optionally filtered by status"""
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute('''
                SELECT * FROM draft_reports 
                WHERE status = ?
                ORDER BY updated_at DESC
            ''', (status,))
        else:
            cursor.execute("SELECT * FROM draft_reports ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_pending_drafts_by_tecnico(tecnico_nombre=None, is_admin=False):
    """Get pending draft reports (status='draft'), filtered by technician if not admin"""
    import json
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM draft_reports 
            WHERE status = 'draft' OR status IS NULL
            ORDER BY updated_at DESC
        ''')
        all_drafts = [dict(row) for row in cursor.fetchall()]
        
        # Filter by technician if not admin
        if not is_admin and tecnico_nombre:
            filtered_drafts = []
            for draft in all_drafts:
                try:
                    form_data = json.loads(draft["form_data"]) if isinstance(draft["form_data"], str) else draft["form_data"]
                    draft_tecnico = form_data.get("tecnico", "").strip()
                    if draft_tecnico == tecnico_nombre:
                        filtered_drafts.append(draft)
                except:
                    continue
            return filtered_drafts
        
        return all_drafts

def delete_draft(folio):
    """Delete a draft report by folio"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM draft_reports WHERE folio = ?", (folio,))
        return cursor.rowcount > 0

def mark_draft_as_sent(folio):
    """Mark a draft report as sent"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE draft_reports
            SET status = 'sent', updated_at = CURRENT_TIMESTAMP
            WHERE folio = ?
        ''', (folio,))
        return cursor.rowcount > 0

def update_draft_pdf(folio, pdf_data):
    """Update only the PDF preview for a draft"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE draft_reports
            SET pdf_preview = ?, updated_at = CURRENT_TIMESTAMP
            WHERE folio = ?
        ''', (pdf_data, folio))
        return cursor.rowcount > 0

# ========== Almacen (Inventory) Functions ==========

def get_all_refacciones():
    """Get all refacciones from almacen"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM almacen ORDER BY numero_parte")
        return [dict(row) for row in cursor.fetchall()]

def get_refaccion_by_id(refaccion_id):
    """Get refaccion by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM almacen WHERE id = ?", (refaccion_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_refaccion(numero_parte, descripcion, unidad='', cantidad=0, ubicacion='', detalles_importacion='', ubicacion_especifica=''):
    """Create a new refaccion in almacen"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO almacen (numero_parte, descripcion, unidad, cantidad, ubicacion, detalles_importacion, ubicacion_especifica)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (numero_parte, descripcion, unidad, cantidad, ubicacion, detalles_importacion, ubicacion_especifica))
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # numero_parte already exists
        return None

def update_refaccion(refaccion_id, numero_parte, descripcion, unidad='', cantidad=0, ubicacion='', detalles_importacion='', ubicacion_especifica=''):
    """Update refaccion information"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE almacen
                SET numero_parte = ?, descripcion = ?, unidad = ?, cantidad = ?, 
                    ubicacion = ?, detalles_importacion = ?, ubicacion_especifica = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (numero_parte, descripcion, unidad, cantidad, ubicacion, detalles_importacion, ubicacion_especifica, refaccion_id))
            return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        # numero_parte already exists
        return False

# --- Cotizaciones Functions ---

def get_next_cotizacion_folio(sucursal):
    """Generate the next quotation folio based on sucursal (T-00001, M-00001, etc.)"""
    prefix = 'T' if sucursal == 'Tijuana' else 'M'
    
    with get_db() as conn:
        cursor = conn.cursor()
        # Get the last folio for this prefix
        cursor.execute(
            "SELECT folio FROM cotizaciones WHERE folio LIKE ? ORDER BY folio DESC LIMIT 1",
            (f"{prefix}-%",)
        )
        row = cursor.fetchone()
        
        if row:
            # Extract number from last folio (e.g., "T-00015" -> 15)
            try:
                last_num = int(row['folio'].split('-')[1])
                next_num = last_num + 1
            except (IndexError, ValueError):
                next_num = 1
        else:
            next_num = 1
        
        # Format with leading zeros (5 digits)
        return f"{prefix}-{next_num:05d}"

def get_all_cotizaciones():
    """Get all quotations ordered by date desc"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cotizaciones ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_cotizacion_by_id(cotizacion_id):
    """Get quotation and its items by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get master record
        cursor.execute("SELECT * FROM cotizaciones WHERE id = ?", (cotizacion_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        cotizacion = dict(row)
        
        # Get items
        cotizacion['items'] = get_cotizacion_items(cotizacion_id)
        return cotizacion

def get_cotizacion_items(cotizacion_id):
    """Get all items for a cotizacion"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cotizacion_items WHERE cotizacion_id = ? ORDER BY linea ASC", (cotizacion_id,))
        return [dict(item) for item in cursor.fetchall()]

def create_cotizacion(data, items):
    """Create a new quotation with items"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Insert Master
            cursor.execute('''
                INSERT INTO cotizaciones (
                    folio, fecha, cliente_id, cliente_nombre, cliente_direccion, cliente_telefono, cliente_rfc,
                    atencion_a, referencia, sucursal, vigencia, moneda, tipo_cambio,
                    tiempo_entrega, condiciones_pago, notas, subtotal, iva_porcentaje, iva_monto, total, cotizador_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('folio'), data.get('fecha'), data.get('cliente_id'), data.get('cliente_nombre'),
                data.get('cliente_direccion'), data.get('cliente_telefono'), data.get('cliente_rfc'), data.get('atencion_a'),
                data.get('referencia'), data.get('sucursal'), data.get('vigencia'), data.get('moneda'),
                data.get('tipo_cambio'), data.get('tiempo_entrega'), data.get('condiciones_pago'),
                data.get('notas'), data.get('subtotal'), data.get('iva_porcentaje'),
                data.get('iva_monto'), data.get('total'), data.get('cotizador_id')
            ))
            
            cotizacion_id = cursor.lastrowid
            
            # Insert Items
            for item in items:
                cursor.execute('''
                    INSERT INTO cotizacion_items (
                        cotizacion_id, linea, cantidad, unidad, numero_parte, descripcion,
                        tiempo_entrega_item, precio_unitario, importe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cotizacion_id, item.get('linea'), item.get('cantidad'), item.get('unidad'),
                    item.get('numero_parte'), item.get('descripcion'), item.get('tiempo_entrega_item'),
                    item.get('precio_unitario'), item.get('importe')
                ))
                
            return cotizacion_id
    except Exception as e:
        print(f"Error creating cotizacion: {e}")
        return None

def update_cotizacion(cotizacion_id, data, items):
    """Update quotation and replace items"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Update Master
            cursor.execute('''
                UPDATE cotizaciones SET
                    folio=?, fecha=?, cliente_id=?, cliente_nombre=?, cliente_direccion=?, cliente_telefono=?, cliente_rfc=?,
                    atencion_a=?, referencia=?, sucursal=?, vigencia=?, moneda=?, tipo_cambio=?,
                    tiempo_entrega=?, condiciones_pago=?, notas=?, subtotal=?, iva_porcentaje=?,
                    iva_monto=?, total=?, cotizador_id=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (
                data.get('folio'), data.get('fecha'), data.get('cliente_id'), data.get('cliente_nombre'),
                data.get('cliente_direccion'), data.get('cliente_telefono'), data.get('cliente_rfc'), data.get('atencion_a'),
                data.get('referencia'), data.get('sucursal'), data.get('vigencia'), data.get('moneda'),
                data.get('tipo_cambio'), data.get('tiempo_entrega'), data.get('condiciones_pago'),
                data.get('notas'), data.get('subtotal'), data.get('iva_porcentaje'),
                data.get('iva_monto'), data.get('total'), data.get('cotizador_id'), cotizacion_id
            ))
            
            # Delete old items
            cursor.execute("DELETE FROM cotizacion_items WHERE cotizacion_id = ?", (cotizacion_id,))
            
            # Insert new items
            for item in items:
                cursor.execute('''
                    INSERT INTO cotizacion_items (
                        cotizacion_id, linea, cantidad, unidad, numero_parte, descripcion,
                        tiempo_entrega_item, precio_unitario, importe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cotizacion_id, item.get('linea'), item.get('cantidad'), item.get('unidad'),
                    item.get('numero_parte'), item.get('descripcion'), item.get('tiempo_entrega_item'),
                    item.get('precio_unitario'), item.get('importe')
                ))
                
            return True
    except Exception as e:
        print(f"Error updating cotizacion: {e}")
        return False

def delete_cotizacion(cotizacion_id):
    """Delete quotation and its items"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Items are deleted by CASCADE if supported, but we do it manually to be safe
            cursor.execute("DELETE FROM cotizacion_items WHERE cotizacion_id = ?", (cotizacion_id,))
            cursor.execute("DELETE FROM cotizaciones WHERE id = ?", (cotizacion_id,))
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting cotizacion: {e}")
        return False

def delete_refaccion(refaccion_id):
    """Delete a refaccion by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM almacen WHERE id = ?", (refaccion_id,))
        return cursor.rowcount > 0

def search_refacciones(search_term='', ubicacion=''):
    """Search refacciones by part number or description, optionally filter by location"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT a.*, 
                   COALESCE((SELECT SUM(cantidad) FROM almacen_reservas ar WHERE ar.refaccion_id = a.id AND ar.status = 'active'), 0) as apartados
            FROM almacen a 
            WHERE 1=1
        """
        params = []
        
        if search_term:
            query += " AND (numero_parte LIKE ? OR descripcion LIKE ?)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
        
        if ubicacion:
            query += " AND ubicacion = ?"
            params.append(ubicacion)
        
        query += " ORDER BY numero_parte"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_refaccion_by_id(refaccion_id):
    """Get refaccion by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM almacen WHERE id = ?", (refaccion_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_refacciones():
    """Get all refacciones"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, 
                   COALESCE((SELECT SUM(cantidad) FROM almacen_reservas ar WHERE ar.refaccion_id = a.id AND ar.status = 'active'), 0) as apartados
            FROM almacen a 
            ORDER BY numero_parte
        """)
        return [dict(row) for row in cursor.fetchall()]

# ==================== INVENTORY MOVEMENTS FUNCTIONS ====================

def get_refaccion_by_numero_parte(numero_parte):
    """Get refaccion by numero_parte"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM almacen WHERE numero_parte = ?", (numero_parte,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_refaccion_with_stock(numero_parte):
    """Get refaccion with calculated stock (cantidad - apartados)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, 
                   COALESCE((SELECT SUM(cantidad) FROM almacen_reservas ar WHERE ar.refaccion_id = a.id AND ar.status = 'active'), 0) as apartados,
                   (a.cantidad - COALESCE((SELECT SUM(cantidad) FROM almacen_reservas ar WHERE ar.refaccion_id = a.id AND ar.status = 'active'), 0)) as disponible
            FROM almacen a 
            WHERE a.numero_parte = ?
        """, (numero_parte,))
        row = cursor.fetchone()
        return dict(row) if row else None

def has_invoice_been_applied(factura_id):
    """Check if inventory movement has already been applied for this invoice"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM inventory_movements 
            WHERE invoice_id = ? AND tipo = 'salida'
        """, (factura_id,))
        result = cursor.fetchone()
        return result['count'] > 0 if result else False

def apply_invoice_inventory_salida(factura_id, usuario_id):
    """
    Apply inventory salida (outgoing) for all invoice items with codigo (numero_parte).
    This function will fulfill reservations (apartados) first, then deduct from stock.
    Returns: (success: bool, errors: list, movements: list)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if already applied
        if has_invoice_been_applied(factura_id):
            return False, ["La salida de almacén ya fue aplicada para esta factura"], []
        
        # Get invoice to obtain cliente_id
        factura = get_factura_by_id(factura_id)
        if not factura:
            return False, ["Factura no encontrada"], []
        
        cliente_id = factura.get('cliente_id')
        if not cliente_id:
            return False, ["La factura no tiene cliente asociado"], []
        
        # Get invoice items
        partidas = get_factura_partidas(factura_id)
        if not partidas:
            return False, ["La factura no tiene partidas"], []
        
        errors = []
        movements = []
        
        # Process each item
        for partida in partidas:
            codigo = partida.get('codigo')
            if not codigo:
                continue  # Skip items without codigo (numero_parte)
            
            cantidad_necesaria = int(partida.get('cantidad', 0))
            if cantidad_necesaria <= 0:
                continue
            
            # Get refaccion with stock info
            refaccion = get_refaccion_with_stock(codigo)
            if not refaccion:
                errors.append(f"Refacción con número de parte '{codigo}' no encontrada en almacén")
                continue
            
            disponible = refaccion.get('disponible', 0)
            if disponible < cantidad_necesaria:
                errors.append(f"Stock insuficiente para '{codigo}': disponible={disponible}, necesario={cantidad_necesaria}")
                continue
            
            refaccion_id = refaccion['id']
            
            # IMPORTANTE: Primero liberar apartados usando fulfill_reserva
            # Esto libera los apartados del cliente Y descuenta del stock principal
            # fulfill_reserva SIEMPRE descuenta del stock, incluso si no hay apartados
            # Por eso NO debemos descontar manualmente después
            try:
                # Verificar stock antes de llamar a fulfill_reserva
                stock_antes = refaccion['cantidad']
                
                # Llamar a fulfill_reserva - esto libera apartados y descuenta stock
                fulfill_reserva(refaccion_id, cliente_id, cantidad_necesaria)
                
                # fulfill_reserva hace commit en su propia transacción
                # El stock ya fue descontado, no necesitamos descontar manualmente
            except Exception as e:
                # Si hay error crítico, registrar y continuar con descuento manual
                print(f"⚠️ Error al liberar apartados para {codigo}: {e}")
                # Descontar manualmente del stock si fulfill_reserva falló
                nueva_cantidad = refaccion['cantidad'] - cantidad_necesaria
                cursor.execute("""
                    UPDATE almacen 
                    SET cantidad = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (nueva_cantidad, refaccion_id))
            
            # Register movement in kardex (fulfill_reserva no registra movimientos)
            cursor.execute("""
                INSERT INTO inventory_movements 
                (invoice_id, refaccion_id, numero_parte, cantidad, tipo, usuario_id, notas)
                VALUES (?, ?, ?, ?, 'salida', ?, ?)
            """, (
                factura_id,
                refaccion_id,
                codigo,
                -cantidad_necesaria,  # Negative for salida
                usuario_id,
                f"Salida por factura {factura_id} (apartados liberados)"
            ))
            
            movement_id = cursor.lastrowid
            movements.append({
                'id': movement_id,
                'numero_parte': codigo,
                'cantidad': cantidad_necesaria,
                'refaccion_id': refaccion_id
            })
        
        if errors:
            conn.rollback()
            return False, errors, []
        
        conn.commit()
        return True, [], movements

def get_inventory_movements_by_invoice(factura_id):
    """Get all inventory movements for an invoice"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT im.*, a.descripcion as refaccion_descripcion
            FROM inventory_movements im
            LEFT JOIN almacen a ON im.refaccion_id = a.id
            WHERE im.invoice_id = ?
            ORDER BY im.fecha DESC
        """, (factura_id,))
        return [dict(row) for row in cursor.fetchall()]

# ==================== REMISIONES FUNCTIONS ====================

def get_next_remision_folio():
    """Generate next remision folio (REM-00001)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT folio FROM remisiones ORDER BY id DESC LIMIT 1")
        last = cursor.fetchone()
        
        if last and last['folio']:
            try:
                num = int(last['folio'].split('-')[1])
                return f"REM-{num + 1:05d}"
            except:
                return "REM-00001"
        return "REM-00001"

def create_remision(cliente_id, cliente_nombre, fecha, estado='draft', factura_id=None, 
                    cotizacion_id=None, trato_id=None, oc_cliente_id=None, notas=None, created_by=None):
    """Create a new remision"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            folio = get_next_remision_folio()
            cursor.execute('''
                INSERT INTO remisiones 
                (folio, cliente_id, cliente_nombre, fecha, estado, factura_id, cotizacion_id, 
                 trato_id, oc_cliente_id, notas, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (folio, cliente_id, cliente_nombre, fecha, estado, factura_id, cotizacion_id,
                  trato_id, oc_cliente_id, notas, created_by))
            return cursor.lastrowid
    except Exception as e:
        print(f"Error creating remision: {e}")
        return None

def get_remision_items(remision_id):
    """Get all items for a remision"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM remision_items 
            WHERE remision_id = ? 
            ORDER BY orden, id
        ''', (remision_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_remision_by_id(remision_id):
    """Get remision by ID with items"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM remisiones WHERE id = ?
        ''', (remision_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        remision = dict(row)
        remision['items'] = get_remision_items(remision_id)
        return remision

def get_all_remisiones():
    """Get all remisiones"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM remisiones ORDER BY fecha DESC, id DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

def update_remision(remision_id, **kwargs):
    """Update remision fields"""
    with get_db() as conn:
        cursor = conn.cursor()
        updates = []
        params = []
        
        allowed_fields = ['cliente_id', 'cliente_nombre', 'fecha', 'estado', 'factura_id',
                         'cotizacion_id', 'trato_id', 'oc_cliente_id', 'notas']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(remision_id)
        
        cursor.execute(f"UPDATE remisiones SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        return cursor.rowcount > 0

def add_remision_item(remision_id, descripcion, cantidad, unidad='PZA', refaccion_id=None, numero_parte=None, orden=0):
    """Add item to remision"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO remision_items 
            (remision_id, refaccion_id, numero_parte, descripcion, cantidad, unidad, orden)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (remision_id, refaccion_id, numero_parte, descripcion, cantidad, unidad, orden))
        return cursor.lastrowid

def delete_remision_item(item_id):
    """Delete a remision item"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM remision_items WHERE id = ?", (item_id,))
        return cursor.rowcount > 0

def has_remision_been_confirmed(remision_id):
    """Check if remision has been confirmed (salida applied)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM inventory_movements 
            WHERE remision_id = ? AND tipo = 'salida'
        """, (remision_id,))
        result = cursor.fetchone()
        return result['count'] > 0 if result else False

def has_factura_remision_confirmed(factura_id):
    """Check if factura has a confirmed remision (to avoid double salida)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM remisiones 
            WHERE factura_id = ? AND estado = 'confirmed'
        """, (factura_id,))
        result = cursor.fetchone()
        return result['count'] > 0 if result else False

def apply_remision_inventory_salida(remision_id, usuario_id):
    """
    Apply inventory salida (outgoing) for all remision items.
    Returns: (success: bool, errors: list, movements: list)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if already applied
        if has_remision_been_confirmed(remision_id):
            return False, ["La salida de almacén ya fue aplicada para esta remisión"], []
        
        # Get remision items
        items = get_remision_items(remision_id)
        if not items:
            return False, ["La remisión no tiene items"], []
        
        errors = []
        movements = []
        
        # Process each item
        for item in items:
            numero_parte = item.get('numero_parte')
            if not numero_parte:
                continue  # Skip items without numero_parte
            
            cantidad_necesaria = int(item.get('cantidad', 0))
            if cantidad_necesaria <= 0:
                continue
            
            # Get refaccion with stock info
            refaccion = get_refaccion_with_stock(numero_parte)
            if not refaccion:
                errors.append(f"Refacción con número de parte '{numero_parte}' no encontrada en almacén")
                continue
            
            disponible = refaccion.get('disponible', 0)
            if disponible < cantidad_necesaria:
                errors.append(f"Stock insuficiente para '{numero_parte}': disponible={disponible}, necesario={cantidad_necesaria}")
                continue
            
            # Update almacen: decrease cantidad
            refaccion_id = refaccion['id']
            nueva_cantidad = refaccion['cantidad'] - cantidad_necesaria
            cursor.execute("""
                UPDATE almacen 
                SET cantidad = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (nueva_cantidad, refaccion_id))
            
            # Register movement in kardex
            cursor.execute("""
                INSERT INTO inventory_movements 
                (remision_id, refaccion_id, numero_parte, cantidad, tipo, usuario_id, notas)
                VALUES (?, ?, ?, ?, 'salida', ?, ?)
            """, (
                remision_id,
                refaccion_id,
                numero_parte,
                -cantidad_necesaria,  # Negative for salida
                usuario_id,
                f"Salida por remisión {remision_id}"
            ))
            
            movement_id = cursor.lastrowid
            movements.append({
                'id': movement_id,
                'numero_parte': numero_parte,
                'cantidad': cantidad_necesaria,
                'refaccion_id': refaccion_id
            })
        
        if errors:
            conn.rollback()
            return False, errors, []
        
        # Update remision estado to 'confirmed'
        cursor.execute("""
            UPDATE remisiones 
            SET estado = 'confirmed', updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (remision_id,))
        
        conn.commit()
        return True, [], movements

def get_inventory_movements_by_remision(remision_id):
    """Get all inventory movements for a remision"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT im.*, a.descripcion as refaccion_descripcion
            FROM inventory_movements im
            LEFT JOIN almacen a ON im.refaccion_id = a.id
            WHERE im.remision_id = ?
            ORDER BY im.fecha DESC
        """, (remision_id,))
        return [dict(row) for row in cursor.fetchall()]

# ==================== DEAL UTIL ====================

def set_deal_ocu_id(deal_id, ocu_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE crm_deals
            SET ocu_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (ocu_id, deal_id))
        return cursor.rowcount > 0

# ==================== OCU FUNCTIONS ====================

def create_oc_cliente(folio_cliente, cliente_id=None, cliente_nombre=None, notas=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO oc_cliente (folio_cliente, cliente_id, cliente_nombre, notas)
            VALUES (?, ?, ?, ?)
        ''', (folio_cliente, cliente_id, cliente_nombre, notas))
        # If already existed, fetch id
        if cursor.lastrowid:
            return cursor.lastrowid
        cursor.execute("SELECT id FROM oc_cliente WHERE folio_cliente = ? AND (cliente_id = ? OR cliente_id IS NULL)", (folio_cliente, cliente_id))
        row = cursor.fetchone()
        return row['id'] if row else None

def create_ocu(oc_cliente_id, cliente_id, cliente_nombre, estado='open', notas=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ocu (oc_cliente_id, cliente_id, cliente_nombre, estado, notas)
            VALUES (?, ?, ?, ?, ?)
        ''', (oc_cliente_id, cliente_id, cliente_nombre, estado, notas))
        ocu_id = cursor.lastrowid
        
        # NOTIFICATION LOGIC
        try:
            # Find users to notify: Compras, Contabilidad, and Admin
            cursor.execute("SELECT id, puesto, role FROM users")
            all_users = [dict(row) for row in cursor.fetchall()]
            
            target_puestos = ['Compras', 'Contabilidad', 'Administrador']
            notified_users = set()
            
            for user in all_users:
                puesto = (user.get('puesto') or '').strip()
                role = (user.get('role') or '').strip()
                
                if (puesto in target_puestos) or (role == 'admin'):
                    if user['id'] not in notified_users:
                        create_notification(
                            user_id=user['id'],
                            tipo='ocu',
                            titulo='Nueva OCu Generada',
                            mensaje=f"Se ha generado la OCu para el cliente {cliente_nombre}",
                            deal_id=None # No direct deal link here, could link if needed
                        )
                        notified_users.add(user['id'])
        except Exception as e:
            print(f"Error sending OCu notifications: {e}")
            
        return ocu_id

def add_ocu_item(ocu_id, numero_parte, descripcion, unidad, cantidad, reservado=0, faltante=0):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ocu_items (ocu_id, numero_parte, descripcion, unidad, cantidad, reservado, faltante)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ocu_id, numero_parte, descripcion, unidad, cantidad, reservado, faltante))
        item_id = cursor.lastrowid
        
        # AUTO-GENERATE REQUISITION IF MISSING PARTS
        if faltante > 0:
            try:
                # Get OCu details for context
                # We can call get_ocu_by_id but we are inside a context, so let's query directly to avoid connection issues or recursion
                cursor.execute("SELECT * FROM ocu WHERE id = ?", (ocu_id,))
                ocu = cursor.fetchone()
                
                if ocu:
                    cliente_id = ocu['cliente_id']
                    cliente_nombre = ocu['cliente_nombre']
                    oc_cliente_id = ocu['oc_cliente_id']
                    
                    # Get folio_cliente (OCu folio)
                    folio_ocu = None
                    if oc_cliente_id:
                        cursor.execute("SELECT folio_cliente FROM oc_cliente WHERE id = ?", (oc_cliente_id,))
                        oc_row = cursor.fetchone()
                        if oc_row:
                            folio_ocu = oc_row['folio_cliente']
                    
                    # Create Requisition
                    # NOTE: We pass 'descripcion' explicitly here, fixing the missing description issue
                    create_purchase_requisition(
                        ocu_id=ocu_id,
                        numero_parte=numero_parte,
                        cantidad=faltante,
                        notas=f"Generado automáticamente por faltante en OCu item {item_id}",
                        descripcion=descripcion, # FIX: Pass description!
                        cliente_id=cliente_id,
                        cliente_nombre=cliente_nombre,
                        folio_ocu=folio_ocu
                    )
            except Exception as e:
                print(f"Error creating automatic requisition: {e}")
        
        return item_id

def create_purchase_requisition(ocu_id, numero_parte, cantidad, notas=None, descripcion=None, cliente_id=None, cliente_nombre=None, folio_ocu=None):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Si no se proporciona folio_ocu, obtenerlo del OCu
        if not folio_ocu:
            cursor.execute("SELECT oc_cliente_id FROM ocu WHERE id = ?", (ocu_id,))
            ocu_row = cursor.fetchone()
            if ocu_row and ocu_row['oc_cliente_id']:
                cursor.execute("SELECT folio_cliente FROM oc_cliente WHERE id = ?", (ocu_row['oc_cliente_id'],))
                oc_row = cursor.fetchone()
                if oc_row:
                    folio_ocu = oc_row['folio_cliente']
        
        # Si no se proporciona cliente_id o cliente_nombre, obtenerlos del OCu
        if not cliente_id or not cliente_nombre:
            cursor.execute("SELECT cliente_id, cliente_nombre FROM ocu WHERE id = ?", (ocu_id,))
            ocu_info = cursor.fetchone()
            if ocu_info:
                if not cliente_id:
                    cliente_id = ocu_info['cliente_id']
                if not cliente_nombre:
                    cliente_nombre = ocu_info['cliente_nombre']
        
        cursor.execute('''
            INSERT INTO purchase_requisitions (ocu_id, cliente_id, cliente_nombre, folio_ocu, numero_parte, descripcion, cantidad, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ocu_id, cliente_id, cliente_nombre, folio_ocu, numero_parte, descripcion, cantidad, notas))
        req_id = cursor.lastrowid
        
        # Crear notificaciones para usuarios con puesto "Compras"
        cursor.execute("SELECT id, nombre FROM users WHERE puesto = 'Compras'")
        compras_users = cursor.fetchall()
        for user_row in compras_users:
            user_id = user_row['id']
            user_nombre = user_row['nombre']
            titulo = "📋 Nueva Requisición de Compra"
            mensaje = f"OCu {folio_ocu or ocu_id} - Faltante: {descripcion or numero_parte} (Cantidad: {cantidad})"
            cursor.execute('''
                INSERT INTO notifications (user_id, tipo, titulo, mensaje, ocu_id, leido, created_at)
                VALUES (?, 'purchase_requisition', ?, ?, ?, 0, CURRENT_TIMESTAMP)
            ''', (user_id, titulo, mensaje, ocu_id))
        
        conn.commit()
        return req_id

def create_finance_request(ocu_id, notas=None, cliente_id=None, cliente_nombre=None, folio_ocu=None):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Si no se proporciona folio_ocu, obtenerlo del OCu
        if not folio_ocu:
            cursor.execute("SELECT oc_cliente_id FROM ocu WHERE id = ?", (ocu_id,))
            ocu_row = cursor.fetchone()
            if ocu_row and ocu_row['oc_cliente_id']:
                cursor.execute("SELECT folio_cliente FROM oc_cliente WHERE id = ?", (ocu_row['oc_cliente_id'],))
                oc_row = cursor.fetchone()
                if oc_row:
                    folio_ocu = oc_row['folio_cliente']
        
        # Si no se proporciona cliente_id o cliente_nombre, obtenerlos del OCu
        if not cliente_id or not cliente_nombre:
            cursor.execute("SELECT cliente_id, cliente_nombre FROM ocu WHERE id = ?", (ocu_id,))
            ocu_info = cursor.fetchone()
            if ocu_info:
                if not cliente_id:
                    cliente_id = ocu_info['cliente_id']
                if not cliente_nombre:
                    cliente_nombre = ocu_info['cliente_nombre']
        
        cursor.execute('''
            INSERT INTO finance_requests (ocu_id, cliente_id, cliente_nombre, folio_ocu, status, notas)
            VALUES (?, ?, ?, ?, 'pending', ?)
        ''', (ocu_id, cliente_id, cliente_nombre, folio_ocu, notas))
        fr_id = cursor.lastrowid
        
        # Crear notificaciones para usuarios con puesto "Contador"
        cursor.execute("SELECT id, nombre FROM users WHERE puesto = 'Contador'")
        contador_users = cursor.fetchall()
        for user_row in contador_users:
            user_id = user_row['id']
            user_nombre = user_row['nombre']
            titulo = "💰 Nueva Solicitud de Factura"
            cliente_info = f" - Cliente: {cliente_nombre}" if cliente_nombre else ""
            mensaje = f"OCu {folio_ocu or ocu_id}{cliente_info} - Lista para facturar"
            cursor.execute('''
                INSERT INTO notifications (user_id, tipo, titulo, mensaje, ocu_id, leido, created_at)
                VALUES (?, 'finance_request', ?, ?, ?, 0, CURRENT_TIMESTAMP)
            ''', (user_id, titulo, mensaje, ocu_id))
        
        conn.commit()
        return fr_id

def notify_contador_ocu_nueva(ocu_id):
    """
    Notificar al contador cuando hay una OCu nueva con stock disponible.
    Solo notifica si hay al menos una partida con reservado > 0.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Obtener información del OCu
        cursor.execute("SELECT * FROM ocu WHERE id = ?", (ocu_id,))
        ocu_row = cursor.fetchone()
        if not ocu_row:
            return
        
        ocu = dict(ocu_row)
        
        # Obtener folio_ocu
        folio_ocu = None
        if ocu.get('oc_cliente_id'):
            cursor.execute("SELECT folio_cliente FROM oc_cliente WHERE id = ?", (ocu.get('oc_cliente_id'),))
            oc_row = cursor.fetchone()
            if oc_row:
                folio_ocu = oc_row['folio_cliente']
        
        # Obtener items del OCu
        cursor.execute("SELECT * FROM ocu_items WHERE ocu_id = ? ORDER BY id", (ocu_id,))
        items = [dict(row) for row in cursor.fetchall()]
        
        # Calcular totales
        total_reservado = sum(item.get('reservado', 0) or 0 for item in items)
        total_faltante = sum(item.get('faltante', 0) or 0 for item in items)
        total_cantidad = sum(item.get('cantidad', 0) or 0 for item in items)
        
        # SOLO notificar si hay al menos una partida en stock (reservado > 0)
        if total_reservado <= 0:
            return  # No hay stock, no notificar al contador
        
        # Obtener usuarios contador
        cursor.execute("SELECT id, nombre FROM users WHERE puesto = 'Contador'")
        contador_users = cursor.fetchall()
        
        cliente_nombre = ocu.get('cliente_nombre', '')
        cliente_info = f" - Cliente: {cliente_nombre}" if cliente_nombre else ""
        
        # Determinar tipo de notificación según el estado
        estado = ocu.get('estado', 'open')
        if estado == 'ready_to_invoice' or total_faltante == 0:
            # OCu completa, lista para facturar
            titulo = "💰 OCu Lista para Facturar"
            mensaje = f"OCu {folio_ocu or ocu_id}{cliente_info} - Todas las partidas disponibles en stock"
        elif estado == 'partial_waiting_purchase' or (total_reservado > 0 and total_faltante > 0):
            # OCu parcial
            partidas_disponibles = [item for item in items if (item.get('reservado', 0) or 0) > 0]
            titulo = "💰 OCu Parcial - Partidas Disponibles"
            mensaje = f"OCu {folio_ocu or ocu_id}{cliente_info} - {len(partidas_disponibles)} partida(s) disponible(s) en stock. ¿Desea facturar parcial o esperar orden completa?"
        else:
            # Estado desconocido pero hay stock
            titulo = "💰 Nueva OCu con Stock Disponible"
            mensaje = f"OCu {folio_ocu or ocu_id}{cliente_info} - Partidas disponibles en stock"
        
        # Crear notificaciones para todos los contadores
        for user_row in contador_users:
            user_id = user_row['id']
            cursor.execute('''
                INSERT INTO notifications (user_id, tipo, titulo, mensaje, ocu_id, leido, created_at)
                VALUES (?, 'ocu_nueva', ?, ?, ?, 0, CURRENT_TIMESTAMP)
            ''', (user_id, titulo, mensaje, ocu_id))
        
        conn.commit()

def get_ocu_by_id(ocu_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ocu WHERE id = ?", (ocu_id,))
        row = cursor.fetchone()
        if not row:
            return None
        ocu = dict(row)
        # get folio_cliente from oc_cliente
        try:
            cursor.execute("SELECT folio_cliente FROM oc_cliente WHERE id = ?", (ocu.get('oc_cliente_id'),))
            oc_row = cursor.fetchone()
            if oc_row:
                ocu['folio_ocu'] = oc_row['folio_cliente']
        except:
            ocu['folio_ocu'] = None
        cursor.execute("SELECT * FROM ocu_items WHERE ocu_id = ? ORDER BY id", (ocu_id,))
        ocu['items'] = [dict(r) for r in cursor.fetchall()]
        return ocu

# ==================== FINANCE & PURCHASE REQUESTS ====================

def get_finance_requests(status=None):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM finance_requests"
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]

def update_finance_request_status(fr_id, status):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE finance_requests
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, fr_id))
        conn.commit()
        return cursor.rowcount > 0

def get_purchase_requisitions(status=None):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM purchase_requisitions"
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]

def update_purchase_requisition_status(req_id, status):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE purchase_requisitions
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, req_id))
        conn.commit()
        return cursor.rowcount > 0

# ==================== ALMACEN RESERVAS FUNCTIONS ====================

def create_reserva(refaccion_id, cliente_id, cantidad, orden_compra='', cliente_nombre=''):
    """Create a new reservation (apartado)"""
    with get_db() as conn:
        cursor = conn.cursor()
        # If no client name provided but ID is, fetch it
        if cliente_id and not cliente_nombre:
            cursor.execute("SELECT nombre FROM clients WHERE id = ?", (cliente_id,))
            row = cursor.fetchone()
            if row:
                cliente_nombre = row['nombre']
                
        cursor.execute('''
            INSERT INTO almacen_reservas (refaccion_id, cliente_id, cliente_nombre, orden_compra, cantidad, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        ''', (refaccion_id, cliente_id, cliente_nombre, orden_compra, cantidad))
        return cursor.lastrowid

def get_reservas_by_refaccion(refaccion_id, status='active'):
    """Get active reservations for a specific part"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM almacen_reservas WHERE refaccion_id = ?"
        params = [refaccion_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
            
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def delete_reserva(reserva_id):
    """Delete (cancel) a reservation"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM almacen_reservas WHERE id = ?", (reserva_id,))
        return cursor.rowcount > 0

def fulfill_reserva(refaccion_id, cliente_id, cantidad_usada):
    """
    Deduct from reservations when items are used/invoiced.
    Strategies: FIFO (First In First Out) for reservations.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get active reservations for this client and part, ordered by date
        cursor.execute('''
            SELECT * FROM almacen_reservas 
            WHERE refaccion_id = ? AND cliente_id = ? AND status = 'active'
            ORDER BY fecha_reserva ASC
        ''', (refaccion_id, cliente_id))
        reservas = [dict(row) for row in cursor.fetchall()]
        
        remaining_to_deduct = cantidad_usada
        
        for res in reservas:
            if remaining_to_deduct <= 0:
                break
                
            qty = res['cantidad']
            
            if qty <= remaining_to_deduct:
                # Fully limit this reservation
                cursor.execute("UPDATE almacen_reservas SET status = 'fulfilled', cantidad = 0 WHERE id = ?", (res['id'],))
                remaining_to_deduct -= qty
            else:
                # Partially fulfill
                new_qty = qty - remaining_to_deduct
                cursor.execute("UPDATE almacen_reservas SET cantidad = ? WHERE id = ?", (new_qty, res['id']))
                remaining_to_deduct = 0
                
        # Also decrease main stock
        cursor.execute("UPDATE almacen SET cantidad = cantidad - ? WHERE id = ?", (cantidad_usada, refaccion_id))
        
        conn.commit()


# ==================== CRM FUNCTIONS ====================

CRM_STAGES = [
    'Prospecto',
    'Contacto Inicial',
    'Solicitud de Cotización',
    'Cotización Lista para Enviar',
    'Negociación',
    'Ganado',
    'Pedido',
    'Solicitud de Factura'
]

def create_deal(data):
    """Create a new CRM deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Generate folio if not provided
        folio = data.get('folio')
        if not folio:
            tipo_deal = data.get('tipo_deal', 'venta')
            folio = get_next_deal_folio(tipo_deal)
        
        # If fecha_creacion is provided, use it; otherwise use CURRENT_TIMESTAMP
        fecha_creacion = data.get('fecha_creacion')
        if fecha_creacion:
            cursor.execute('''
                INSERT INTO crm_deals (
                    cliente_id, contacto_nombre, vendedor_id, titulo, valor_estimado,
                    moneda, etapa, fecha_cierre_estimada, producto_servicio, notas, email,
                    firma_vendedor, mensaje_envio, tipo_deal, fecha_servicio, tiempo_estimado_horas, folio, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('cliente_id'), data.get('contacto_nombre'), data.get('vendedor_id'),
                data.get('titulo'), data.get('valor_estimado', 0), data.get('moneda', 'USD'),
                data.get('etapa', 'Prospecto'), data.get('fecha_cierre_estimada'),
                data.get('producto_servicio'), data.get('notas'), data.get('email'),
                data.get('firma_vendedor'), data.get('mensaje_envio'),
                data.get('tipo_deal', 'venta'), data.get('fecha_servicio'), data.get('tiempo_estimado_horas'),
                folio, fecha_creacion
            ))
        else:
            cursor.execute('''
                INSERT INTO crm_deals (
                    cliente_id, contacto_nombre, vendedor_id, titulo, valor_estimado,
                    moneda, etapa, fecha_cierre_estimada, producto_servicio, notas, email,
                    firma_vendedor, mensaje_envio, tipo_deal, fecha_servicio, tiempo_estimado_horas, folio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('cliente_id'), data.get('contacto_nombre'), data.get('vendedor_id'),
                data.get('titulo'), data.get('valor_estimado', 0), data.get('moneda', 'USD'),
                data.get('etapa', 'Prospecto'), data.get('fecha_cierre_estimada'),
                data.get('producto_servicio'), data.get('notas'), data.get('email'),
                data.get('firma_vendedor'), data.get('mensaje_envio'),
                data.get('tipo_deal', 'venta'), data.get('fecha_servicio'), data.get('tiempo_estimado_horas'),
                folio
            ))
        return cursor.lastrowid

def update_deal(deal_id, data):
    """Update an existing deal - only updates fields provided in data dict"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Build dynamic UPDATE query - only update fields that are provided
        fields = []
        values = []
        
        # List of all possible fields
        possible_fields = [
            'cliente_id', 'contacto_nombre', 'vendedor_id', 'titulo', 'valor_estimado',
            'moneda', 'etapa', 'fecha_cierre_estimada', 'producto_servicio', 'notas',
            'email', 'firma_vendedor', 'mensaje_envio', 'tipo_deal', 'fecha_servicio', 'tiempo_estimado_horas',
            'oc_cliente_file_path', 'folio'
        ]
        
        # Only add fields that are actually in the data dict
        for field in possible_fields:
            if field in data:
                fields.append(f'{field}=?')
                values.append(data[field])
        
        # Always update updated_at
        fields.append('updated_at=CURRENT_TIMESTAMP')
        
        if not fields:
            return False  # No fields to update
        
        query = f'UPDATE crm_deals SET {", ".join(fields)} WHERE id=?'
        values.append(deal_id)
        
        cursor.execute(query, values)
        return cursor.rowcount > 0

def update_deal_stage(deal_id, new_stage):
    """Update only the stage of a deal (for drag-drop)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE crm_deals SET etapa=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
        ''', (new_stage, deal_id))
        return cursor.rowcount > 0

def update_deal_email_fields(deal_id, firma_vendedor=None, mensaje_envio=None):
    """Update only email-related fields of a deal (firma and mensaje)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE crm_deals 
            SET firma_vendedor=?, mensaje_envio=?, updated_at=CURRENT_TIMESTAMP 
            WHERE id=?
        ''', (firma_vendedor, mensaje_envio, deal_id))
        return cursor.rowcount > 0

def delete_deal(deal_id):
    """Delete a deal and its related data"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM crm_activities WHERE deal_id = ?", (deal_id,))
        cursor.execute("DELETE FROM crm_deal_cotizaciones WHERE deal_id = ?", (deal_id,))
        cursor.execute("DELETE FROM crm_deal_pis WHERE deal_id = ?", (deal_id,))
        cursor.execute("DELETE FROM crm_deal_reportes WHERE deal_id = ?", (deal_id,))
        cursor.execute("DELETE FROM crm_deals WHERE id = ?", (deal_id,))
        return cursor.rowcount > 0

# ========== Modular Messaging Functions ==========

def get_deal_message(deal_id, module, context):
    """
    Get the effective message subject, body, and signature for a deal/module/context.
    Prioritizes Overrides > Templates > Hardcoded Fallbacks.
    """
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Try to get Deal Override
        cursor.execute('''
            SELECT subject, body, signature 
            FROM crm_deal_message_overrides 
            WHERE deal_id = ? AND module = ? AND context = ?
        ''', (deal_id, module, context))
        override = cursor.fetchone()
        
        if override:
            return {
                'subject': override['subject'],
                'body': override['body'],
                'signature': override['signature']
            }
            
        # 2. Try to get Module Template
        cursor.execute('''
            SELECT subject_tpl, body_tpl, signature_tpl 
            FROM crm_module_templates 
            WHERE module = ? AND context = ?
        ''', (module, context))
        template = cursor.fetchone()
        
        if template:
            return {
                'subject': template['subject_tpl'],
                'body': template['body_tpl'],
                'signature': template['signature_tpl']
            }
            
        # 3. Fallback (should be covered by templates migration, but for safety)
        # Return generic structure
        return {
            'subject': None,
            'body': '',
            'signature': None
        }

def save_deal_message(deal_id, module, context, body, signature=None, subject=None):
    """
    Save or update a deal-specific message override.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO crm_deal_message_overrides (deal_id, module, context, body, signature, subject)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(deal_id, module, context) DO UPDATE SET
                body = excluded.body,
                signature = excluded.signature,
                subject = excluded.subject,
                updated_at = CURRENT_TIMESTAMP
        ''', (deal_id, module, context, body, signature, subject))
        conn.commit()
        return True

def get_module_template(module, context):
    """Get the default template for a module/context"""
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT subject_tpl, body_tpl, signature_tpl 
            FROM crm_module_templates 
            WHERE module = ? AND context = ?
        ''', (module, context))
        row = cursor.fetchone()
        return dict(row) if row else None

# ========== Service Deal Equipment Functions ==========

def add_equipo_to_deal(deal_id, tipo_equipo, modelo='', serie='', descripcion_servicio='', detalles_adicionales='', orden=0):
    """Add equipment to a service deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO crm_deal_equipos (deal_id, tipo_equipo, modelo, serie, descripcion_servicio, detalles_adicionales, orden)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (deal_id, tipo_equipo, modelo, serie, descripcion_servicio, detalles_adicionales, orden))
        return cursor.lastrowid

def get_equipos_by_deal(deal_id):
    """Get all equipment for a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM crm_deal_equipos 
            WHERE deal_id = ? 
            ORDER BY orden ASC, id ASC
        ''', (deal_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_equipo_deal_by_id(equipo_id):
    """Get specific equipment by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM crm_deal_equipos WHERE id = ?', (equipo_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# ========== Service Timer Functions ==========

def start_service_timer(deal_id, tecnico_id):
    """Start timer for a service deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if timer already started
        cursor.execute('''
            SELECT * FROM crm_service_timer 
            WHERE deal_id = ? AND fecha_fin IS NULL
        ''', (deal_id,))
        existing = cursor.fetchone()
        if existing:
            return None  # Timer already started
        
        cursor.execute('''
            INSERT INTO crm_service_timer (deal_id, tecnico_inicio_id, fecha_inicio)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (deal_id, tecnico_id))
        conn.commit()
        return cursor.lastrowid

def stop_service_timer(deal_id, tecnico_id):
    """Stop timer for a service deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Get active timer
        cursor.execute('''
            SELECT * FROM crm_service_timer 
            WHERE deal_id = ? AND fecha_fin IS NULL
        ''', (deal_id,))
        timer = cursor.fetchone()
        if not timer:
            return None  # No active timer
        
        # Only the technician who started can stop
        if timer['tecnico_inicio_id'] != tecnico_id:
            return False  # Not authorized
        
        # Calculate time difference
        fecha_inicio = datetime.fromisoformat(timer['fecha_inicio'].replace('Z', '+00:00'))
        fecha_fin = datetime.now()
        tiempo_segundos = int((fecha_fin - fecha_inicio).total_seconds())
        
        cursor.execute('''
            UPDATE crm_service_timer 
            SET tecnico_fin_id = ?, fecha_fin = CURRENT_TIMESTAMP, tiempo_segundos = ?
            WHERE id = ?
        ''', (tecnico_id, tiempo_segundos, timer['id']))
        conn.commit()
        return True

def get_service_timer(deal_id):
    """Get timer status for a service deal"""
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, 
                   u1.nombre as tecnico_inicio_nombre,
                   u2.nombre as tecnico_fin_nombre
            FROM crm_service_timer t
            LEFT JOIN users u1 ON t.tecnico_inicio_id = u1.id
            LEFT JOIN users u2 ON t.tecnico_fin_id = u2.id
            WHERE t.deal_id = ?
            ORDER BY t.created_at DESC
            LIMIT 1
        ''', (deal_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def is_timer_active(deal_id):
    """Check if timer is currently active for a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM crm_service_timer 
            WHERE deal_id = ? AND fecha_fin IS NULL
        ''', (deal_id,))
        return cursor.fetchone()[0] > 0

def can_user_control_timer(deal_id, user_id):
    """Check if user can start/stop timer"""
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Check if timer is active
        cursor.execute('''
            SELECT * FROM crm_service_timer 
            WHERE deal_id = ? AND fecha_fin IS NULL
        ''', (deal_id,))
        timer = cursor.fetchone()
        
        if not timer:
            # No active timer - any assigned technician can start
            cursor.execute('''
                SELECT COUNT(*) FROM crm_deal_tecnicos 
                WHERE deal_id = ? AND tecnico_id = ?
            ''', (deal_id, user_id))
            return cursor.fetchone()[0] > 0
        
        # Timer is active - only the one who started can stop
        return timer['tecnico_inicio_id'] == user_id

def update_equipo_deal(equipo_id, **kwargs):
    """Update equipment details"""
    with get_db() as conn:
        cursor = conn.cursor()
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['tipo_equipo', 'modelo', 'serie', 'descripcion_servicio', 'detalles_adicionales', 'orden']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if fields:
            values.append(equipo_id)
            cursor.execute(f"UPDATE crm_deal_equipos SET {', '.join(fields)} WHERE id = ?", values)
            return cursor.rowcount > 0
        return False

def delete_equipo_deal(equipo_id):
    """Delete equipment from deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM crm_deal_equipos WHERE id = ?", (equipo_id,))
        return cursor.rowcount > 0

# ========== Service Deal Technician Functions ==========

def assign_tecnico_to_deal(deal_id, tecnico_id, asignado_por, puntos=0):
    """Assign a technician to a service deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO crm_deal_tecnicos (deal_id, tecnico_id, asignado_por, puntos)
                VALUES (?, ?, ?, ?)
            ''', (deal_id, tecnico_id, asignado_por, puntos))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Already assigned
            return None

def remove_tecnico_from_deal(deal_id, tecnico_id):
    """Remove technician from a service deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM crm_deal_tecnicos 
            WHERE deal_id = ? AND tecnico_id = ?
        ''', (deal_id, tecnico_id))
        return cursor.rowcount > 0

def update_tecnico_puntos(deal_id, tecnico_id, puntos):
    """Update technician points for a service"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE crm_deal_tecnicos 
            SET puntos = ? 
            WHERE deal_id = ? AND tecnico_id = ?
        ''', (puntos, deal_id, tecnico_id))
        return cursor.rowcount > 0

def get_tecnicos_by_deal(deal_id):
    """Get all technicians assigned to a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dt.*, u.nombre, u.username, u.email
            FROM crm_deal_tecnicos dt
            JOIN users u ON dt.tecnico_id = u.id
            WHERE dt.deal_id = ?
            ORDER BY dt.asignado_at ASC
        ''', (deal_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_deals_by_tecnico(tecnico_id, tipo_deal='servicio', etapa=None):
    """Get all deals assigned to a technician"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT d.*, c.nombre as cliente_nombre, dt.puntos
            FROM crm_deals d
            JOIN crm_deal_tecnicos dt ON d.id = dt.deal_id
            LEFT JOIN clients c ON d.cliente_id = c.id
            WHERE dt.tecnico_id = ? AND d.tipo_deal = ?
        '''
        params = [tecnico_id, tipo_deal]
        
        if etapa:
            query += " AND d.etapa = ?"
            params.append(etapa)
        
        query += " ORDER BY d.fecha_servicio ASC, d.created_at DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def is_tecnico_assigned_to_deal(deal_id, tecnico_id):
    """Check if a technician is assigned to a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM crm_deal_tecnicos 
            WHERE deal_id = ? AND tecnico_id = ?
        ''', (deal_id, tecnico_id))
        return cursor.fetchone()['count'] > 0


# ==================== Equipment Photos & Comments ====================

def add_equipo_foto(equipo_id, foto_data, descripcion='', uploaded_by=None, orden=0):
    """Add photo to equipment (max 10 photos)"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Check current photo count
        cursor.execute('SELECT COUNT(*) as count FROM crm_deal_equipo_fotos WHERE equipo_id = ?', (equipo_id,))
        count = cursor.fetchone()['count']
        if count >= 10:
            return None  # Max 10 photos
        
        cursor.execute('''
            INSERT INTO crm_deal_equipo_fotos (equipo_id, foto_data, descripcion, uploaded_by, orden)
            VALUES (?, ?, ?, ?, ?)
        ''', (equipo_id, foto_data, descripcion, uploaded_by, orden))
        return cursor.lastrowid

def get_equipo_fotos(equipo_id):
    """Get all photos for an equipment"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, u.nombre as uploaded_by_name
            FROM crm_deal_equipo_fotos f
            LEFT JOIN users u ON f.uploaded_by = u.id
            WHERE f.equipo_id = ?
            ORDER BY f.orden, f.uploaded_at
        ''', (equipo_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_equipo_foto(foto_id):
    """Delete equipment photo"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM crm_deal_equipo_fotos WHERE id = ?', (foto_id,))
        return cursor.rowcount > 0

def add_equipo_comentario(equipo_id, user_id, mensaje, imagen_data=None):
    """Add comment to equipment (chat-style)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO crm_deal_equipo_comentarios (equipo_id, user_id, mensaje, imagen_data)
            VALUES (?, ?, ?, ?)
        ''', (equipo_id, user_id, mensaje, imagen_data))
        return cursor.lastrowid

def get_equipo_comentarios(equipo_id):
    """Get all comments for an equipment"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, u.nombre as user_nombre, u.prefijo
            FROM crm_deal_equipo_comentarios c
            JOIN users u ON c.user_id = u.id
            WHERE c.equipo_id = ?
            ORDER BY c.created_at ASC
        ''', (equipo_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_equipo_comentario(comentario_id):
    """Delete equipment comment (admin only in frontend)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM crm_deal_equipo_comentarios WHERE id = ?', (comentario_id,))
        return cursor.rowcount > 0


def get_all_deals():
    """Get all deals with client and vendor info"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, c.nombre as cliente_nombre, u.nombre as vendedor_nombre
            FROM crm_deals d
            LEFT JOIN clients c ON d.cliente_id = c.id
            LEFT JOIN users u ON d.vendedor_id = u.id
            ORDER BY d.updated_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

def get_deals_by_client_id(cliente_id):
    """Get all deals for a specific client"""
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, c.nombre as cliente_nombre
            FROM crm_deals d
            LEFT JOIN clients c ON d.cliente_id = c.id
            WHERE d.cliente_id = ?
            ORDER BY d.created_at DESC
        ''', (cliente_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_deals_by_vendor(vendor_id):
    """Get deals filtered by assigned vendor"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, c.nombre as cliente_nombre, u.nombre as vendedor_nombre
            FROM crm_deals d
            LEFT JOIN clients c ON d.cliente_id = c.id
            LEFT JOIN users u ON d.vendedor_id = u.id
            WHERE d.vendedor_id = ?
            ORDER BY d.updated_at DESC
        ''', (vendor_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_pending_activities_by_vendor(vendor_id):
    """Get pending activities for deals owned by a vendor"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, d.titulo as deal_titulo, c.nombre as cliente_nombre
            FROM crm_activities a
            JOIN crm_deals d ON a.deal_id = d.id
            LEFT JOIN clients c ON d.cliente_id = c.id
            WHERE a.completada = 0 AND d.vendedor_id = ?
            ORDER BY a.fecha_programada ASC
        ''', (vendor_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_deal_by_id(deal_id):
    """Get a single deal with all details"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, c.nombre as cliente_nombre, u.nombre as vendedor_nombre
            FROM crm_deals d
            LEFT JOIN clients c ON d.cliente_id = c.id
            LEFT JOIN users u ON d.vendedor_id = u.id
            WHERE d.id = ?
        ''', (deal_id,))
        row = cursor.fetchone()
        if row:
            deal = dict(row)
            # Get linked cotizaciones
            cursor.execute('''
                SELECT cot.id, cot.folio, cot.fecha, cot.total, cot.moneda
                FROM cotizaciones cot
                JOIN crm_deal_cotizaciones dc ON cot.id = dc.cotizacion_id
                WHERE dc.deal_id = ?
            ''', (deal_id,))
            deal['cotizaciones'] = [dict(r) for r in cursor.fetchall()]
            
            # Get linked PIs (New)
            try:
                cursor.execute('''
                    SELECT pi.id, pi.folio, pi.fecha, pi.total, pi.moneda
                    FROM pis pi
                    JOIN crm_deal_pis dp ON pi.id = dp.pi_id
                    WHERE dp.deal_id = ?
                ''', (deal_id,))
                deal['pis'] = [dict(r) for r in cursor.fetchall()]
            except:
                deal['pis'] = []

            # Get linked reportes
            cursor.execute('''
                SELECT reporte_folio FROM crm_deal_reportes WHERE deal_id = ?
            ''', (deal_id,))
            deal['reportes'] = [r['reporte_folio'] for r in cursor.fetchall()]
            # Get activities
            cursor.execute('''
                SELECT * FROM crm_activities WHERE deal_id = ? ORDER BY fecha_programada ASC
            ''', (deal_id,))
            deal['actividades'] = [dict(r) for r in cursor.fetchall()]
            return deal
        return None

def get_deals_by_stage(stage):
    """Get deals filtered by stage (case-insensitive)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, c.nombre as cliente_nombre
            FROM crm_deals d
            LEFT JOIN clients c ON d.cliente_id = c.id
            WHERE LOWER(TRIM(d.etapa)) = LOWER(TRIM(?))
            ORDER BY d.updated_at DESC
        ''', (stage,))
        return [dict(row) for row in cursor.fetchall()]

# Activity functions
def create_activity(deal_id, data):
    """Create a new activity for a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO crm_activities (deal_id, tipo, descripcion, fecha_programada)
            VALUES (?, ?, ?, ?)
        ''', (deal_id, data.get('tipo'), data.get('descripcion'), data.get('fecha_programada')))
        return cursor.lastrowid

def get_deal_activities(deal_id):
    """Get all activities for a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM crm_activities WHERE deal_id = ? ORDER BY fecha_programada ASC
        ''', (deal_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_pending_activities():
    """Get all pending activities across all deals"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, d.titulo as deal_titulo, c.nombre as cliente_nombre
            FROM crm_activities a
            JOIN crm_deals d ON a.deal_id = d.id
            LEFT JOIN clients c ON d.cliente_id = c.id
            WHERE a.completada = 0
            ORDER BY a.fecha_programada ASC
        ''')
        return [dict(row) for row in cursor.fetchall()]

def mark_activity_complete(activity_id, completed=True):
    """Mark an activity as complete or incomplete"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE crm_activities SET completada = ? WHERE id = ?
        ''', (1 if completed else 0, activity_id))
        return cursor.rowcount > 0

def delete_activity(activity_id):
    """Delete an activity"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM crm_activities WHERE id = ?", (activity_id,))
        return cursor.rowcount > 0

# Linking functions
def link_cotizacion_to_deal(deal_id, cotizacion_id):
    """Link a cotizacion to a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO crm_deal_cotizaciones (deal_id, cotizacion_id) VALUES (?, ?)
            ''', (deal_id, cotizacion_id))
            return True
        except:
            return False

def unlink_cotizacion_from_deal(deal_id, cotizacion_id):
    """Unlink a cotizacion from a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM crm_deal_cotizaciones WHERE deal_id = ? AND cotizacion_id = ?
        ''', (deal_id, cotizacion_id))
        return cursor.rowcount > 0

def link_reporte_to_deal(deal_id, folio):
    """Link a report to a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Ensure table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_deal_reportes (
                deal_id INTEGER NOT NULL,
                reporte_folio TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (deal_id, reporte_folio),
                FOREIGN KEY (deal_id) REFERENCES crm_deals(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO crm_deal_reportes (deal_id, reporte_folio) VALUES (?, ?)
            ''', (deal_id, folio))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error linking report to deal: {e}")
            return False

def unlink_reporte_from_deal(deal_id, folio):
    """Unlink a report from a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM crm_deal_reportes WHERE deal_id = ? AND reporte_folio = ?
        ''', (deal_id, folio))
        return cursor.rowcount > 0

def get_reports_by_deal(deal_id):
    """Get all reports (drafts and sent) linked to a deal"""
    import json
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, ensure the table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_deal_reportes (
                deal_id INTEGER NOT NULL,
                reporte_folio TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (deal_id, reporte_folio),
                FOREIGN KEY (deal_id) REFERENCES crm_deals(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        
        # Get report folios from crm_deal_reportes table
        cursor.execute('''
            SELECT reporte_folio FROM crm_deal_reportes WHERE deal_id = ?
        ''', (deal_id,))
        folios_from_link = [row['reporte_folio'] for row in cursor.fetchall()]
        
        # Also get reports directly from draft_reports and reports tables by deal_id
        # IMPORTANT: Only get reports that were explicitly generated for this deal
        # (have deal_id saved in the database)
        try:
            cursor.execute('SELECT folio FROM draft_reports WHERE deal_id = ?', (deal_id,))
            folios_from_drafts = [row['folio'] for row in cursor.fetchall()]
        except Exception as e:
            # Column might not exist
            print(f"Error querying draft_reports by deal_id: {e}")
            folios_from_drafts = []
        
        try:
            cursor.execute('SELECT folio FROM reports WHERE deal_id = ?', (deal_id,))
            folios_from_reports = [row['folio'] for row in cursor.fetchall()]
        except Exception as e:
            # Column might not exist
            print(f"Error querying reports by deal_id: {e}")
            folios_from_reports = []
        
        # Combine all folios and remove duplicates
        # ONLY include reports that were explicitly linked to this deal
        all_folios = list(set(folios_from_link + folios_from_drafts + folios_from_reports))
        
        # If we found reports in draft_reports or reports that aren't in crm_deal_reportes,
        # link them now
        for folio in all_folios:
            if folio not in folios_from_link:
                link_reporte_to_deal(deal_id, folio)
        
        folios = all_folios
        
        reports = []
        for folio in folios:
            # Try to get from draft_reports first
            cursor.execute('SELECT * FROM draft_reports WHERE folio = ?', (folio,))
            draft = cursor.fetchone()
            
            if draft:
                # It's a draft
                try:
                    form_data = json.loads(draft['form_data']) if isinstance(draft['form_data'], str) else draft['form_data']
                    report = {
                        'folio': folio,
                        'status': draft['status'] or 'draft',
                        'created_at': draft['created_at'],
                        'updated_at': draft['updated_at'],
                        'fecha': form_data.get('fecha', ''),
                        'cliente': form_data.get('cliente', ''),
                        'tipo_servicio': form_data.get('tipo_servicio', '')
                    }
                except:
                    report = {
                        'folio': folio,
                        'status': draft['status'] or 'draft',
                        'created_at': draft['created_at'],
                        'updated_at': draft['updated_at'],
                        'fecha': '',
                        'cliente': '',
                        'tipo_servicio': ''
                    }
            else:
                # Try to get from reports table
                cursor.execute('SELECT * FROM reports WHERE folio = ?', (folio,))
                report_row = cursor.fetchone()
                if report_row:
                    report = {
                        'folio': folio,
                        'status': 'sent',
                        'created_at': report_row['created_at'],
                        'updated_at': report_row['created_at'],
                        'fecha': report_row['fecha'],
                        'cliente': report_row['cliente'],
                        'tipo_servicio': report_row['tipo_servicio']
                    }
                else:
                    # Report not found, skip
                    continue
            
            reports.append(report)
        
        # Sort by updated_at or created_at (most recent first)
        reports.sort(key=lambda x: x.get('updated_at') or x.get('created_at') or '', reverse=True)
        
        return reports

# ==================== CRM PUESTO STAGES FUNCTIONS ====================

def get_stages_by_puesto(puesto):
    """Get CRM stages for a specific puesto (case-insensitive)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM crm_puesto_stages 
            WHERE LOWER(TRIM(puesto)) = LOWER(TRIM(?))
            ORDER BY orden ASC
        ''', (puesto,))
        return [dict(row) for row in cursor.fetchall()]

def get_all_puesto_stages():
    """Get all puesto stages grouped by puesto"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM crm_puesto_stages 
            ORDER BY puesto, orden ASC
        ''')
        return [dict(row) for row in cursor.fetchall()]

def add_puesto_stage(puesto, stage_name, orden=0, color='#6c757d'):
    """Add a new stage for a puesto"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO crm_puesto_stages (puesto, stage_name, orden, color)
                VALUES (?, ?, ?, ?)
            ''', (puesto, stage_name, orden, color))
            return cursor.lastrowid
    except:
        return None

def update_puesto_stage(stage_id, stage_name=None, orden=None, color=None):
    """Update a puesto stage"""
    with get_db() as conn:
        cursor = conn.cursor()
        updates = []
        params = []
        if stage_name is not None:
            updates.append("stage_name = ?")
            params.append(stage_name)
        if orden is not None:
            updates.append("orden = ?")
            params.append(orden)
        if color is not None:
            updates.append("color = ?")
            params.append(color)
        if updates:
            params.append(stage_id)
            cursor.execute(f"UPDATE crm_puesto_stages SET {', '.join(updates)} WHERE id = ?", params)
            return cursor.rowcount > 0
        return False

def delete_puesto_stage(stage_id):
    """Delete a puesto stage"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM crm_puesto_stages WHERE id = ?", (stage_id,))
        return cursor.rowcount > 0

def get_stage_triggers():
    """Get all stage triggers"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_stage_triggers WHERE is_active = 1")
        return [dict(row) for row in cursor.fetchall()]

def get_trigger_for_stage(source_puesto, source_stage):
    """Get trigger for a specific stage change (case-insensitive)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM crm_stage_triggers 
            WHERE LOWER(TRIM(source_puesto)) = LOWER(TRIM(?)) 
            AND LOWER(TRIM(source_stage)) = LOWER(TRIM(?)) 
            AND is_active = 1
        ''', (source_puesto, source_stage))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_deals_by_puesto(puesto):
    """Get deals visible to a specific puesto (deals in their stages) - case-insensitive"""
    stages = get_stages_by_puesto(puesto)
    stage_names = [s['stage_name'] for s in stages]
    
    if not stage_names:
        return []
    
    with get_db() as conn:
        cursor = conn.cursor()
        # Build case-insensitive OR conditions
        conditions = ' OR '.join([f'LOWER(TRIM(d.etapa)) = LOWER(TRIM(?))' for _ in stage_names])
        query = f'''
            SELECT d.*, c.nombre as cliente_nombre, u.nombre as vendedor_nombre
            FROM crm_deals d
            LEFT JOIN clients c ON d.cliente_id = c.id
            LEFT JOIN users u ON d.vendedor_id = u.id
            WHERE {conditions}
            ORDER BY d.updated_at DESC
        '''
        cursor.execute(query, stage_names)
        return [dict(row) for row in cursor.fetchall()]

def get_pending_activities_by_vendor(vendor_id):
    """Get pending activities for a specific vendor"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, d.titulo as deal_titulo, c.nombre as cliente_nombre
            FROM crm_activities a
            JOIN crm_deals d ON a.deal_id = d.id
            LEFT JOIN clients c ON d.cliente_id = c.id
            WHERE a.completada = 0 AND d.vendedor_id = ?
            ORDER BY a.fecha_programada ASC
        ''', (vendor_id,))
        return [dict(row) for row in cursor.fetchall()]

# ==================== PUESTOS (POSITIONS) FUNCTIONS ====================

def get_all_puestos():
    """Get all puestos from database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM puestos ORDER BY nombre")
        return [dict(row) for row in cursor.fetchall()]

def get_puesto_by_id(puesto_id):
    """Get puesto by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM puestos WHERE id = ?", (puesto_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_puesto_by_nombre(nombre):
    """Get puesto by nombre"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM puestos WHERE nombre = ?", (nombre,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_puesto(nombre, permisos='formulario'):
    """Create a new puesto"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO puestos (nombre, permisos)
                VALUES (?, ?)
            ''', (nombre, permisos))
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # Already exists

def update_puesto(puesto_id, nombre=None, permisos=None):
    """Update puesto information"""
    with get_db() as conn:
        cursor = conn.cursor()
        updates = []
        params = []
        if nombre is not None:
            updates.append("nombre = ?")
            params.append(nombre)
        if permisos is not None:
            updates.append("permisos = ?")
            params.append(permisos)
        if updates:
            params.append(puesto_id)
            try:
                cursor.execute(f"UPDATE puestos SET {', '.join(updates)} WHERE id = ?", params)
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False
        return False

def delete_puesto(puesto_id):
    """Delete a puesto by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if any users have this puesto
        cursor.execute("SELECT nombre FROM puestos WHERE id = ?", (puesto_id,))
        row = cursor.fetchone()
        if row:
            puesto_nombre = row['nombre']
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE puesto = ?", (puesto_nombre,))
            if cursor.fetchone()['count'] > 0:
                return False  # Can't delete if users have this puesto
        cursor.execute("DELETE FROM puestos WHERE id = ?", (puesto_id,))
        return cursor.rowcount > 0

# ==================== FINANZAS (FINANCES) FUNCTIONS ====================

def preview_next_factura_folio():
    """Preview next invoice folio number without incrementing"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO folios (prefijo, ultimo_numero)
            VALUES ('IA', 0)
        ''')
        cursor.execute("SELECT ultimo_numero FROM folios WHERE prefijo = 'IA'")
        row = cursor.fetchone()
        numero = (row['ultimo_numero'] if row else 0) + 1
        return f"IA-{numero:05d}"

def get_next_factura_folio():
    """Generate next invoice folio number (increments counter)"""
    return get_next_folio("IA")

def create_factura(numero_factura, fecha_emision, cliente_nombre, subtotal, iva_porcentaje=16, 
                   cliente_id=None, cliente_rfc=None, cotizacion_id=None, moneda='MXN',
                   fecha_vencimiento=None, metodo_pago=None, notas=None, partidas=None):
    """Create a new invoice with line items"""
    iva_monto = subtotal * (iva_porcentaje / 100)
    total = subtotal + iva_monto
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO facturas (
                numero_factura, fecha_emision, cliente_id, cliente_nombre, cliente_rfc,
                cotizacion_id, subtotal, iva_porcentaje, iva_monto, total, moneda,
                fecha_vencimiento, metodo_pago, notas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (numero_factura, fecha_emision, cliente_id, cliente_nombre, cliente_rfc,
              cotizacion_id, subtotal, iva_porcentaje, iva_monto, total, moneda,
              fecha_vencimiento, metodo_pago, notas))
        factura_id = cursor.lastrowid
        
        # Add line items if provided
        if partidas:
            for i, partida in enumerate(partidas):
                cursor.execute('''
                    INSERT INTO factura_partidas (
                        factura_id, codigo, descripcion, cantidad, unidad, precio_unitario, subtotal, orden
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (factura_id, partida.get('codigo', 'N/A'), partida['descripcion'], 
                      partida.get('cantidad', 1), partida.get('unidad', 'SER'),
                      partida['precio_unitario'], partida['subtotal'], i))
        
        conn.commit()
        return factura_id

def add_factura_partida(factura_id, descripcion, cantidad, precio_unitario):
    """Add a line item to an invoice"""
    subtotal = cantidad * precio_unitario
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO factura_partidas (factura_id, descripcion, cantidad, precio_unitario, subtotal)
            VALUES (?, ?, ?, ?, ?)
        ''', (factura_id, descripcion, cantidad, precio_unitario, subtotal))
        return cursor.lastrowid

def get_factura_partidas(factura_id):
    """Get all line items for an invoice"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM factura_partidas WHERE factura_id = ? ORDER BY orden, id
        ''', (factura_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_factura_partida(partida_id):
    """Delete a line item"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM factura_partidas WHERE id = ?", (partida_id,))
        return cursor.rowcount > 0

def get_all_facturas():
    """Get all invoices"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, 
                   COALESCE(SUM(p.monto), 0) as monto_pagado,
                   (f.total - COALESCE(SUM(p.monto), 0)) as saldo_pendiente,
                   CASE 
                       WHEN f.fecha_vencimiento IS NOT NULL 
                       THEN julianday('now') - julianday(f.fecha_vencimiento)
                       ELSE NULL
                   END as dias_vencido
            FROM facturas f
            LEFT JOIN pagos p ON f.id = p.factura_id
            GROUP BY f.id
            ORDER BY f.fecha_emision DESC
        ''')
        rows = [dict(row) for row in cursor.fetchall()]
        
        # Convert dias_vencido to integer
        for row in rows:
            if row.get('dias_vencido') is not None:
                row['dias_vencido'] = int(row['dias_vencido'])
        
        return rows

def get_factura_by_id(factura_id):
    """Get invoice by ID with payments and line items"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, 
                   COALESCE(SUM(p.monto), 0) as monto_pagado,
                   (f.total - COALESCE(SUM(p.monto), 0)) as saldo_pendiente
            FROM facturas f
            LEFT JOIN pagos p ON f.id = p.factura_id
            WHERE f.id = ?
            GROUP BY f.id
        ''', (factura_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        factura = dict(row)
        
        # Get all payments for this invoice
        cursor.execute('''
            SELECT * FROM pagos WHERE factura_id = ? ORDER BY fecha_pago DESC
        ''', (factura_id,))
        factura['pagos'] = [dict(p) for p in cursor.fetchall()]
        
        # Get all line items for this invoice
        factura['partidas'] = get_factura_partidas(factura_id)
        
        return factura

def get_cotizaciones_disponibles(cliente_id=None):
    """Get cotizaciones that are not yet invoiced, optionally filtered by client"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if cliente_id:
            cursor.execute('''
                SELECT c.* FROM cotizaciones c
                LEFT JOIN facturas f ON c.id = f.cotizacion_id
                WHERE f.id IS NULL AND c.cliente_id = ?
                ORDER BY c.fecha DESC
            ''', (cliente_id,))
        else:
            cursor.execute('''
                SELECT c.* FROM cotizaciones c
                LEFT JOIN facturas f ON c.id = f.cotizacion_id
                WHERE f.id IS NULL
                ORDER BY c.fecha DESC
            ''')
        
        return [dict(row) for row in cursor.fetchall()]

def update_factura_estado(factura_id):
    """Update invoice payment status based on payments"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.total, COALESCE(SUM(p.monto), 0) as monto_pagado
            FROM facturas f
            LEFT JOIN pagos p ON f.id = p.factura_id
            WHERE f.id = ?
            GROUP BY f.id
        ''', (factura_id,))
        row = cursor.fetchone()
        
        if row:
            total = row['total']
            pagado = row['monto_pagado']
            
            if pagado >= total:
                estado = 'Pagada'
            elif pagado > 0:
                estado = 'Parcial'
            else:
                estado = 'Pendiente'
            
            cursor.execute('''
                UPDATE facturas SET estado_pago = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (estado, factura_id))
            conn.commit()

def create_pago(factura_id, fecha_pago, monto, metodo=None, referencia=None, notas=None):
    """Register a payment for an invoice"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pagos (factura_id, fecha_pago, monto, metodo, referencia, notas)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (factura_id, fecha_pago, monto, metodo, referencia, notas))
        pago_id = cursor.lastrowid
        conn.commit()
        
        # Update invoice status
        update_factura_estado(factura_id)
        
        return pago_id

def delete_pago(pago_id):
    """Delete a payment"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Get factura_id before deleting
        cursor.execute("SELECT factura_id FROM pagos WHERE id = ?", (pago_id,))
        row = cursor.fetchone()
        if row:
            factura_id = row['factura_id']
            cursor.execute("DELETE FROM pagos WHERE id = ?", (pago_id,))
            conn.commit()
            # Update invoice status
            update_factura_estado(factura_id)
            return True
    return False

# ==================== DEAL MESSAGES FUNCTIONS (FASE 1) ====================

def create_deal_message(deal_id, user_id, mensaje):
    """Create a new message in a deal"""
    import re
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO deal_messages (deal_id, user_id, mensaje)
            VALUES (?, ?, ?)
        ''', (deal_id, user_id, mensaje))
        message_id = cursor.lastrowid
        
        # Detect mentions @username and create notifications
        mentions = re.findall(r'@(\w+)', mensaje)
        if mentions:
            # Get user details of the sender
            cursor.execute("SELECT username, nombre FROM users WHERE id = ?", (user_id,))
            sender = cursor.fetchone()
            sender_name = sender['nombre'] if sender else 'Usuario'
            
            # Get deal details
            cursor.execute("SELECT titulo FROM crm_deals WHERE id = ?", (deal_id,))
            deal = cursor.fetchone()
            deal_title = deal['titulo'] if deal else f'Trato #{deal_id}'
            
            for username in mentions:
                # Find user by username
                cursor.execute("SELECT id FROM users WHERE username = ?", (username.lower(),))
                mentioned_user = cursor.fetchone()
                if mentioned_user:
                    cursor.execute('''
                        INSERT INTO notifications (user_id, tipo, titulo, mensaje, deal_id, deal_message_id, leido)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                    ''', (
                        mentioned_user['id'],
                        'mencion',
                        f'Te mencionó {sender_name}',
                        f'En "{deal_title}": {mensaje[:100]}...',
                        deal_id,
                        message_id
                    ))
        
        conn.commit()
        return message_id

def get_deal_messages(deal_id):
    """Get all messages for a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dm.*, u.username, u.nombre
            FROM deal_messages dm
            LEFT JOIN users u ON dm.user_id = u.id
            WHERE dm.deal_id = ?
            ORDER BY dm.created_at ASC
        ''', (deal_id,))
        messages = [dict(row) for row in cursor.fetchall()]
        
        # Load attachments for each message
        for msg in messages:
            attachments = get_attachments('internal_message', msg['id'])
            msg['attachments'] = attachments
        
        return messages

def delete_deal_message(message_id):
    """Delete a message"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deal_messages WHERE id = ?", (message_id,))
        conn.commit()
        return cursor.rowcount > 0

# ==================== NOTIFICATIONS FUNCTIONS ====================

def get_user_notifications(user_id, leido=None, limit=50):
    """Get notifications for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT n.*, d.titulo as deal_titulo
            FROM notifications n
            LEFT JOIN crm_deals d ON n.deal_id = d.id
            WHERE n.user_id = ?
        '''
        params = [user_id]
        
        if leido is not None:
            query += " AND n.leido = ?"
            params.append(1 if leido else 0)
        
        query += " ORDER BY n.created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_unread_notification_count(user_id):
    """Get count of unread notifications for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM notifications
            WHERE user_id = ? AND leido = 0
        ''', (user_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE notifications
            SET leido = 1
            WHERE id = ?
        ''', (notification_id,))
        conn.commit()
        return cursor.rowcount > 0

def mark_all_notifications_read(user_id):
    """Mark all notifications as read for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE notifications
            SET leido = 1
            WHERE user_id = ? AND leido = 0
        ''', (user_id,))
        conn.commit()
        return cursor.rowcount > 0

def delete_notification(notification_id):
    """Delete a notification"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
        conn.commit()
        return cursor.rowcount > 0

def create_notification(user_id, tipo, titulo, mensaje, deal_id=None, deal_message_id=None, ocu_id=None):
    """Create a new notification"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, tipo, titulo, mensaje, deal_id, deal_message_id, ocu_id, leido, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
        ''', (user_id, tipo, titulo, mensaje, deal_id, deal_message_id, ocu_id))
        conn.commit()
        return cursor.lastrowid

# ==================== EMAIL HISTORY FUNCTIONS (FASE 2) ====================

def normalize_subject(subject):
    """Normalize email subject by removing repeated Re:/Fwd: prefixes (RFC-compliant)
    
    Args:
        subject: Raw subject line (e.g., "Re: Re: Re: Cotización #T-00036")
    
    Returns:
        Normalized subject (e.g., "Cotización #T-00036")
    """
    if not subject:
        return ''
    import re
    # Remove all Re:/Fwd:/FW: prefixes (case-insensitive) and extra spaces
    normalized = re.sub(r'^((?:Re|Fwd|Rv|Fw|Aw|Resend|RE|FW|FWD)(?:\[\d+\])?:\s*)+', '', subject, flags=re.IGNORECASE).strip()
    # Clean up multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized

def create_email_record(deal_id, direccion, tipo, asunto, cuerpo, remitente, destinatario, 
                        adjuntos=None, cotizacion_id=None, estado='enviado', cc=None, thread_id=None, message_id=None,
                        in_reply_to=None, references=None, subject_raw=None, subject_norm=None, 
                        thread_root_id=None, direction=None, provider=None):
    """Create a new email history record
    
    Args:
        deal_id: ID del trato relacionado
        direccion: 'salida' o 'entrada'
        tipo: 'cotizacion', 'respuesta', 'seguimiento', etc.
        asunto: Asunto del email
        cuerpo: Cuerpo del email
        remitente: Email del remitente
        destinatario: Email del destinatario (puede ser múltiples separados por coma)
        adjuntos: JSON string con lista de adjuntos
        cotizacion_id: ID de cotización si aplica
        estado: 'enviado', 'fallido', 'leido', etc.
        cc: Emails en copia (separados por coma)
        thread_id: ID del hilo de conversación (basado en asunto)
        message_id: ID único del mensaje para evitar duplicados
    """
    # Normalize subject for threading
    if not subject_raw:
        subject_raw = asunto
    if not subject_norm:
        subject_norm = normalize_subject(asunto)
    
    # Generate thread_id from normalized subject if not provided
    if not thread_id:
        thread_id = subject_norm[:100]  # First 100 chars as thread identifier
    
    # Determine direction and provider
    if not direction:
        direction = 'inbound' if direccion == 'entrada' else 'outbound'
    if not provider:
        provider = 'outlook_imap'  # Default, can be overridden
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO email_history 
            (deal_id, direccion, tipo, asunto, cuerpo, remitente, destinatario, cc, thread_id, message_id, 
             adjuntos, cotizacion_id, estado, in_reply_to, "references", subject_raw, subject_norm, 
             thread_root_id, direction, provider)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (deal_id, direccion, tipo, asunto, cuerpo, remitente, destinatario, cc, thread_id, message_id, 
              adjuntos, cotizacion_id, estado, in_reply_to, references, subject_raw, subject_norm, 
              thread_root_id, direction, provider))
        email_id = cursor.lastrowid
        
        # FASE 3: Notificaciones automáticas para correos entrantes
        if direccion == 'entrada' and deal_id:
            try:
                # Obtener el vendedor del trato para notificarle
                cursor.execute("SELECT vendedor_id, titulo FROM crm_deals WHERE id = ?", (deal_id,))
                deal_row = cursor.fetchone()
                
                if deal_row and deal_row['vendedor_id']:
                    vendedor_id = deal_row['vendedor_id']
                    deal_titulo = deal_row['titulo'] or "Trato sin título"
                    
                    # Preparar mensaje de notificación
                    sender_display = remitente
                    if '<' in (remitente or ''):
                        import re
                        match = re.search(r'^(.*?)\s*<', remitente)
                        if match:
                            sender_display = match.group(1).strip()
                            if not sender_display: # Si estaba vacío antes del <
                                sender_display = remitente
                    
                    notif_titulo = f"Nuevo correo de {sender_display}"
                    notif_mensaje = f"En {deal_titulo}: {asunto}"
                    
                    # Crear notificación
                    cursor.execute('''
                        INSERT INTO notifications (user_id, tipo, titulo, mensaje, deal_id, leido)
                        VALUES (?, 'email', ?, ?, ?, 0)
                    ''', (vendedor_id, notif_titulo, notif_mensaje, deal_id))
                    
            except Exception as e:
                print(f"Error creando notificación de email: {e}")
        
        conn.commit()
        return email_id

def get_deal_thread_subjects(deal_id):
    """Get all unique thread subjects for a deal (to find related responses)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT thread_id FROM email_history 
            WHERE deal_id = ? AND thread_id IS NOT NULL
        ''', (deal_id,))
        return [row['thread_id'] for row in cursor.fetchall()]

def email_exists_by_message_id(message_id):
    """Check if email already exists by message_id"""
    if not message_id:
        return False
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM email_history WHERE message_id = ?', (message_id,))
        return cursor.fetchone() is not None

def get_deal_emails(deal_id):
    """Get all emails for a specific deal - FILTRO ESTRICTO por deal_id (no mezclar tratos)
    
    OPTIMIZACIÓN: Usar DISTINCT o GROUP BY para evitar duplicados por JOIN
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar qué columnas RFC existen en la tabla (SQLite-safe)
        cursor.execute("PRAGMA table_info(email_history)")
        existing_columns = {row['name'] for row in cursor.fetchall()}
        
        # Columnas base (siempre existen)
        base_columns = [
            'eh.id', 'eh.deal_id', 'eh.direccion', 'eh.tipo', 'eh.asunto', 'eh.cuerpo',
            'eh.remitente', 'eh.destinatario', 'eh.cc', 'eh.thread_id', 'eh.message_id',
            'eh.adjuntos', 'eh.cotizacion_id', 'eh.estado', 'eh.created_at'
        ]
        
        # Columnas RFC (pueden no existir en bases de datos antiguas)
        rfc_columns = []
        if 'in_reply_to' in existing_columns:
            rfc_columns.append('eh.in_reply_to')
        if 'references' in existing_columns:
            rfc_columns.append('eh."references"')  # Escapar palabra reservada
        if 'subject_raw' in existing_columns:
            rfc_columns.append('eh.subject_raw')
        if 'subject_norm' in existing_columns:
            rfc_columns.append('eh.subject_norm')
        if 'thread_root_id' in existing_columns:
            rfc_columns.append('eh.thread_root_id')
        if 'direction' in existing_columns:
            rfc_columns.append('eh.direction')
        if 'provider' in existing_columns:
            rfc_columns.append('eh.provider')
        
        # Construir SELECT dinámicamente
        all_columns = base_columns + rfc_columns + ['c.folio as cotizacion_folio']
        select_clause = 'SELECT DISTINCT ' + ', '.join(all_columns)
        
        query = f'''
            {select_clause}
            FROM email_history eh
            LEFT JOIN cotizaciones c ON eh.cotizacion_id = c.id
            WHERE eh.deal_id = ?
            ORDER BY eh.created_at DESC
        '''
        
        cursor.execute(query, (deal_id,))
        results = [dict(row) for row in cursor.fetchall()]
        
        # Asegurar que las columnas RFC tengan valores por defecto si no existen
        for result in results:
            if 'in_reply_to' not in result:
                result['in_reply_to'] = None
            if 'references' not in result:
                result['references'] = None
            if 'subject_raw' not in result:
                result['subject_raw'] = result.get('asunto')
            if 'subject_norm' not in result:
                # Normalizar subject si no existe (usar función del mismo módulo)
                result['subject_norm'] = normalize_subject(result.get('asunto', ''))
            if 'thread_root_id' not in result:
                result['thread_root_id'] = result.get('thread_id')
            if 'direction' not in result:
                result['direction'] = 'inbound' if result.get('direccion') == 'entrada' else 'outbound'
            if 'provider' not in result:
                result['provider'] = 'outlook_imap'
        
        # Verificación adicional: asegurar que todos los resultados pertenecen al deal_id correcto
        filtered_results = [r for r in results if r.get('deal_id') == deal_id]
        if len(filtered_results) != len(results):
            print(f"⚠️ ADVERTENCIA: Se filtraron {len(results) - len(filtered_results)} emails con deal_id incorrecto")
        
        # DEDUPLICACIÓN ADICIONAL: Por si acaso hay duplicados por el JOIN
        seen_ids = set()
        unique_results = []
        for r in filtered_results:
            email_id = r.get('id')
            if email_id and email_id in seen_ids:
                continue  # Skip duplicate
            if email_id:
                seen_ids.add(email_id)
            unique_results.append(r)
        
        if len(unique_results) != len(filtered_results):
            print(f"⚠️ ADVERTENCIA: Se eliminaron {len(filtered_results) - len(unique_results)} emails duplicados en get_deal_emails")
        
        return unique_results

def get_client_emails(cliente_id):
    """Get all emails for a specific client across all deals"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT eh.*, d.titulo as deal_titulo, c.folio as cotizacion_folio
            FROM email_history eh
            LEFT JOIN crm_deals d ON eh.deal_id = d.id
            LEFT JOIN cotizaciones c ON eh.cotizacion_id = c.id
            WHERE d.cliente_id = ?
            ORDER BY eh.created_at DESC
        ''', (cliente_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_email_by_id(email_id):
    """Get a specific email record"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT eh.*, d.titulo as deal_titulo, c.folio as cotizacion_folio
            FROM email_history eh
            LEFT JOIN crm_deals d ON eh.deal_id = d.id
            LEFT JOIN cotizaciones c ON eh.cotizacion_id = c.id
            WHERE eh.id = ?
        ''', (email_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def find_email_by_message_id(message_id, deal_id=None):
    """
    Find an email by its Message-ID to get cotizacion_id/factura_id for threading.
    
    Args:
        message_id: The Message-ID header from the email
        deal_id: Optional deal_id to filter results (recommended for accuracy)
        
    Returns:
        Dict with email data including cotizacion_id, factura_id, thread_id, etc.
        None if not found
    """
    if not message_id:
        return None
        
    # Clean message_id (remove < > if present)
    clean_msg_id = message_id.strip('<>').strip()
    if not clean_msg_id:
        return None
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Search with optional deal_id filter for accuracy
        if deal_id:
            cursor.execute('''
                SELECT id, deal_id, cotizacion_id, thread_id, asunto, message_id
                FROM email_history
                WHERE deal_id = ? AND (
                    message_id = ? OR 
                    message_id = ? OR
                    message_id LIKE ? OR
                    message_id LIKE ?
                )
                LIMIT 1
            ''', (deal_id, clean_msg_id, f'<{clean_msg_id}>', f'%{clean_msg_id}%', f'%<{clean_msg_id}>%'))
        else:
            cursor.execute('''
                SELECT id, deal_id, cotizacion_id, thread_id, asunto, message_id
                FROM email_history
                WHERE message_id = ? OR 
                      message_id = ? OR
                      message_id LIKE ? OR
                      message_id LIKE ?
                LIMIT 1
            ''', (clean_msg_id, f'<{clean_msg_id}>', f'%{clean_msg_id}%', f'%<{clean_msg_id}>%'))
        
        row = cursor.fetchone()
        return dict(row) if row else None

def update_email_status(email_id, estado):
    """Update email status (ej: 'leido', 'respondido')"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE email_history
            SET estado = ?
            WHERE id = ?
        ''', (estado, email_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_email_record(email_id):
    """Delete an email record"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_history WHERE id = ?", (email_id,))
        conn.commit()
        return cursor.rowcount > 0

# ==================== EMAIL DRAFTS (BORRADORES) ====================

def save_email_draft(deal_id, tipo_documento, documento_id, mensaje, asunto=None, adjuntos=None, created_by=None):
    """Save or update email draft for a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if draft exists
        cursor.execute('''
            SELECT id FROM email_drafts 
            WHERE deal_id = ? AND tipo_documento = ? AND documento_id = ?
        ''', (deal_id, tipo_documento, documento_id))
        existing = cursor.fetchone()
        
        import json
        adjuntos_json = json.dumps(adjuntos) if adjuntos else None
        
        if existing:
            # Update existing draft
            cursor.execute('''
                UPDATE email_drafts 
                SET mensaje = ?, asunto = ?, adjuntos = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (mensaje, asunto, adjuntos_json, existing['id']))
            draft_id = existing['id']
        else:
            # Create new draft
            cursor.execute('''
                INSERT INTO email_drafts (deal_id, tipo_documento, documento_id, mensaje, asunto, adjuntos, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (deal_id, tipo_documento, documento_id, mensaje, asunto, adjuntos_json, created_by))
            draft_id = cursor.lastrowid
        
        conn.commit()
        return draft_id

def get_email_draft(deal_id, tipo_documento, documento_id):
    """Get email draft for a deal and document type"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM email_drafts 
            WHERE deal_id = ? AND tipo_documento = ? AND documento_id = ?
        ''', (deal_id, tipo_documento, documento_id))
        row = cursor.fetchone()
        if row:
            draft = dict(row)
            # Parse adjuntos JSON
            if draft.get('adjuntos'):
                import json
                try:
                    draft['adjuntos'] = json.loads(draft['adjuntos'])
                except:
                    draft['adjuntos'] = []
            else:
                draft['adjuntos'] = []
            return draft
        return None

def delete_email_draft(deal_id, tipo_documento, documento_id):
    """Delete email draft"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM email_drafts 
            WHERE deal_id = ? AND tipo_documento = ? AND documento_id = ?
        ''', (deal_id, tipo_documento, documento_id))
        conn.commit()
        return cursor.rowcount > 0

def save_first_email_draft(deal_id, to, cc=None, subject=None, body=None, auto_send_email=1):
    """Save first email draft for a deal (before sending quotation)"""
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if draft exists
        cursor.execute('SELECT id FROM first_email_drafts WHERE deal_id = ?', (deal_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute('''
                UPDATE first_email_drafts 
                SET to_email=?, cc=?, subject=?, body=?, auto_send_email=?, updated_at=CURRENT_TIMESTAMP
                WHERE deal_id = ?
            ''', (to, cc, subject, body, auto_send_email, deal_id))
            draft_id = existing['id']
        else:
            # Create new
            cursor.execute('''
                INSERT INTO first_email_drafts (deal_id, to_email, cc, subject, body, auto_send_email)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (deal_id, to, cc, subject, body, auto_send_email))
            draft_id = cursor.lastrowid
        
        # Also update auto_send_email in crm_deals
        cursor.execute('UPDATE crm_deals SET auto_send_email = ? WHERE id = ?', (auto_send_email, deal_id))
        
        conn.commit()
        return draft_id

def get_first_email_draft(deal_id):
    """Get first email draft for a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM first_email_drafts WHERE deal_id = ?', (deal_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_first_email_draft(deal_id):
    """Delete first email draft"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM first_email_drafts WHERE deal_id = ?', (deal_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_deal_email_drafts(deal_id):
    """Get all email drafts for a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM email_drafts 
            WHERE deal_id = ?
            ORDER BY updated_at DESC
        ''', (deal_id,))
        drafts = []
        import json
        for row in cursor.fetchall():
            draft = dict(row)
            if draft.get('adjuntos'):
                try:
                    draft['adjuntos'] = json.loads(draft['adjuntos'])
                except:
                    draft['adjuntos'] = []
            else:
                draft['adjuntos'] = []
            drafts.append(draft)
        return drafts

# ==================== EMAIL TEMPLATES AND MODULE MESSAGES FUNCTIONS ====================

def get_email_template(module, template_type):
    """Get default email template for a module and type (mensaje or firma)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM email_templates 
            WHERE module = ? AND template_type = ? AND is_active = 1
            ORDER BY id DESC LIMIT 1
        ''', (module, template_type))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_email_templates(module=None):
    """Get all email templates, optionally filtered by module"""
    with get_db() as conn:
        cursor = conn.cursor()
        if module:
            cursor.execute('''
                SELECT * FROM email_templates 
                WHERE module = ? AND is_active = 1
                ORDER BY module, template_type
            ''', (module,))
        else:
            cursor.execute('''
                SELECT * FROM email_templates 
                WHERE is_active = 1
                ORDER BY module, template_type
            ''')
        return [dict(row) for row in cursor.fetchall()]

def create_or_update_email_template(module, template_type, default_content, description=None):
    """Create or update an email template"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO email_templates (module, template_type, default_content, description, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(module, template_type) 
            DO UPDATE SET 
                default_content = excluded.default_content,
                description = excluded.description,
                updated_at = CURRENT_TIMESTAMP
        ''', (module, template_type, default_content, description))
        conn.commit()
        return cursor.lastrowid

def get_deal_email_message(deal_id, module):
    """Get personalized email message and signature for a deal and module"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM deal_email_messages 
            WHERE deal_id = ? AND module = ?
        ''', (deal_id, module))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_or_update_deal_email_message(deal_id, module, mensaje=None, firma=None):
    """Create or update personalized email message and signature for a deal and module"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO deal_email_messages (deal_id, module, mensaje, firma, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(deal_id, module) 
            DO UPDATE SET 
                mensaje = COALESCE(excluded.mensaje, mensaje),
                firma = COALESCE(excluded.firma, firma),
                updated_at = CURRENT_TIMESTAMP
        ''', (deal_id, module, mensaje, firma))
        conn.commit()
        return cursor.lastrowid

def delete_deal_email_message(deal_id, module):
    """Delete personalized email message for a deal and module"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM deal_email_messages 
            WHERE deal_id = ? AND module = ?
        ''', (deal_id, module))
        conn.commit()
        return cursor.rowcount > 0

def get_deal_email_content(deal_id, module, content_type='mensaje'):
    """
    Get email content (mensaje or firma) for a deal and module.
    
    Priority:
    1. Personalized content from deal_email_messages
    2. Default template from email_templates
    3. Legacy content from crm_deals (for backward compatibility)
    4. Generic default
    
    Args:
        deal_id: ID del trato
        module: Módulo ('ventas', 'finanzas', 'compras', 'servicios', etc.)
        content_type: 'mensaje' o 'firma'
    
    Returns:
        String con el contenido del mensaje o firma
    """
    # Priority 1: Check for personalized content
    deal_message = get_deal_email_message(deal_id, module)
    if deal_message:
        content = deal_message.get(content_type)
        if content:
            return content
    
    # Priority 2: Get default template
    template = get_email_template(module, content_type)
    if template:
        return template.get('default_content', '')
    
    # Priority 3: Legacy compatibility (only for 'ventas' module)
    if module == 'ventas':
        deal = get_deal_by_id(deal_id)
        if deal:
            if content_type == 'mensaje':
                legacy_content = deal.get('mensaje_envio')
                if legacy_content:
                    return legacy_content
            elif content_type == 'firma':
                legacy_content = deal.get('firma_vendedor')
                if legacy_content:
                    return legacy_content
    
    # Priority 4: Generic defaults
    if content_type == 'mensaje':
        return 'Hola, buen día\n\nAdjunto encontrará el documento solicitado.\n\nQuedamos a sus órdenes.'
    else:  # firma
        return 'Saludos cordiales,'

def create_gasto(fecha, categoria, concepto, monto, proveedor=None, metodo_pago=None, 
                 referencia=None, notas=None):
    """Create a new expense"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO gastos (fecha, categoria, concepto, monto, proveedor, 
                                metodo_pago, referencia, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fecha, categoria, concepto, monto, proveedor, metodo_pago, referencia, notas))
        return cursor.lastrowid

def get_all_gastos():
    """Get all expenses"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gastos ORDER BY fecha DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_gastos_by_periodo(fecha_inicio, fecha_fin):
    """Get expenses by date range"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM gastos 
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC
        ''', (fecha_inicio, fecha_fin))
        return [dict(row) for row in cursor.fetchall()]

def get_flujo_caja(fecha_inicio, fecha_fin):
    """Get cash flow summary for a period"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get total income from payments
        cursor.execute('''
            SELECT COALESCE(SUM(monto), 0) as total_ingresos
            FROM pagos
            WHERE fecha_pago BETWEEN ? AND ?
        ''', (fecha_inicio, fecha_fin))
        ingresos = cursor.fetchone()['total_ingresos']
        
        # Get total expenses
        cursor.execute('''
            SELECT COALESCE(SUM(monto), 0) as total_gastos
            FROM gastos
            WHERE fecha BETWEEN ? AND ?
        ''', (fecha_inicio, fecha_fin))
        gastos = cursor.fetchone()['total_gastos']
        
        return {
            'ingresos': ingresos,
            'gastos': gastos,
            'balance': ingresos - gastos
        }

def get_cuentas_por_cobrar():
    """Get accounts receivable summary"""
    from datetime import datetime, date
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, 
                   COALESCE(SUM(p.monto), 0) as monto_pagado,
                   (f.total - COALESCE(SUM(p.monto), 0)) as saldo_pendiente,
                   CASE 
                       WHEN f.fecha_vencimiento IS NOT NULL 
                       THEN julianday('now') - julianday(f.fecha_vencimiento)
                       ELSE NULL
                   END as dias_vencido
            FROM facturas f
            LEFT JOIN pagos p ON f.id = p.factura_id
            WHERE f.estado_pago != 'Pagada'
            GROUP BY f.id
            ORDER BY f.fecha_vencimiento ASC
        ''')
        rows = [dict(row) for row in cursor.fetchall()]
        
        # Convert dias_vencido to integer
        for row in rows:
            if row.get('dias_vencido') is not None:
                row['dias_vencido'] = int(row['dias_vencido'])
        
        return rows

def get_dashboard_stats():
    """Get financial dashboard statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total por cobrar
        cursor.execute('''
            SELECT COALESCE(SUM(f.total - COALESCE(p.monto_pagado, 0)), 0) as total
            FROM facturas f
            LEFT JOIN (
                SELECT factura_id, SUM(monto) as monto_pagado 
                FROM pagos 
                GROUP BY factura_id
            ) p ON f.id = p.factura_id
            WHERE f.estado_pago != 'Pagada'
        ''')
        por_cobrar = cursor.fetchone()['total']
        
        # Facturas vencidas
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM facturas
            WHERE estado_pago != 'Pagada' 
            AND fecha_vencimiento < DATE('now')
        ''')
        facturas_vencidas = cursor.fetchone()['count']
        
        # Ingresos del mes
        cursor.execute('''
            SELECT COALESCE(SUM(monto), 0) as total
            FROM pagos
            WHERE strftime('%Y-%m', fecha_pago) = strftime('%Y-%m', 'now')
        ''')
        ingresos_mes = cursor.fetchone()['total']
        
        # Gastos del mes
        cursor.execute('''
            SELECT COALESCE(SUM(monto), 0) as total
            FROM gastos
            WHERE strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
        ''')
        gastos_mes = cursor.fetchone()['total']
        
        return {
            'por_cobrar': por_cobrar,
            'facturas_vencidas': facturas_vencidas,
            'ingresos_mes': ingresos_mes,
            'gastos_mes': gastos_mes,
            'balance_mes': ingresos_mes - gastos_mes
        }


# ==================== COMPRAS MODULE FUNCTIONS ====================



# ----- PROVEEDORES -----



def get_all_proveedores():

    """Get all suppliers ordered by name"""

    with get_db() as conn:

        cursor = conn.cursor()

        cursor.execute("SELECT * FROM proveedores ORDER BY nombre_empresa")

        return [dict(row) for row in cursor.fetchall()]



def get_proveedor_by_id(proveedor_id):

    """Get supplier by ID"""

    with get_db() as conn:

        cursor = conn.cursor()

        cursor.execute("SELECT * FROM proveedores WHERE id = ?", (proveedor_id,))

        row = cursor.fetchone()

        return dict(row) if row else None



def create_proveedor(data):

    """Create a new supplier"""

    with get_db() as conn:

        cursor = conn.cursor()

        cursor.execute('''

            INSERT INTO proveedores (nombre_empresa, contacto_nombre, telefono, email, direccion, rfc)

            VALUES (?, ?, ?, ?, ?, ?)

        ''', (

            data.get('nombre_empresa'), data.get('contacto_nombre'), 

            data.get('telefono'), data.get('email'), 

            data.get('direccion'), data.get('rfc')

        ))

        return cursor.lastrowid



def update_proveedor(proveedor_id, data):

    """Update supplier information"""

    with get_db() as conn:

        cursor = conn.cursor()

        cursor.execute('''

            UPDATE proveedores 

            SET nombre_empresa=?, contacto_nombre=?, telefono=?, email=?, direccion=?, rfc=?, updated_at=CURRENT_TIMESTAMP

            WHERE id=?

        ''', (

            data.get('nombre_empresa'), data.get('contacto_nombre'), 

            data.get('telefono'), data.get('email'), 

            data.get('direccion'), data.get('rfc'), proveedor_id

        ))

        return cursor.rowcount > 0



def delete_proveedor(proveedor_id):

    """Delete supplier"""

    with get_db() as conn:

        cursor = conn.cursor()

        # Should check constraints before delete? Sqlite handles FK?

        cursor.execute("DELETE FROM proveedores WHERE id = ?", (proveedor_id,))

        return cursor.rowcount > 0



# ----- COMPRAS (Purchase Orders) -----



def get_all_compras():

    """Get all purchase orders"""

    with get_db() as conn:

        cursor = conn.cursor()

        cursor.execute('''

            SELECT c.*, p.nombre_empresa as proveedor_nombre, u.nombre as creador_nombre 

            FROM compras c

            LEFT JOIN proveedores p ON c.proveedor_id = p.id

            LEFT JOIN users u ON c.created_by = u.id

            ORDER BY c.created_at DESC

        ''')

        return [dict(row) for row in cursor.fetchall()]



def get_compra_by_id(compra_id):

    """Get purchase order with items"""

    with get_db() as conn:

        cursor = conn.cursor()

        

        # Get master

        cursor.execute('''

            SELECT c.*, p.nombre_empresa as proveedor_nombre, 

                   p.direccion as proveedor_direccion, p.rfc as proveedor_rfc,

                   p.contacto_nombre as proveedor_contacto, p.telefono as proveedor_telefono, p.email as proveedor_email,

                   u.nombre as creador_nombre

            FROM compras c

            LEFT JOIN proveedores p ON c.proveedor_id = p.id

            LEFT JOIN users u ON c.created_by = u.id

            WHERE c.id = ?

        ''', (compra_id,))

        row = cursor.fetchone()

        if not row:

            return None

        

        compra = dict(row)

        

        # Get items

        cursor.execute("SELECT * FROM compra_items WHERE compra_id = ? ORDER BY linea ASC", (compra_id,))

        items = [dict(item) for item in cursor.fetchall()]

        compra['items'] = items

        

        return compra



def get_next_compra_folio():

    """Generate next PO folio (OC-XXXX)"""

    with get_db() as conn:

        cursor = conn.cursor()

        cursor.execute("SELECT folio FROM compras ORDER BY id DESC LIMIT 1")

        last = cursor.fetchone()

        if last and last['folio']:

            try:

                num = int(last['folio'].split('-')[1])

                return f"OC-{num + 1:04d}"

            except:

                return "OC-0001"

        return "OC-0001"



def create_compra(data, items, user_id):

    """Create new Purchase Order"""

    try:

        with get_db() as conn:

            cursor = conn.cursor()

            

            folio = data.get('folio') or get_next_compra_folio()

            

            cursor.execute('''

                INSERT INTO compras (

                    folio, proveedor_id, fecha_emision, fecha_entrega_estimada, estado,

                    moneda, subtotal, iva, total, notas, created_by

                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ''', (

                folio, data.get('proveedor_id'), data.get('fecha_emision'), 

                data.get('fecha_entrega_estimada'), data.get('estado', 'Borrador'),

                data.get('moneda', 'MXN'), data.get('subtotal'), data.get('iva'), 

                data.get('total'), data.get('notas'), user_id

            ))

            

            compra_id = cursor.lastrowid

            

            # Insert items

            for item in items:

                cursor.execute('''
                    INSERT INTO compra_items (
                        compra_id, linea, numero_parte, descripcion, cantidad, unidad, precio_unitario, importe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    compra_id, item.get('linea'), item.get('numero_parte'), item.get('descripcion'),
                    item.get('cantidad'), item.get('unidad'), item.get('precio_unitario'), item.get('importe')
                ))

                

            return compra_id

    except Exception as e:
        print(f"Error creating compra: {e}")
        return None

def delete_compra(compra_id):
    """Delete Purchase Order"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM compras WHERE id = ?", (compra_id,))
            return True
    except Exception as e:
        print(f"Error deleting compra: {e}")
        return False



def update_compra(compra_id, data, items):

    """Update Purchase Order"""

    try:

        with get_db() as conn:

            cursor = conn.cursor()

            

            cursor.execute('''

                UPDATE compras SET

                    proveedor_id=?, fecha_emision=?, fecha_entrega_estimada=?, 

                    estado=?, moneda=?, subtotal=?, iva=?, total=?, notas=?, updated_at=CURRENT_TIMESTAMP

                WHERE id=?

            ''', (

                data.get('proveedor_id'), data.get('fecha_emision'), data.get('fecha_entrega_estimada'),

                data.get('estado'), data.get('moneda'), data.get('subtotal'), data.get('iva'),

                data.get('total'), data.get('notas'), compra_id

            ))

            

            # Rewrite items

            cursor.execute("DELETE FROM compra_items WHERE compra_id = ?", (compra_id,))

            

            for item in items:

                cursor.execute('''
                    INSERT INTO compra_items (
                        compra_id, linea, numero_parte, descripcion, cantidad, unidad, precio_unitario, importe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    compra_id, item.get('linea'), item.get('numero_parte'), item.get('descripcion'),
                    item.get('cantidad'), item.get('unidad'), item.get('precio_unitario'), item.get('importe')
                ))

            

            return True

    except Exception as e:

        print(f"Error updating compra: {e}")

        return False


# ==================== GESTION DE PI (PROFORMA INVOICES) FUNCTIONS ====================

def get_next_pi_folio():
    """Generate next PI folio (PI-00001)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT folio FROM pis ORDER BY id DESC LIMIT 1")
        last = cursor.fetchone()
        
        if last and last['folio']:
            try:
                num = int(last['folio'].split('-')[1])
                return f"PI-{num + 1:05d}"
            except:
                return "PI-00001"
        return "PI-00001"

def create_pi(data, items):
    """Create a new Proforma Invoice"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO pis (
                    folio, fecha, proveedor_id, proveedor_nombre, atencion_a, referencia,
                    orden_compra_id, cotizacion_id, cliente_id, cliente_nombre, moneda, tipo_cambio, tiempo_entrega, condiciones_pago,
                    notas, subtotal, iva_porcentaje, iva_monto, total, created_by, solicitado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('folio'), data.get('fecha'), data.get('proveedor_id'), data.get('proveedor_nombre'),
                data.get('atencion_a'), data.get('referencia'), data.get('orden_compra_id'), data.get('cotizacion_id'),
                data.get('cliente_id'), data.get('cliente_nombre'),
                data.get('moneda', 'USD'), data.get('tipo_cambio', 1.0),
                data.get('tiempo_entrega'), data.get('condiciones_pago'), data.get('notas'),
                data.get('subtotal', 0), data.get('iva_porcentaje', 16), data.get('iva_monto', 0),
                data.get('total', 0), data.get('created_by'), data.get('solicitado_por')
            ))
            
            pi_id = cursor.lastrowid
            
            for item in items:
                cursor.execute('''
                    INSERT INTO pi_items (
                        pi_id, linea, cantidad, unidad, numero_parte, descripcion,
                        estatus, tiempo_entrega_item, precio_unitario, importe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pi_id, item.get('linea'), item.get('cantidad'), item.get('unidad'),
                    item.get('numero_parte'), item.get('descripcion'), item.get('estatus', 'Pendiente'),
                    item.get('tiempo_entrega_item'), item.get('precio_unitario'), item.get('importe')
                ))
            
            return pi_id
    except Exception as e:
        print(f"Error creating PI: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_pi_by_id(pi_id):
    """Get PI by ID with items"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pis WHERE id = ?", (pi_id,))
        row = cursor.fetchone()
        if not row: return None
        
        pi = dict(row)
        cursor.execute("SELECT * FROM pi_items WHERE pi_id = ? ORDER BY linea ASC", (pi_id,))
        pi['items'] = [dict(r) for r in cursor.fetchall()]
        return pi

def get_all_pis():
    """Get all PIs ordered by date desc with items"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pis ORDER BY created_at DESC")
        pis = [dict(r) for r in cursor.fetchall()]
        
        for pi in pis:
            cursor.execute("SELECT * FROM pi_items WHERE pi_id = ? ORDER BY linea ASC", (pi['id'],))
            pi['items'] = [dict(r) for r in cursor.fetchall()]
            # print(f"DEBUG: PI {pi['folio']} has {len(pi['items'])} items")
            
        return pis

def update_pi(pi_id, data, items):
    """Update PI and replace items"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE pis SET
                    fecha=?, proveedor_id=?, proveedor_nombre=?, atencion_a=?, referencia=?,
                    orden_compra_id=?, cotizacion_id=?, cliente_id=?, cliente_nombre=?, moneda=?, tipo_cambio=?, tiempo_entrega=?, condiciones_pago=?,
                    notas=?, subtotal=?, iva_porcentaje=?, iva_monto=?, total=?, solicitado_por=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (
                data.get('fecha'), data.get('proveedor_id'), data.get('proveedor_nombre'),
                data.get('atencion_a'), data.get('referencia'), data.get('orden_compra_id'), data.get('cotizacion_id'),
                data.get('cliente_id'), data.get('cliente_nombre'),
                data.get('moneda'), data.get('tipo_cambio'), data.get('tiempo_entrega'),
                data.get('condiciones_pago'), data.get('notas'), data.get('subtotal'),
                data.get('iva_porcentaje'), data.get('iva_monto'), data.get('total'),
                data.get('solicitado_por'), pi_id
            ))
            
            # Replace items (simpler than syncing)
            cursor.execute("DELETE FROM pi_items WHERE pi_id = ?", (pi_id,))
            
            for item in items:
                cursor.execute('''
                    INSERT INTO pi_items (
                        pi_id, linea, cantidad, unidad, numero_parte, descripcion,
                        estatus, tiempo_entrega_item, precio_unitario, importe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pi_id, item.get('linea'), item.get('cantidad'), item.get('unidad'),
                    item.get('numero_parte'), item.get('descripcion'), item.get('estatus', 'Pendiente'),
                    item.get('tiempo_entrega_item'), item.get('precio_unitario'), item.get('importe')
                ))
            return True
    except Exception as e:
        print(f"Error updating PI: {e}")
        return False

def delete_pi(pi_id):
    """Delete PI"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pi_items WHERE pi_id = ?", (pi_id,))
        cursor.execute("DELETE FROM pis WHERE id = ?", (pi_id,))
        return cursor.rowcount > 0

def get_cotizaciones_by_client(cliente_id):
    """Get all quotes for a specific client"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, folio, referencia, total, moneda, fecha
            FROM cotizaciones
            WHERE cliente_id = ?
            ORDER BY created_at DESC
        ''', (cliente_id,))
        return [dict(row) for row in cursor.fetchall()]

def update_pi_item_status(item_id, status):
    """Update status of a single PI item"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE pi_items SET estatus = ? WHERE id = ?", (status, item_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating item status: {e}")
        return False

def update_pi_items_bulk(pi_id, status):
    """Update status of ALL items in a PI"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE pi_items SET estatus = ? WHERE pi_id = ?", (status, pi_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error bulk updating items: {e}")
        return False


def link_pi_to_deal(deal_id, pi_id):
    """Link a PI to a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO crm_deal_pis (deal_id, pi_id) VALUES (?, ?)
            ''', (deal_id, pi_id))
            return True
        except:
            return False

# ========== Attachment Functions ==========

def create_attachment(owner_type, owner_id, filename, original_name, mime_type, size, file_path, created_by=None):
    """Create a new attachment record
    
    Args:
        owner_type: 'email' or 'internal_message'
        owner_id: ID of the email or message
        filename: Unique filename on disk
        original_name: Original filename from user
        mime_type: MIME type of the file
        size: File size in bytes
        file_path: Relative path to the file
        created_by: User ID who uploaded the file
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attachments (owner_type, owner_id, filename, original_name, mime_type, size, file_path, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (owner_type, owner_id, filename, original_name, mime_type, size, file_path, created_by))
        conn.commit()
        return cursor.lastrowid

def get_attachments(owner_type, owner_id):
    """Get all attachments for an owner (email or message)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, u.nombre as created_by_name
            FROM attachments a
            LEFT JOIN users u ON a.created_by = u.id
            WHERE a.owner_type = ? AND a.owner_id = ?
            ORDER BY a.created_at ASC
        ''', (owner_type, owner_id))
        return [dict(row) for row in cursor.fetchall()]

def get_attachment_by_id(attachment_id):
    """Get a specific attachment by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, u.nombre as created_by_name
            FROM attachments a
            LEFT JOIN users u ON a.created_by = u.id
            WHERE a.id = ?
        ''', (attachment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_attachment(attachment_id):
    """Delete an attachment record and optionally the file"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM attachments WHERE id = ?', (attachment_id,))
        row = cursor.fetchone()
        if row:
            file_path = row['file_path']
            cursor.execute('DELETE FROM attachments WHERE id = ?', (attachment_id,))
            conn.commit()
            # Optionally delete the file (commented for safety)
            # try:
            #     if os.path.exists(file_path):
            #         os.remove(file_path)
            # except:
            #     pass
            return True
        return False

def unlink_pi_from_deal(deal_id, pi_id):
    """Unlink a PI from a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM crm_deal_pis 
            WHERE deal_id = ? AND pi_id = ?
        ''', (deal_id, pi_id))
        return cursor.rowcount > 0

def get_pis_for_deal(deal_id):
    """Get all PIs linked to a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.* FROM pis p
            JOIN crm_deal_pis dp ON p.id = dp.pi_id
            WHERE dp.deal_id = ?
            ORDER BY p.created_at DESC
        ''', (deal_id,))
        return [dict(row) for row in cursor.fetchall()]

# ========== CRM Email Log Functions ==========

import re
import hashlib

def normalize_subject(subject):
    """Normalize email subject: remove RE:, FW:, FWD:, extra spaces"""
    if not subject:
        return ""
    # Remove common prefixes (case insensitive)
    normalized = re.sub(r'^(RE|FW|FWD):\s*', '', subject, flags=re.IGNORECASE)
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def calculate_thread_key(references_header, in_reply_to, subject_norm, cliente_email, deal_id):
    """Calculate stable thread_key for email threading"""
    # Priority 1: First Message-ID from references_header
    if references_header:
        # Extract first Message-ID from references (format: <message-id> <message-id> ...)
        match = re.search(r'<([^>]+)>', references_header)
        if match:
            return match.group(1)
    
    # Priority 2: in_reply_to
    if in_reply_to:
        # Remove < > if present
        thread_key = in_reply_to.strip('<>')
        return thread_key
    
    # Priority 3: Hash of subject_norm + cliente_email + deal_id
    combined = f"{subject_norm}|{cliente_email}|{deal_id}"
    return hashlib.md5(combined.encode()).hexdigest()

def save_crm_email_message(deal_id, direction, from_email, to_emails, cc_emails, 
                           subject_raw, message_id, in_reply_to, references_header,
                           date_ts, snippet, body_html=None, body_text=None, 
                           provider_uid=None):
    """Save email message to crm_email_messages with deduplication"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Normalize subject
        subject_norm = normalize_subject(subject_raw)
        
        # Get deal to get client email
        cursor.execute('SELECT email FROM crm_deals WHERE id = ?', (deal_id,))
        deal_row = cursor.fetchone()
        cliente_email = deal_row['email'] if deal_row else ''
        
        # Calculate thread_key
        thread_key = calculate_thread_key(references_header, in_reply_to, subject_norm, cliente_email, deal_id)
        
        # Deduplication: Check if message already exists
        # Key 1: message_id (if exists)
        if message_id:
            cursor.execute('SELECT id FROM crm_email_messages WHERE message_id = ?', (message_id,))
            if cursor.fetchone():
                return None  # Already exists
        
        # Key 2: provider_uid + date + from + subject_norm (if no message_id)
        if provider_uid:
            cursor.execute('''
                SELECT id FROM crm_email_messages 
                WHERE provider_uid = ? AND from_email = ? AND subject_norm = ? AND deal_id = ?
                AND ABS(JULIANDAY(date_ts) - JULIANDAY(?)) < 0.001
            ''', (provider_uid, from_email, subject_norm, deal_id, date_ts))
            if cursor.fetchone():
                return None  # Already exists
        
        # Insert new message
        cursor.execute('''
            INSERT INTO crm_email_messages 
            (deal_id, direction, from_email, to_emails, cc_emails, subject_raw, subject_norm,
             message_id, in_reply_to, references_header, thread_key, date_ts, snippet,
             body_html, body_text, provider_uid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (deal_id, direction, from_email, to_emails, cc_emails, subject_raw, subject_norm,
              message_id, in_reply_to, references_header, thread_key, date_ts, snippet,
              body_html, body_text, provider_uid))
        
        email_id = cursor.lastrowid
        conn.commit()
        return email_id

def get_crm_email_messages(deal_id):
    """Get all email messages for a deal, ordered by date_ts ASC"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crm_email_messages'")
            if not cursor.fetchone():
                print("⚠️ Tabla crm_email_messages no existe, retornando lista vacía")
                return []
            
            cursor.execute('''
                SELECT * FROM crm_email_messages
                WHERE deal_id = ?
                ORDER BY date_ts ASC
            ''', (deal_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ Error en get_crm_email_messages: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_crm_email_attachments(email_id):
    """Get all attachments for an email message"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM crm_email_attachments
            WHERE email_id = ?
            ORDER BY created_at ASC
        ''', (email_id,))
        return [dict(row) for row in cursor.fetchall()]

def save_crm_email_attachment(email_id, filename, mime=None, size=None, storage_path=None, hash_value=None):
    """Save email attachment"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO crm_email_attachments (email_id, filename, mime, size, storage_path, hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email_id, filename, mime, size, storage_path, hash_value))
        conn.commit()
        return cursor.lastrowid

def save_email_log(deal_id, direction='sent', to=None, cc=None, subject=None, body=None, message_id=None, status='sent', error=None, cotizacion_id=None, tipo='primer_correo', message_hash=None):
    """Save email log entry for tracing"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO email_log (deal_id, cotizacion_id, tipo, direction, to_email, cc, subject, body, message_id, message_hash, status, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (deal_id, cotizacion_id, tipo, direction, to, cc, subject, body, message_id, message_hash, status, error))
        conn.commit()
        return cursor.lastrowid

def check_email_already_sent(deal_id, cotizacion_id=None, tipo='primer_correo', message_hash=None):
    """Check if an email of this type has already been sent for this deal/cotizacion"""
    with get_db() as conn:
        cursor = conn.cursor()
        if message_hash:
            cursor.execute('''
                SELECT id, created_at, message_id FROM email_log
                WHERE deal_id = ? AND tipo = ? AND message_hash = ? AND status = 'sent'
                ORDER BY created_at DESC LIMIT 1
            ''', (deal_id, tipo, message_hash))
        elif cotizacion_id:
            cursor.execute('''
                SELECT id, created_at, message_id FROM email_log
                WHERE deal_id = ? AND cotizacion_id = ? AND tipo = ? AND status = 'sent'
                ORDER BY created_at DESC LIMIT 1
            ''', (deal_id, cotizacion_id, tipo))
        else:
            cursor.execute('''
                SELECT id, created_at, message_id FROM email_log
                WHERE deal_id = ? AND tipo = ? AND status = 'sent'
                ORDER BY created_at DESC LIMIT 1
            ''', (deal_id, tipo,))
        row = cursor.fetchone()
        return dict(row) if row else None

def mark_first_quote_email_sent(deal_id, method='erp'):
    """Mark that the first quote email has been sent for a deal"""
    from datetime import datetime
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE crm_deals 
            SET first_quote_email_sent = 1,
                first_quote_email_sent_at = ?,
                first_quote_email_sent_method = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), method, deal_id))
        conn.commit()

def is_first_quote_email_sent(deal_id):
    """Check if the first quote email has been sent for a deal"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT first_quote_email_sent FROM crm_deals WHERE id = ?
        ''', (deal_id,))
        row = cursor.fetchone()
        return bool(row and row[0] == 1) if row else False
