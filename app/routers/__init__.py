# Routers package for Online Shop API

from .health import router as health_router
from .auth import router as auth_router
from .users import router as users_router
from .categories import router as categories_router
from .products import router as products_router
from .cart import router as cart_router
from .orders import router as orders_router
from .payments import router as payments_router
from .conversations import router as conversations_router
from .chatbot import router as chatbot_router

__all__ = [
    "health_router",
    "auth_router", 
    "users_router",
    "categories_router",
    "products_router",
    "cart_router",
    "orders_router",
    "payments_router",
    "conversations_router",
    "chatbot_router"
] 