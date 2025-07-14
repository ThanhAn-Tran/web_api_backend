from fastapi import APIRouter, HTTPException, Depends, status
from app.models import PaymentCreate, PaymentStatusUpdate, PaymentResponse
from app.auth import get_current_user, generate_transaction_code
from app.database import get_connection

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_payment(payment: PaymentCreate, current_user_id: int = Depends(get_current_user)):
    """Create payment for an order"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Verify the order belongs to the user
        cursor.execute("""
            SELECT OrderID, TotalAmount, Status 
            FROM Orders 
            WHERE OrderID = ? AND UserID = ?
        """, payment.order_id, current_user_id)
        
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order_id, total_amount, order_status = order
        
        # Check if payment already exists for this order
        cursor.execute("SELECT PaymentID FROM Payments WHERE OrderID = ?", order_id)
        existing_payment = cursor.fetchone()
        
        if existing_payment:
            raise HTTPException(status_code=400, detail="Payment already exists for this order")
        
        # Validate payment method
        valid_methods = ['Momo', 'COD', 'Credit Card', 'ZaloPay']
        if payment.payment_method not in valid_methods:
            raise HTTPException(status_code=400, detail=f"Invalid payment method. Valid methods: {valid_methods}")
        
        # Generate transaction code
        transaction_code = generate_transaction_code(payment.payment_method)
        
        # Create payment record
        cursor.execute("""
            INSERT INTO Payments (OrderID, PaymentMethod, PaymentStatus, TransactionCode) 
            VALUES (?, ?, 'Unpaid', ?)
        """, order_id, payment.payment_method, transaction_code)
        
        cursor.execute("SELECT @@IDENTITY")
        payment_id = cursor.fetchone()[0]
        
        conn.commit()
        
        return {
            "message": "Payment created successfully",
            "payment_id": payment_id,
            "transaction_code": transaction_code,
            "order_id": order_id,
            "payment_method": payment.payment_method,
            "amount": float(total_amount)
        }
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, current_user_id: int = Depends(get_current_user)):
    """Get payment details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get payment with order verification
        cursor.execute("""
            SELECT p.PaymentID, p.OrderID, p.PaymentMethod, p.PaymentStatus, 
                   p.TransactionCode, p.PaidAt, o.UserID
            FROM Payments p
            JOIN Orders o ON p.OrderID = o.OrderID
            WHERE p.PaymentID = ?
        """, payment_id)
        
        payment = cursor.fetchone()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Check if user owns this payment (or is admin)
        cursor.execute("SELECT Role FROM Users WHERE UserID = ?", current_user_id)
        user_role = cursor.fetchone()[0]
        
        if payment[6] != current_user_id and user_role < 2:  # payment[6] is UserID from order
            raise HTTPException(status_code=403, detail="Access denied")
        
        return PaymentResponse(
            payment_id=payment[0],
            order_id=payment[1],
            payment_method=payment[2],
            payment_status=payment[3],
            transaction_code=payment[4],
            paid_at=str(payment[5]) if payment[5] else None
        )
    
    finally:
        conn.close()

