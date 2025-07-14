# 📡 Complete API Endpoints Documentation

## Base URL: `http://localhost:8000`

---

## 🏥 **Health Check Endpoints**
| Method | Endpoint | Description | Auth Required | Response |
|--------|----------|-------------|---------------|----------|
| GET | `/health` | Basic API health check | No | JSON status |
| GET | `/health/database` | Database connection test | No | Database info |

---

## 🔐 **Authentication Endpoints**
| Method | Endpoint | Description | Auth Required | Body Required |
|--------|----------|-------------|---------------|---------------|
| POST | `/auth/register` | Register new user | No | UserCreate |
| POST | `/auth/login` | User login | No | UserLogin |

### Request Models:
```json
// UserCreate
{
    "username": "string",
    "password": "string", 
    "email": "string",
    "role": 1  // Optional: 0=Customer, 1=Manager, 2=Admin
}

// UserLogin
{
    "username": "string",
    "password": "string"
}
```

---

## 👥 **User Management Endpoints**
| Method | Endpoint | Description | Auth Required | Response Model |
|--------|----------|-------------|---------------|----------------|
| GET | `/users/me` | Get current user info | Yes | UserResponse |

⚠️ **README Correction**: The endpoint is `/users/me`, not `/users/profile`

### Response Model:
```json
// UserResponse
{
    "user_id": 1,
    "username": "string",
    "email": "string", 
    "role": 1,
    "created_at": "2024-01-01T00:00:00"
}
```

---

## 🏷️ **Category Endpoints**
| Method | Endpoint | Description | Auth Required | Role Required |
|--------|----------|-------------|---------------|---------------|
| GET | `/categories` | Get all categories | No | None |
| POST | `/categories` | Create category | Yes | Admin (≥2) |

⚠️ **Missing Endpoints**: PUT/DELETE operations for categories are not implemented

### Request/Response Models:
```json
// CategoryCreate
{
    "name": "string"
}

// CategoryResponse
{
    "category_id": 1,
    "name": "string"
}
```

---

## 📦 **Product Endpoints** 
| Method | Endpoint | Description | Auth Required | Role Required |
|--------|----------|-------------|---------------|---------------|
| GET | `/products` | Get all products | No | None |
| GET | `/products/{id}` | Get product by ID | No | None |
| POST | `/products` | Create product | Yes | Admin (≥2) |
| PUT | `/products/{id}` | Update product | Yes | Admin (≥2) |
| DELETE | `/products/{id}` | Delete product | Yes | Admin (≥2) |

### Request/Response Models:
```json
// ProductCreate
{
    "name": "string",
    "description": "string",
    "price": 99.99,
    "stock": 100,
    "color": "string",
    "style": "string", 
    "category_id": 1
}

// ProductResponse
{
    "product_id": 1,
    "name": "string",
    "description": "string",
    "price": 99.99,
    "stock": 100,
    "color": "string",
    "style": "string",
    "category_id": 1,
    "created_at": "2024-01-01T00:00:00"
}
```

---

## 🛒 **Shopping Cart Endpoints**
| Method | Endpoint | Description | Auth Required | Body Required |
|--------|----------|-------------|---------------|---------------|
| GET | `/cart` | Get cart contents | Yes | None |
| POST | `/cart/items` | Add item to cart | Yes | CartItemCreate |
| DELETE | `/cart/items/{cart_item_id}` | Remove item from cart | Yes | None |

⚠️ **Missing Endpoint**: PUT for updating cart item quantity - not implemented

### Request Models:
```json
// CartItemCreate
{
    "product_id": 1,
    "quantity": 2
}
```

### Response Example:
```json
{
    "cart_id": 1,
    "items": [
        {
            "cart_item_id": 1,
            "product_id": 1,
            "product_name": "Product Name",
            "price": 99.99,
            "quantity": 2,
            "total": 199.98
        }
    ],
    "total_amount": 199.98
}
```

---

