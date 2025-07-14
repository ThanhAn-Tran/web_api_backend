from fastapi import APIRouter
from app.database import get_connection

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    """Basic API health check"""
    return {"status": "healthy", "message": "Online Shop API is running"}

@router.get("/health/database")
def database_health_check():
    """Check database connection and basic functionality"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        # Test if database exists and has our tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            AND TABLE_CATALOG = 'ShopDB'
            ORDER BY TABLE_NAME
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Test a simple query on Users table
        cursor.execute("SELECT COUNT(*) as user_count FROM Users")
        user_count = cursor.fetchone()[0]
        
        # Test a simple query on Products table
        cursor.execute("SELECT COUNT(*) as product_count FROM Products")
        product_count = cursor.fetchone()[0]
        
        # Test a simple query on Categories table
        cursor.execute("SELECT COUNT(*) as category_count FROM Categories")
        category_count = cursor.fetchone()[0]
        
        # Test a simple query on Payments table
        cursor.execute("SELECT COUNT(*) as payment_count FROM Payments")
        payment_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "healthy",
            "message": "Database connection successful",
            "database": "ShopDB",
            "tables_found": tables,
            "data_counts": {
                "users": user_count,
                "products": product_count,
                "categories": category_count,
                "payments": payment_count
            },
            "connection_details": {
                "driver": "ODBC Driver 18 for SQL Server",
                "server": "THANHAN\\MSSQLSERVER2019"
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Database connection failed",
            "error": str(e),
            "connection_details": {
                "driver": "ODBC Driver 18 for SQL Server",
                "server": "THANHAN\\MSSQLSERVER2019",
                "database": "ShopDB"
            }
        } 