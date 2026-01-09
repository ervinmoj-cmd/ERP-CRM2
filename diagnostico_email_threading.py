#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para analizar el threading de emails en el CRM.
Verifica si los emails enviados y recibidos están agrupados correctamente.
"""

import sqlite3
from datetime import datetime

DB_NAME = "inair_reportes.db"

def diagnosticar_email_threading():
    """Diagnosticar problemas de threading en emails del CRM"""
    
    print("\n" + "="*80)
    print("🔍 DIAGNÓSTICO DE EMAIL THREADING - CRM")
    print("="*80 + "\n")
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 1. Verificar estructura de la tabla
    print("📋 PASO 1: Verificando estructura de tabla email_history")
    print("-" * 80)
    
    c.execute("PRAGMA table_info(email_history)")
    columns = c.fetchall()
    column_names = [col['name'] for col in columns]
    
    print(f"✅ Tabla encontrada con {len(columns)} columnas:")
    important_cols = ['id', 'deal_id', 'thread_id', 'thread_root_id', 'message_id', 
                      'direccion', 'tipo', 'asunto', 'created_at']
    for col_name in important_cols:
        status = "✅" if col_name in column_names else "❌"
        print(f"   {status} {col_name}")
    
    print()
    
    # 2. Obtener estadísticas generales
    print("📊 PASO 2: Estadísticas Generales")
    print("-" * 80)
    
    c.execute("SELECT COUNT(*) as total FROM email_history")
    total_emails = c.fetchone()['total']
    print(f"Total de emails en BD: {total_emails}")
    
    c.execute("SELECT COUNT(*) as total FROM email_history WHERE direccion = 'entrada'")
    entrada_count = c.fetchone()['total']
    print(f"  - Entrada (recibidos): {entrada_count}")
    
    c.execute("SELECT COUNT(*) as total FROM email_history WHERE direccion = 'salida'")
    salida_count = c.fetchone()['total']
    print(f"  - Salida (enviados): {salida_count}")
    
    c.execute("SELECT COUNT(DISTINCT deal_id) as total FROM email_history WHERE deal_id IS NOT NULL")
    deals_con_emails = c.fetchone()['total']
    print(f"Tratos con emails: {deals_con_emails}")
    
    c.execute("SELECT COUNT(DISTINCT thread_id) as total FROM email_history WHERE thread_id IS NOT NULL")
    threads_unicos = c.fetchone()['total']
    print(f"Threads únicos (thread_id): {threads_unicos}")
    
    print()
    
    # 3. Buscar threads con emails tanto enviados como recibidos
    print("🔍 PASO 3: Buscando conversaciones (threads con enviados Y recibidos)")
    print("-" * 80)
    
    query = """
        SELECT 
            thread_id,
            deal_id,
            COUNT(*) as total_emails,
            SUM(CASE WHEN direccion = 'entrada' THEN 1 ELSE 0 END) as entrada_count,
            SUM(CASE WHEN direccion = 'salida' THEN 1 ELSE 0 END) as salida_count,
            MIN(asunto) as asunto_ejemplo
        FROM email_history
        WHERE thread_id IS NOT NULL
        GROUP BY thread_id, deal_id
        HAVING entrada_count > 0 AND salida_count > 0
        ORDER BY total_emails DESC
        LIMIT 10
    """
    
    c.execute(query)
    conversaciones = c.fetchall()
    
    if conversaciones:
        print(f"✅ Encontradas {len(conversaciones)} conversaciones (threads con enviados Y recibidos):\n")
        
        for idx, conv in enumerate(conversaciones, 1):
            print(f"  {idx}. Thread ID: {conv['thread_id'][:60]}...")
            print(f"     Deal: #{conv['deal_id']}")
            print(f"     Total: {conv['total_emails']} emails ({conv['salida_count']} enviados, {conv['entrada_count']} recibidos)")
            print(f"     Asunto: {conv['asunto_ejemplo'][:70]}...")
            print()
    else:
        print("⚠️ NO se encontraron conversaciones con enviados Y recibidos en el mismo thread")
        print("   Esto indica que los emails no se están agrupando correctamente.\n")
    
    # 4. Buscar cotizaciones enviadas recientemente
    print("📧 PASO 4: Analizando cotizaciones enviadas recientemente")
    print("-" * 80)
    
    query = """
        SELECT 
            id,
            deal_id,
            thread_id,
            thread_root_id,
            message_id,
            direccion,
            tipo,
            asunto,
            remitente,
            destinatario,
            created_at
        FROM email_history
        WHERE tipo = 'cotizacion' AND direccion = 'salida'
        ORDER BY created_at DESC
        LIMIT 5
    """
    
    c.execute(query)
    cotizaciones = c.fetchall()
    
    if cotizaciones:
        print(f"✅ Últimas {len(cotizaciones)} cotizaciones enviadas:\n")
        
        for idx, cot in enumerate(cotizaciones, 1):
            print(f"  {idx}. Cotización enviada")
            print(f"     Email ID: {cot['id']}")
            print(f"     Deal: #{cot['deal_id']}")
            print(f"     Asunto: {cot['asunto'][:70]}")
            print(f"     Thread ID: {cot['thread_id'][:50] if cot['thread_id'] else 'NO TIENE'}...")
            print(f"     Thread Root ID: {cot['thread_root_id'][:50] if cot['thread_root_id'] else 'NO TIENE'}...")
            print(f"     Message ID: {cot['message_id'][:50] if cot['message_id'] else 'NO TIENE'}...")
            print(f"     Para: {cot['destinatario']}")
            print(f"     Fecha: {cot['created_at']}")
            
            # Buscar respuestas a esta cotización
            if cot['thread_id']:
                c.execute("""
                    SELECT COUNT(*) as count 
                    FROM email_history 
                    WHERE deal_id = ? AND thread_id = ? AND direccion = 'entrada'
                """, (cot['deal_id'], cot['thread_id']))
                
                respuestas = c.fetchone()['count']
                if respuestas > 0:
                    print(f"     ✅ Tiene {respuestas} respuesta(s) en el mismo thread")
                else:
                    print(f"     ⚠️ No tiene respuestas en este thread (aún)")
            else:
                print(f"     ❌ NO TIENE thread_id asignado")
            
            print()
    else:
        print("⚠️ No se encontraron cotizaciones enviadas en el historial\n")
    
    # 5. Detectar problemas: emails del mismo deal con thread_id diferentes
    print("🔍 PASO 5: Detectando problemas - Emails del mismo deal con threads diferentes")
    print("-" * 80)
    
    query = """
        SELECT 
            deal_id,
            COUNT(DISTINCT thread_id) as thread_count,
            COUNT(*) as total_emails
        FROM email_history
        WHERE deal_id IS NOT NULL AND thread_id IS NOT NULL
        GROUP BY deal_id
        HAVING thread_count > 1
        ORDER BY total_emails DESC
        LIMIT 5
    """
    
    c.execute(query)
    deals_problema = c.fetchall()
    
    if deals_problema:
        print(f"⚠️ Encontrados {len(deals_problema)} deals con múltiples threads:\n")
        
        for deal in deals_problema:
            print(f"  Deal #{deal['deal_id']}: {deal['total_emails']} emails en {deal['thread_count']} threads diferentes")
            
            # Mostrar los threads de este deal
            c.execute("""
                SELECT 
                    thread_id,
                    COUNT(*) as email_count,
                    MIN(asunto) as asunto,
                    SUM(CASE WHEN direccion = 'entrada' THEN 1 ELSE 0 END) as entrada,
                    SUM(CASE WHEN direccion = 'salida' THEN 1 ELSE 0 END) as salida
                FROM email_history
                WHERE deal_id = ?
                GROUP BY thread_id
            """, (deal['deal_id'],))
            
            threads = c.fetchall()
            for t in threads:
                print(f"     - Thread: {t['thread_id'][:50]}...")
                print(f"       {t['email_count']} emails ({t['salida']} enviados, {t['entrada']} recibidos)")
                print(f"       Asunto: {t['asunto'][:60]}...")
            print()
    else:
        print("✅ No se detectaron deals con threads fragmentados\n")
    
    # 6. Verificar si hay emails sin thread_id
    print("🔍 PASO 6: Emails sin thread_id asignado")
    print("-" * 80)
    
    c.execute("SELECT COUNT(*) as count FROM email_history WHERE thread_id IS NULL OR thread_id = ''")
    sin_thread = c.fetchone()['count']
    
    if sin_thread > 0:
        print(f"⚠️ {sin_thread} emails SIN thread_id asignado")
        
        c.execute("""
            SELECT id, deal_id, direccion, tipo, asunto, created_at 
            FROM email_history 
            WHERE thread_id IS NULL OR thread_id = ''
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        emails_sin_thread = c.fetchall()
        print(f"\n   Ejemplos:")
        for email in emails_sin_thread:
            print(f"     - Email #{email['id']} (Deal #{email['deal_id']}): {email['asunto'][:50]}...")
        print()
    else:
        print("✅ Todos los emails tienen thread_id asignado\n")
    
    # RESUMEN FINAL
    print("\n" + "="*80)
    print("📋 RESUMEN DEL DIAGNÓSTICO")
    print("="*80)
    
    if conversaciones and len(conversaciones) > 0:
        print("✅ Hay conversaciones con threading correcto (enviados + recibidos agrupados)")
    else:
        print("❌ NO hay conversaciones completas - los emails no se están agrupando")
    
    if deals_problema and len(deals_problema) > 0:
        print(f"⚠️ {len(deals_problema)} deals tienen emails en múltiples threads (deberían estar en uno solo)")
    else:
        print("✅ No hay deals con threads fragmentados")
    
    if sin_thread > 0:
        print(f"⚠️ {sin_thread} emails sin thread_id (deben ser asignados)")
    else:
        print("✅ Todos los emails tienen thread_id")
    
    print("="*80 + "\n")
    
    conn.close()

if __name__ == "__main__":
    try:
        diagnosticar_email_threading()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
