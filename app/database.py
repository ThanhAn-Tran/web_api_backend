import pyodbc
from app.config import DATABASE_CONFIG

def get_connection():
    """Get database connection"""
    connection_string = (
        f"DRIVER={{{DATABASE_CONFIG['driver']}}};"
        f"SERVER={DATABASE_CONFIG['server']};"
        f"DATABASE={DATABASE_CONFIG['database']};"
        f"Trusted_Connection={DATABASE_CONFIG['trusted_connection']};"
        f"TrustServerCertificate={DATABASE_CONFIG['trust_server_certificate']};"
    )
    
    conn = pyodbc.connect(connection_string)
    return conn 