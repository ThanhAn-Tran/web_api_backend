#!/usr/bin/env python3
"""
Web Selling Chatbot API
Main entry point for the application
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config import API_HOST, API_PORT
    uvicorn.run(app, host=API_HOST, port=API_PORT)
