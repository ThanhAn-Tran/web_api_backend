from fastapi import APIRouter, HTTPException, Depends, status
from app.models import CartItemCreate
from app.auth import get_current_user
from app.database import get_connection

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])

@router.get("")
def get_user_cart(current_user_id: int = Depends(get_current_user)):
    """Get user's shopping cart"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get or create cart for user
        cursor.execute("SELECT CartID FROM Cart WHERE UserID = ?", current_user_id)
        cart = cursor.fetchone()
        
        if not cart:
            cursor.execute("INSERT INTO Cart (UserID) VALUES (?)", current_user_id)
            conn.commit()
            cursor.execute("SELECT CartID FROM Cart WHERE UserID = ?", current_user_id)
            cart = cursor.fetchone()
        
        cart_id = cart[0]
        
        # Get cart items
        cursor.execute("""
            SELECT ci.CartItemID, p.ProductID, p.Name, p.Price, ci.Quantity, (p.Price * ci.Quantity) as Total
            FROM CartItems ci
            JOIN Products p ON ci.ProductID = p.ProductID
            WHERE ci.CartID = ?
        """, cart_id)
        
        items = cursor.fetchall()
        total_amount = sum(item[5] for item in items)
        
        return {
            "cart_id": cart_id,
            "items": [
                {
                    "cart_item_id": item[0],
                    "product_id": item[1],
                    "product_name": item[2],
                    "price": float(item[3]),
                    "quantity": item[4],
                    "total": float(item[5])
                } for item in items
            ],
            "total_amount": total_amount
        }
    finally:
        conn.close()

@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_to_cart(item: CartItemCreate, current_user_id: int = Depends(get_current_user)):
    """Add item to cart"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get or create cart
        cursor.execute("SELECT CartID FROM Cart WHERE UserID = ?", current_user_id)
        cart = cursor.fetchone()
        
        if not cart:
            cursor.execute("INSERT INTO Cart (UserID) VALUES (?)", current_user_id)
            conn.commit()
            cursor.execute("SELECT CartID FROM Cart WHERE UserID = ?", current_user_id)
            cart = cursor.fetchone()
        
        cart_id = cart[0]
        
        # Check if item already exists in cart
        cursor.execute("SELECT CartItemID, Quantity FROM CartItems WHERE CartID = ? AND ProductID = ?", cart_id, item.product_id)
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Update quantity
            new_quantity = existing_item[1] + item.quantity
            cursor.execute("UPDATE CartItems SET Quantity = ? WHERE CartItemID = ?", new_quantity, existing_item[0])
        else:
            # Add new item
            cursor.execute("INSERT INTO CartItems (CartID, ProductID, Quantity) VALUES (?, ?, ?)", cart_id, item.product_id, item.quantity)
        
        conn.commit()
        return {"message": "Item added to cart successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/items/{cart_item_id}")
def remove_from_cart(cart_item_id: int, current_user_id: int = Depends(get_current_user)):
    """Remove item from cart"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Verify the cart item belongs to the user
        cursor.execute("""
            SELECT ci.CartItemID 
            FROM CartItems ci
            JOIN Cart c ON ci.CartID = c.CartID
            WHERE ci.CartItemID = ? AND c.UserID = ?
        """, cart_item_id, current_user_id)
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        cursor.execute("DELETE FROM CartItems WHERE CartItemID = ?", cart_item_id)
        conn.commit()
        return {"message": "Item removed from cart successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.put("/items/{cart_item_id}")
def update_cart_item_quantity(cart_item_id: int, update_data: dict, current_user_id: int = Depends(get_current_user)):
    """Update cart item quantity"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        quantity = update_data.get("quantity")
        if not quantity or quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        
        # Verify the cart item belongs to the user
        cursor.execute("""
            SELECT ci.CartItemID, ci.ProductID
            FROM CartItems ci
            JOIN Cart c ON ci.CartID = c.CartID
            WHERE ci.CartItemID = ? AND c.UserID = ?
        """, cart_item_id, current_user_id)
        
        cart_item = cursor.fetchone()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        product_id = cart_item[1]
        
        # Check if product has enough stock
        cursor.execute("SELECT Stock FROM Products WHERE ProductID = ?", product_id)
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if product[0] < quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {product[0]}")
        
        # Update quantity
        cursor.execute("UPDATE CartItems SET Quantity = ? WHERE CartItemID = ?", quantity, cart_item_id)
        conn.commit()
        
        return {"message": "Cart item quantity updated successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close() 