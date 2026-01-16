-- Create airflow database
CREATE DATABASE airflow_db;

-- Connect to sales_db (default database)
\c sales_db;

-- Create query logs table only
CREATE TABLE query_logs (
    log_id SERIAL PRIMARY KEY,
    natural_language_query TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    execution_status VARCHAR(20),
    execution_time_ms INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