## 📋 **Order Endpoints**
| Method | Endpoint | Description | Auth Required | Response |
|--------|----------|-------------|---------------|----------|
| POST | `/orders` | Create order from cart | Yes | Order created |
| GET | `/orders` | Get user orders | Yes | Order list |
| GET | `/orders/{id}` | Get order details | Yes | Order details |
| GET | `/orders/{id}/payment` | Get order payment info | Yes | Payment info |

---

## 💳 **Payment Endpoints**
| Method | Endpoint | Description | Auth Required | Body Required |
|--------|----------|-------------|---------------|---------------|
| POST | `/payments` | Create payment | Yes | PaymentCreate |
| GET | `/payments/{id}` | Get payment details | Yes | None |
| PUT | `/payments/{id}/status` | Update payment status | Yes | PaymentStatusUpdate |
| GET | `/payments` | Get user payments | Yes | None |

### Request Models:
```json
// PaymentCreate
{
    "order_id": 1,
    "payment_method": "Momo"  // Momo, COD, Credit Card, ZaloPay
}

// PaymentStatusUpdate
{
    "payment_status": "Paid"  // Paid, Unpaid, Failed, Refunded
}
```

---

## 💬 **Conversation Endpoints**
| Method | Endpoint | Description | Auth Required | Body Required |
|--------|----------|-------------|---------------|---------------|
| POST | `/conversations` | Save chat message | Yes | ConversationCreate |
| GET | `/conversations` | Get chat history | Yes | None |

### Request Model:
```json
// ConversationCreate
{
    "role": "user",
    "message": "Hello"
}
```

---

## 🤖 **Chatbot Endpoints**
| Method | Endpoint | Description | Auth Required | Body Required |
|--------|----------|-------------|---------------|---------------|
| POST | `/chatbot/chat` | Chat with AI bot | Yes | ChatMessage |
| GET | `/chatbot/history` | Get conversation history | Yes | None |
| POST | `/chatbot/product-search` | Natural language search | Yes | ChatMessage |
| POST | `/chatbot/add-to-cart/{id}` | Add to cart via chat | Yes | None |
| GET | `/chatbot/cart-contents` | Get cart via chat | Yes | None |
| POST | `/chatbot/quick-chat` | Quick chat (no context) | Yes | ChatMessage |

⚠️ **Missing Documentation**: `/chatbot/quick-chat` endpoint was not in README

### Request Model:
```json
// ChatMessage
{
    "message": "I'm looking for red shoes"
}
```

---

## 🔧 **Issues Found & Recommendations**

### 1. **API Inconsistencies:**
- **Users endpoint**: README shows `/users/profile` but actual is `/users/me`
- **Missing cart update**: No PUT endpoint for updating cart item quantities
- **Missing category management**: No PUT/DELETE for categories
- **Undocumented endpoint**: `/chatbot/quick-chat` exists but not in README

### 2. **Missing CRUD Operations:**
- Categories: Only GET/POST implemented, missing PUT/DELETE
- Cart: Only GET/POST/DELETE implemented, missing PUT for quantity updates

### 3. **Authentication Issues:**
- Some endpoints check for role ≥ 2 for admin access
- Role system: 0=Customer, 1=Manager, 2=Admin (but some checks use different logic)

### 4. **Database Schema Issues:**
- Products table uses `Stock` column but model references `stock`
- Conversations table schema mismatch (Role vs Message/Response/Intent columns)

---

## 📝 **Recommended Fixes**

1. **Update README.md** to correct the users endpoint
2. **Add missing cart update endpoint**:
   ```python
   @router.put("/items/{cart_item_id}")
   def update_cart_item_quantity(cart_item_id: int, quantity: int, current_user_id: int = Depends(get_current_user)):
   ```

3. **Add category management endpoints**:
   ```python
   @router.put("/categories/{category_id}")
   @router.delete("/categories/{category_id}")
   ```

4. **Fix database column name consistency**
5. **Update documentation to include `/chatbot/quick-chat`**

---

## 🧪 **Testing Commands**

```bash
# Test health
curl -X GET "http://localhost:8000/health"

# Test user registration  
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "test123", "role": 0}'

# Test login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}'

# Test protected endpoint (replace TOKEN)
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer TOKEN"
```

This documentation reflects the **actual implemented endpoints** in your codebase, not just what was documented in the README. 