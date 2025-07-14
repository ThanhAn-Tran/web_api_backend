from fastapi import APIRouter, HTTPException, Depends, status
from app.auth import get_current_user
from app.database import get_connection

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(current_user_id: int = Depends(get_current_user)):
    """Create order from cart"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get user's cart
        cursor.execute("SELECT CartID FROM Cart WHERE UserID = ?", current_user_id)
        cart = cursor.fetchone()
        
        if not cart:
            raise HTTPException(status_code=400, detail="No cart found")
        
        cart_id = cart[0]
        
        # Get cart items
        cursor.execute("""
            SELECT ci.ProductID, ci.Quantity, p.Price
            FROM CartItems ci
            JOIN Products p ON ci.ProductID = p.ProductID
            WHERE ci.CartID = ?
        """, cart_id)
        
        cart_items = cursor.fetchall()
        
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Calculate total amount
        total_amount = sum(item[1] * item[2] for item in cart_items)
        
        # Create order
        cursor.execute("INSERT INTO Orders (UserID, TotalAmount) VALUES (?, ?)", current_user_id, total_amount)
        cursor.execute("SELECT @@IDENTITY")
        order_id = cursor.fetchone()[0]
        
        # Create order items
        for item in cart_items:
            cursor.execute(
                "INSERT INTO OrderItems (OrderID, ProductID, Quantity, Price) VALUES (?, ?, ?, ?)",
                order_id, item[0], item[1], item[2]
            )
        
        # Clear cart
        cursor.execute("DELETE FROM CartItems WHERE CartID = ?", cart_id)
        
        conn.commit()
        return {"message": "Order created successfully", "order_id": order_id}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("")
def get_user_orders(current_user_id: int = Depends(get_current_user)):
    """Get user's orders"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT OrderID, OrderDate, Status, TotalAmount
            FROM Orders
            WHERE UserID = ?
            ORDER BY OrderDate DESC
        """, current_user_id)
        
        orders = cursor.fetchall()
        
        return [
            {
                "order_id": order[0],
                "order_date": str(order[1]),
                "status": order[2],
                "total_amount": float(order[3])
            } for order in orders
        ]
    finally:
        conn.close()

@router.get("/{order_id}")
def get_order_details(order_id: int, current_user_id: int = Depends(get_current_user)):
    """Get order details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get order
        cursor.execute("""
            SELECT OrderID, OrderDate, Status, TotalAmount
            FROM Orders
            WHERE OrderID = ? AND UserID = ?
        """, order_id, current_user_id)
        
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get order items
        cursor.execute("""
            SELECT oi.ProductID, p.Name, oi.Quantity, oi.Price, (oi.Quantity * oi.Price) as Total
            FROM OrderItems oi
            JOIN Products p ON oi.ProductID = p.ProductID
            WHERE oi.OrderID = ?
        """, order_id)
        
        items = cursor.fetchall()
        
        return {
            "order_id": order[0],
            "order_date": str(order[1]),
            "status": order[2],
            "total_amount": float(order[3]),
            "items": [
                {
                    "product_id": item[0],
                    "product_name": item[1],
                    "quantity": item[2],
                    "price": float(item[3]),
                    "total": float(item[4])
                } for item in items
            ]
        }
    finally:
        conn.close()

@router.get("/{order_id}/payment")
def get_order_payment(order_id: int, current_user_id: int = Depends(get_current_user)):
    """Get payment for specific order"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Verify order belongs to user
        cursor.execute("SELECT UserID FROM Orders WHERE OrderID = ?", order_id)
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if user owns this order (or is admin)
        cursor.execute("SELECT Role FROM Users WHERE UserID = ?", current_user_id)
        user_role = cursor.fetchone()[0]
        
        if order[0] != current_user_id and user_role < 2:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get payment for this order
        cursor.execute("""
            SELECT PaymentID, OrderID, PaymentMethod, PaymentStatus, 
                   TransactionCode, PaidAt
            FROM Payments 
            WHERE OrderID = ?
        """, order_id)
        
        payment = cursor.fetchone()
        
        if not payment:
            return {"message": "No payment found for this order", "order_id": order_id}
        
        return {
            "payment_id": payment[0],
            "order_id": payment[1],
            "payment_method": payment[2],
            "payment_status": payment[3],
            "transaction_code": payment[4],
            "paid_at": str(payment[5]) if payment[5] else None
        }
    
    finally:
        conn.close() 