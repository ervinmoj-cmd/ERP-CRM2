#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script simplificado para diagnosticar threading de emails"""

import sqlite3
import json

DB_NAME = "inair_reportes.db"

def main():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    resultados = {}
    
    # 1. Total de emails
    c.execute("SELECT COUNT(*) as total FROM email_history")
    resultados['total_emails'] = c.fetchone()['total']
    
    c.execute("SELECT COUNT(*) as total FROM email_history WHERE direccion = 'entrada'")
    resultados['entrada_count'] = c.fetchone()['total']
    
    c.execute("SELECT COUNT(*) as total FROM email_history WHERE direccion = 'salida'")
    resultados['salida_count'] = c.fetchone()['total']
    
    # 2. Threads unicos
    c.execute("SELECT COUNT(DISTINCT thread_id) as total FROM email_history WHERE thread_id IS NOT NULL AND thread_id != ''")
    resultados['threads_unicos'] = c.fetchone()['total']
    
    # 3. Conversaciones (threads con enviados Y recibidos)
    c.execute("""
        SELECT 
            thread_id,
            deal_id,
            COUNT(*) as total_emails,
            SUM(CASE WHEN direccion = 'entrada' THEN 1 ELSE 0 END) as entrada,
            SUM(CASE WHEN direccion = 'salida' THEN 1 ELSE 0 END) as salida,
            MIN(asunto) as asunto
        FROM email_history
        WHERE thread_id IS NOT NULL AND thread_id != ''
        GROUP BY thread_id, deal_id
        HAVING entrada > 0 AND salida > 0
        ORDER BY total_emails DESC
        LIMIT 10
    """)
    
    conversaciones = []
    for row in c.fetchall():
        conversaciones.append({
            'thread_id': row['thread_id'][:60],
            'deal_id': row['deal_id'],
            'total': row['total_emails'],
            'entrada': row['entrada'],
            'salida': row['salida'],
            'asunto': row['asunto'][:70]
        })
    resultados['conversaciones'] = conversaciones
    
    # 4. Deals con multiples threads
    c.execute("""
        SELECT 
            deal_id,
            COUNT(DISTINCT thread_id) as thread_count,
            COUNT(*) as total_emails
        FROM email_history
        WHERE deal_id IS NOT NULL AND thread_id IS NOT NULL AND thread_id != ''
        GROUP BY deal_id
        HAVING thread_count > 1
        ORDER BY total_emails DESC
        LIMIT 5
    """)
    
    deals_problema = []
    for row in c.fetchall():
        deal_id = row['deal_id']
        
        # Obtener threads de este deal
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
        """, (deal_id,))
        
        threads = []
        for t in c.fetchall():
            threads.append({
                'thread_id': t['thread_id'][:50] if t['thread_id'] else 'NULL',
                'email_count': t['email_count'],
                'entrada': t['entrada'],
                'salida': t['salida'],
                'asunto': t['asunto'][:60] if t['asunto'] else ''
            })
        
        deals_problema.append({
            'deal_id': deal_id,
            'thread_count': row['thread_count'],
            'total_emails': row['total_emails'],
            'threads': threads
        })
    
    resultados['deals_con_multiples_threads'] = deals_problema
    
    # 5. Emails sin thread_id
    c.execute("SELECT COUNT(*) as count FROM email_history WHERE thread_id IS NULL OR thread_id = ''")
    resultados['emails_sin_thread'] = c.fetchone()['count']
    
    # 6. Ultimas cotizaciones enviadas
    c.execute("""
        SELECT 
            id, deal_id, thread_id, asunto, destinatario, created_at
        FROM email_history
        WHERE tipo = 'cotizacion' AND direccion = 'salida'
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    cotizaciones = []
    for row in c.fetchall():
        # Buscar respuestas
        thread_id = row['thread_id']
        respuestas_count = 0
        if thread_id:
            c.execute("""
                SELECT COUNT(*) as count 
                FROM email_history 
                WHERE deal_id = ? AND thread_id = ? AND direccion = 'entrada'
            """, (row['deal_id'], thread_id))
            respuestas_count = c.fetchone()['count']
        
        cotizaciones.append({
            'email_id': row['id'],
            'deal_id': row['deal_id'],
            'thread_id': row['thread_id'][:50] if row['thread_id'] else 'NULL',
            'asunto': row['asunto'][:70],
            'destinatario': row['destinatario'],
            'fecha': row['created_at'],
            'respuestas': respuestas_count
        })
    
    resultados['ultimas_cotizaciones'] = cotizaciones
    
    conn.close()
    
    # Guardar resultados
    with open('diagnostico_resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print("Diagnostico completado. Resultados guardados en: diagnostico_resultados.json")
    print(f"Total emails: {resultados['total_emails']}")
    print(f"Conversaciones (threads completos): {len(resultados['conversaciones'])}")
    print(f"Deals con threads fragmentados: {len(resultados['deals_con_multiples_threads'])}")
    print(f"Emails sin thread_id: {resultados['emails_sin_thread']}")

if __name__ == "__main__":
    main()
