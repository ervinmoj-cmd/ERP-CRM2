#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migración: Actualizar thread_ids de emails existentes
para usar formato deal_{deal_id}_cot_{cotizacion_id}
"""

import sqlite3

DB_NAME = "inair_reportes.db"

def migrate_thread_ids():
    """Actualizar thread_ids existentes al nuevo formato"""
    
    print("\n" + "="*80)
    print("🔄 MIGRACIÓN DE THREAD_IDS - Emails en CRM")
    print("="*80 + "\n")
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 1. Actualizar emails de cotizaciones (que tienen cotizacion_id)
    print("📧 Paso 1: Actualizando thread_ids de emails de cotizaciones...")
    c.execute("""
        UPDATE email_history
        SET thread_id = 'deal_' || deal_id || '_cot_' || cotizacion_id
        WHERE cotizacion_id IS NOT NULL 
          AND deal_id IS NOT NULL
          AND cotizacion_id != ''
    """)
    
    updated_cot = c.rowcount
    print(f"   ✅ Actualizados {updated_cot} emails con cotizacion_id\n")
    
    # 2. Actualizar emails que son respuestas (tienen In-Reply-To)
    # Buscar el email padre y copiar su thread_id
    print("📧 Paso 2: Actualizando thread_ids de emails que son respuestas...")
    c.execute("""
        SELECT id, deal_id, in_reply_to, "references", asunto
        FROM email_history
        WHERE direccion = 'entrada' 
          AND (thread_id IS NULL OR thread_id NOT LIKE 'deal_%')
          AND (in_reply_to IS NOT NULL OR "references" IS NOT NULL)
    """)
    
    respuestas = c.fetchall()
    updated_resp = 0
    
    print(f"   Encontradas {len(respuestas)} respuestas para procesar...")
    
    for row in respuestas:
        email_id = row['id']
        deal_id = row['deal_id']
        in_reply_to = row['in_reply_to']
        references = row['references']
        
        # Buscar email padre por message_id
        msg_ids_to_check = []
        if in_reply_to:
            # Limpiar < >
            clean_id = in_reply_to.strip('<>').strip()
            msg_ids_to_check.append(clean_id)
        
        if references:
            # Extraer todos los message_ids de References
            import re
            refs_list = re.findall(r'<([^>]+)>', references)
            msg_ids_to_check.extend(refs_list)
        
        # Buscar el primer email padre que encontremos
        parent_thread_id = None
        for msg_id in msg_ids_to_check:
            c.execute("""
                SELECT thread_id, cotizacion_id
                FROM email_history
                WHERE deal_id = ? AND (
                    message_id = ? OR 
                    message_id LIKE ? OR
                    message_id LIKE ?
                )
                LIMIT 1
            """, (deal_id, msg_id, f'<{msg_id}>', f'%{msg_id}%'))
            
            parent = c.fetchone()
            if parent and parent['thread_id']:
                parent_thread_id = parent['thread_id']
                break
        
        if parent_thread_id:
            c.execute("""
                UPDATE email_history
                SET thread_id = ?
                WHERE id = ?
            """, (parent_thread_id, email_id))
            updated_resp += 1
    
    print(f"   ✅ Actualizadas {updated_resp} respuestas\n")
    
    # 3. Resumen final
    conn.commit()
    
    # Contar threads únicos después de la migración
    c.execute("""
        SELECT COUNT(DISTINCT thread_id) as count
        FROM email_history
        WHERE thread_id IS NOT NULL AND thread_id LIKE 'deal_%'
    """)
    
    new_threads = c.fetchone()['count']
    
    print("="*80)
    print("✅ MIGRACIÓN COMPLETADA")
    print("="*80)
    print(f"   - Emails de cotizaciones actualizados: {updated_cot}")
    print(f"   - Respuestas actualizadas: {updated_resp}")
    print(f"   - Total emails migrados: {updated_cot + updated_resp}")
    print(f"   - Threads únicos con nuevo formato: {new_threads}")
    print("="*80 + "\n")
    
    conn.close()

if __name__ == "__main__":
    try:
        migrate_thread_ids()
        print("✅ Migración exitosa. Puedes verificar en el CRM que los emails se agrupen correctamente.")
    except Exception as e:
        print(f"\n❌ ERROR durante la migración: {e}")
        import traceback
        traceback.print_exc()