@router.put("/{payment_id}/status")
def update_payment_status(payment_id: int, status_update: PaymentStatusUpdate, current_user_id: int = Depends(get_current_user)):
    """Update payment status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get payment with order verification
        cursor.execute("""
            SELECT p.PaymentID, p.OrderID, p.PaymentStatus, o.UserID
            FROM Payments p
            JOIN Orders o ON p.OrderID = o.OrderID
            WHERE p.PaymentID = ?
        """, payment_id)
        
        payment = cursor.fetchone()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Check if user owns this payment (or is admin)
        cursor.execute("SELECT Role FROM Users WHERE UserID = ?", current_user_id)
        user_role = cursor.fetchone()[0]
        
        if payment[3] != current_user_id and user_role < 2:  # payment[3] is UserID from order
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Validate payment status
        valid_statuses = ['Paid', 'Unpaid', 'Failed', 'Refunded']
        if status_update.payment_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid payment status. Valid statuses: {valid_statuses}")
        
        current_status = payment[2]
        order_id = payment[1]
        
        # Update payment status
        paid_at = "GETDATE()" if status_update.payment_status == 'Paid' else "NULL"
        cursor.execute(f"""
            UPDATE Payments 
            SET PaymentStatus = ?, PaidAt = {paid_at}
            WHERE PaymentID = ?
        """, status_update.payment_status, payment_id)
        
        # Update order status based on payment status
        if status_update.payment_status == 'Paid' and current_status != 'Paid':
            print(f"DEBUG: Processing payment {payment_id} for order {order_id} - marking as Paid")
            cursor.execute("UPDATE Orders SET Status = 'Confirmed' WHERE OrderID = ?", order_id)
            
            # Reduce stock for each product in the order
            cursor.execute("""
                SELECT oi.ProductID, oi.Quantity
                FROM OrderItems oi
                WHERE oi.OrderID = ?
            """, order_id)
            
            order_items = cursor.fetchall()
            print(f"DEBUG: Found {len(order_items)} order items to process")
            
            for product_id, quantity in order_items:
                print(f"DEBUG: Processing product {product_id}, quantity {quantity}")
                # Check if product has enough stock
                cursor.execute("SELECT Stock FROM Products WHERE ProductID = ?", product_id)
                stock_result = cursor.fetchone()
                
                if stock_result:
                    current_stock = stock_result[0]
                    print(f"DEBUG: Product {product_id} current stock: {current_stock}")
                    if current_stock >= quantity:
                        # Reduce stock
                        cursor.execute("""
                            UPDATE Products 
                            SET Stock = Stock - ? 
                            WHERE ProductID = ?
                        """, quantity, product_id)
                        print(f"DEBUG: Reduced stock for product {product_id} by {quantity}")
                    else:
                        # Log warning but don't fail the payment - could be handled differently
                        print(f"Warning: Insufficient stock for product {product_id}. Stock: {current_stock}, Ordered: {quantity}")
                        # Still reduce stock to 0 or handle as needed
                        cursor.execute("""
                            UPDATE Products 
                            SET Stock = 0 
                            WHERE ProductID = ?
                        """, product_id)
                        print(f"DEBUG: Set stock to 0 for product {product_id}")
                else:
                    print(f"DEBUG: Product {product_id} not found!")
            
        elif status_update.payment_status == 'Failed':
            cursor.execute("UPDATE Orders SET Status = 'Cancelled' WHERE OrderID = ?", order_id)
        elif status_update.payment_status == 'Refunded':
            cursor.execute("UPDATE Orders SET Status = 'Refunded' WHERE OrderID = ?", order_id)
            
            # Restore stock when refunded
            cursor.execute("""
                SELECT oi.ProductID, oi.Quantity
                FROM OrderItems oi
                WHERE oi.OrderID = ?
            """, order_id)
            
            order_items = cursor.fetchall()
            
            for product_id, quantity in order_items:
                cursor.execute("""
                    UPDATE Products 
                    SET Stock = Stock + ? 
                    WHERE ProductID = ?
                """, quantity, product_id)
        
        conn.commit()
        
        return {
            "message": "Payment status updated successfully",
            "payment_id": payment_id,
            "new_status": status_update.payment_status
        }
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("")
def get_user_payments(current_user_id: int = Depends(get_current_user)):
    """Get user's payments (admin sees all)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user is admin
        cursor.execute("SELECT Role FROM Users WHERE UserID = ?", current_user_id)
        user_role = cursor.fetchone()[0]
        
        if user_role >= 2:  # Admin can see all payments
            cursor.execute("""
                SELECT p.PaymentID, p.OrderID, p.PaymentMethod, p.PaymentStatus, 
                       p.TransactionCode, p.PaidAt, o.UserID, u.Username, o.TotalAmount
                FROM Payments p
                JOIN Orders o ON p.OrderID = o.OrderID
                JOIN Users u ON o.UserID = u.UserID
                ORDER BY p.PaymentID DESC
            """)
            
            payments = cursor.fetchall()
            
            return [
                {
                    "payment_id": payment[0],
                    "order_id": payment[1],
                    "payment_method": payment[2],
                    "payment_status": payment[3],
                    "transaction_code": payment[4],
                    "paid_at": str(payment[5]) if payment[5] else None,
                    "user_id": payment[6],
                    "username": payment[7],
                    "amount": float(payment[8])
                } for payment in payments
            ]
        else:  # Regular user sees only their payments
            cursor.execute("""
                SELECT p.PaymentID, p.OrderID, p.PaymentMethod, p.PaymentStatus, 
                       p.TransactionCode, p.PaidAt, o.TotalAmount
                FROM Payments p
                JOIN Orders o ON p.OrderID = o.OrderID
                WHERE o.UserID = ?
                ORDER BY p.PaymentID DESC
            """, current_user_id)
            
            payments = cursor.fetchall()
            
            return [
                {
                    "payment_id": payment[0],
                    "order_id": payment[1],
                    "payment_method": payment[2],
                    "payment_status": payment[3],
                    "transaction_code": payment[4],
                    "paid_at": str(payment[5]) if payment[5] else None,
                    "amount": float(payment[6])
                } for payment in payments
            ]
    
    finally:
        conn.close() 