-- Create table for Module Templates (Defaults)
CREATE TABLE IF NOT EXISTS crm_module_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module TEXT NOT NULL,          -- e.g. 'Ventas', 'Finanzas', 'Servicios'
    context TEXT NOT NULL,         -- e.g. 'cotizacion', 'envio_factura', 'orden_servicio'
    subject_tpl TEXT,              -- Default subject template
    body_tpl TEXT NOT NULL,        -- Default body template
    signature_tpl TEXT,            -- Default signature template
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(module, context)
);

-- Create table for Deal Message Overrides (Per deal customization)
CREATE TABLE IF NOT EXISTS crm_deal_message_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id INTEGER NOT NULL,
    module TEXT NOT NULL,
    context TEXT NOT NULL,
    subject TEXT,                  -- Overridden subject
    body TEXT NOT NULL,            -- Overridden body
    signature TEXT,                -- Overridden signature
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(deal_id) REFERENCES crm_deals(id),
    UNIQUE(deal_id, module, context)
);

-- Populate default templates (Idempotent)
INSERT OR IGNORE INTO crm_module_templates (module, context, subject_tpl, body_tpl, signature_tpl) VALUES 
('Ventas', 'cotizacion', 'Cotización #{folio} - INAIR', 'Hola, buen día\n\nAdjunto encontrará la cotización solicitada.\n\nQuedamos a sus órdenes para cualquier duda o aclaración.', NULL),
('Finanzas', 'envio_factura', 'Factura #{folio} - INAIR', 'Buen día,\n\nAdjunto su factura correspondiente.\n\nFavor de confirmar recepción.', NULL),
('Finanzas', 'solicitud_factura', 'Solicitud de Facturación', 'Por favor generar factura para el siguiente pedido.', NULL),
('Servicios', 'orden_servicio', 'Orden de Servicio - {equipo}', 'Adjunto orden de servicio realizado.', NULL);

-- Migrate existing overrides from crm_deals to crm_deal_message_overrides
-- Context: Ventas / cotizacion
INSERT OR IGNORE INTO crm_deal_message_overrides (deal_id, module, context, body, signature)
SELECT 
    id, 
    'Ventas', 
    'cotizacion', 
    mensaje_envio, 
    firma_vendedor 
FROM crm_deals 
WHERE mensaje_envio IS NOT NULL OR firma_vendedor IS NOT NULL;
