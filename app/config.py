# Configuration settings for the Online Shop API

# JWT Configuration
SECRET_KEY = "your-secret-key-change-this-in-production" #not need
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database Configuration
DATABASE_CONFIG = {
    "driver": "ODBC Driver 18 for SQL Server", 
    "server": "THANHAN\\MSSQLSERVER2019", #replace your server
    "database": "ShopDB",
    "trusted_connection": "yes",
    "trust_server_certificate": "yes"
}

# CORS Configuration
CORS_ORIGINS = ["*"]  # In production, specify your frontend domains
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# API Configuration
API_TITLE = "Online Shop API"
API_VERSION = "1.0.0"
API_HOST = "0.0.0.0"
API_PORT = 8000

# OpenAI Configuration
OPENAI_API_KEY = "your_openai_key_here"  # Replace with your actual API key
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 1000
OPENAI_TEMPERATURE = 0.7 
