import re
from typing import Tuple

DANGEROUS_KEYWORDS = [
    'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 
    'INSERT', 'UPDATE', 'GRANT', 'REVOKE', 'EXEC'
]

def validate_sql(sql: str) -> Tuple[bool, str]:
    sql_upper = sql.upper().strip()
    
    # Check for dangerous keywords
    for keyword in DANGEROUS_KEYWORDS:
        if re.search(r'\b' + keyword + r'\b', sql_upper):
            return False, f"Query contains forbidden keyword: {keyword}"
    
    # Must be a SELECT query
    if not sql_upper.startswith('SELECT'):
        return False, "Only SELECT queries are allowed"
    
    # Check for multiple statements
    if ';' in sql.rstrip(';'):
        return False, "Multiple SQL statements are not allowed"
    
    return True, None
