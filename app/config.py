# Configuration settings for the Online Shop API

# JWT Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database Configuration
DATABASE_CONFIG = {
    "driver": "ODBC Driver 18 for SQL Server",
    "server": "THANHAN\\MSSQLSERVER2019",
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
OPENAI_API_KEY = "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"  # Replace with your actual API key
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 1000
OPENAI_TEMPERATURE = 0.7 