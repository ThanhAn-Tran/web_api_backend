from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import *
from app.routers import (
    health_router,
    auth_router,
    users_router,
    categories_router,
    products_router,
    cart_router,
    orders_router,
    payments_router,
    conversations_router,
    chatbot_router
)
import os

# Create static directory if it doesn't exist
if not os.path.exists("static/product_images"):
    os.makedirs("static/product_images")

# Create FastAPI application
app = FastAPI(title=API_TITLE, version=API_VERSION)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(conversations_router)
app.include_router(chatbot_router)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Online Shop API",
        "version": API_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT) 