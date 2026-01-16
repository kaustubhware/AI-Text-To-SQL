from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import time
import requests
import pandas as pd
import io
from database import get_db_connection, get_schema_info, execute_query, log_query
from sql_validator import validate_sql

app = FastAPI(title="Text-to-SQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

class QueryRequest(BaseModel):
    question: str
    table_name: Optional[str] = None

class QueryResponse(BaseModel):
    question: str
    generated_sql: str
    results: Optional[List[Dict[str, Any]]] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None

def generate_sql_with_groq(question: str, schema_info: str) -> str:
    prompt = f"""You are a SQL expert. Convert the natural language question to a PostgreSQL query.

Database Schema:
{schema_info}

Rules:
- Only generate SELECT queries
- Use proper PostgreSQL syntax
- Return only the SQL query without explanation
- Use table and column names exactly as shown in schema

Question: {question}

SQL Query:"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        sql_query = result['choices'][0]['message']['content'].strip()
        
        # Clean up the response
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        return sql_query
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
        raise Exception(f"Groq API Error: {error_detail}")

@app.get("/")
def root():
    return {"message": "Text-to-SQL API is running"}

@app.get("/schema")
def get_schema():
    try:
        schema = get_schema_info()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
def text_to_sql(request: QueryRequest):
    start_time = time.time()
    
    try:
        # Get database schema
        schema_info = get_schema_info()
        
        # If table_name is provided, focus on that table
        if request.table_name:
            question = f"{request.question} (Query the {request.table_name} table)"
        else:
            question = request.question
        
        # Generate SQL using Groq
        generated_sql = generate_sql_with_groq(question, schema_info)
        
        # Validate SQL
        is_valid, error_msg = validate_sql(generated_sql)
        if not is_valid:
            log_query(request.question, generated_sql, "failed", 0, error_msg)
            return QueryResponse(
                question=request.question,
                generated_sql=generated_sql,
                error=error_msg
            )
        
        # Execute query
        results = execute_query(generated_sql)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Log successful query
        log_query(request.question, generated_sql, "success", execution_time, None)
        
        return QueryResponse(
            question=request.question,
            generated_sql=generated_sql,
            results=results,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        log_query(request.question, generated_sql if 'generated_sql' in locals() else "", "error", execution_time, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_query_history(limit: int = 10):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT natural_language_query, generated_sql, execution_status, 
                   execution_time_ms, error_message, created_at
            FROM query_logs
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        history = []
        for row in results:
            history.append({
                "question": row[0],
                "sql": row[1],
                "status": row[2],
                "execution_time_ms": row[3],
                "error": row[4],
                "timestamp": row[5].isoformat()
            })
        
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file content
        content = await file.read()
        filename = file.filename.lower()
        
        # Determine file type and read data
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        elif filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV, Excel, or JSON")
        
        # Clean table name from filename
        table_name = filename.split('.')[0].lower().replace(' ', '_').replace('-', '_')
        table_name = ''.join(c for c in table_name if c.isalnum() or c == '_')
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop table if exists
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Create table from dataframe
        # Map pandas dtypes to PostgreSQL types
        type_mapping = {
            'int64': 'INTEGER',
            'float64': 'DECIMAL',
            'object': 'TEXT',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP'
        }
        
        columns = []
        for col, dtype in df.dtypes.items():
            col_name = col.lower().replace(' ', '_').replace('-', '_')
            col_name = ''.join(c for c in col_name if c.isalnum() or c == '_')
            pg_type = type_mapping.get(str(dtype), 'TEXT')
            columns.append(f"{col_name} {pg_type}")
        
        create_sql = f"CREATE TABLE {table_name} ({', '.join(columns)})"
        cursor.execute(create_sql)
        
        # Insert data
        col_names = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        col_names = [''.join(c for c in col if c.isalnum() or c == '_') for col in col_names]
        
        for _, row in df.iterrows():
            values = [None if pd.isna(val) else val for val in row]
            placeholders = ','.join(['%s'] * len(values))
            insert_sql = f"INSERT INTO {table_name} ({','.join(col_names)}) VALUES ({placeholders})"
            cursor.execute(insert_sql, values)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": "File uploaded successfully",
            "table_name": table_name,
            "rows": len(df),
            "columns": list(df.columns),
            "hint": f"Ask questions like: 'Show me data from {table_name} table' or 'What are the columns in {table_name}?'"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tables")
def get_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
