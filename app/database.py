import psycopg2
import os
from typing import List, Dict, Any

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@postgres:5432/sales_db")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def get_schema_info() -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND table_name != 'query_logs'
    """)
    
    tables = cursor.fetchall()
    schema_info = []
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        columns_str = ", ".join([f"{col[0]} ({col[1]})" for col in columns])
        schema_info.append(f"Table: {table_name}\nColumns: {columns_str}")
    
    cursor.close()
    conn.close()
    
    return "\n\n".join(schema_info)

def execute_query(sql: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return [dict(zip(columns, row)) for row in results]

def log_query(question: str, sql: str, status: str, execution_time: int, error: str = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO query_logs (natural_language_query, generated_sql, execution_status, execution_time_ms, error_message)
            VALUES (%s, %s, %s, %s, %s)
        """, (question, sql, status, execution_time, error))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error logging query: {e}")
