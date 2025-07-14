from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile, Form
from typing import List, Optional
from app.models import ProductCreate, ProductResponse, ProductUpdate, ProductImageResponse
from app.auth import get_current_user
from app.database import get_connection
import os
import shutil

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=List[ProductResponse])
def get_products():
    """Get all products"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT ProductID, Name, Description, Price, Stock, Color, Style, CategoryID, CreatedAt, IsLocked, ImagePath FROM Products"
        )
        products = cursor.fetchall()
        
        product_responses = []
        for prod in products:
            product_id = prod[0]
            cursor.execute("SELECT ImageID, ImageURL FROM ProductImages WHERE ProductID = ?", product_id)
            images = cursor.fetchall()
            image_responses = [ProductImageResponse(image_id=img[0], image_url=img[1]) for img in images]
            
            product_responses.append(ProductResponse(
                product_id=product_id,
                name=prod[1],
                description=prod[2],
                price=float(prod[3]),
                stock=prod[4],
                color=prod[5],
                style=prod[6],
                category_id=prod[7],
                created_at=str(prod[8]),
                is_locked=prod[9],
                image_path=prod[10],
                images=image_responses
            ))
        return product_responses
    finally:
        conn.close()

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    """Get a specific product by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT ProductID, Name, Description, Price, Stock, Color, Style, CategoryID, CreatedAt, IsLocked, ImagePath FROM Products WHERE ProductID = ?",
            product_id
        )
        product = cursor.fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        cursor.execute("SELECT ImageID, ImageURL FROM ProductImages WHERE ProductID = ?", product_id)
        images = cursor.fetchall()
        image_responses = [ProductImageResponse(image_id=img[0], image_url=img[1]) for img in images]

        return ProductResponse(
            product_id=product[0],
            name=product[1],
            description=product[2],
            price=float(product[3]),
            stock=product[4],
            color=product[5],
            style=product[6],
            category_id=product[7],
            created_at=str(product[8]),
            is_locked=product[9],
            image_path=product[10],
            images=image_responses
        )
    finally:
        conn.close()

@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    color: str = Form(...),
    style: str = Form(...),
    category_id: int = Form(...),
    files: List[UploadFile] = File(...),
    current_user_id: int = Depends(get_current_user)
):
    """Create a new product with images (Admin only)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user is admin (role 2 or 3)
        cursor.execute("SELECT Role FROM Users WHERE UserID = ?", current_user_id)
        user_role = cursor.fetchone()[0]
        if user_role < 2:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Insert product
        cursor.execute(
            "INSERT INTO Products (Name, Description, Price, Stock, Color, Style, CategoryID) OUTPUT INSERTED.ProductID VALUES (?, ?, ?, ?, ?, ?, ?)",
            name, description, price, stock, color, style, category_id
        )
        product_id = cursor.fetchone()[0]

        # Handle image uploads
        image_urls = []
        for file in files:
            file_path = f"static/product_images/{product_id}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Use forward slashes for URL
            image_url = file_path.replace("\\", "/")
            image_urls.append(image_url)
            
            cursor.execute(
                "INSERT INTO ProductImages (ProductID, ImageURL) VALUES (?, ?)",
                product_id, image_url
            )

        # Set primary image path
        if image_urls:
            cursor.execute("UPDATE Products SET ImagePath = ? WHERE ProductID = ?", image_urls[0], product_id)

        conn.commit()
        return {"message": "Product created successfully", "product_id": product_id, "image_urls": image_urls}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.put("/{product_id}")
def update_product(
    product_id: int, 
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    color: Optional[str] = Form(None),
    style: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    is_locked: Optional[bool] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user_id: int = Depends(get_current_user)
):
    """Update a product (Admin only)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user is admin (role 2 or 3)
        cursor.execute("SELECT Role FROM Users WHERE UserID = ?", current_user_id)
        user_role = cursor.fetchone()[0]
        if user_role < 2:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Create a dictionary of fields to update
        update_data = {
            "Name": name, "Description": description, "Price": price, "Stock": stock,
            "Color": color, "Style": style, "CategoryID": category_id, "IsLocked": is_locked
        }
        update_data = {k: v for k, v in update_data.items() if v is not None}

        if update_data:
            set_clause = ", ".join([f"{key}=?" for key in update_data.keys()])
            values = list(update_data.values())
            values.append(product_id)

            cursor.execute(f"UPDATE Products SET {set_clause} WHERE ProductID=?", values)

        # Handle new image uploads
        if files:
            image_urls = []
            for file in files:
                file_path = f"static/product_images/{product_id}_{file.filename}"
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                image_url = file_path.replace("\\", "/")
                image_urls.append(image_url)
                
                cursor.execute(
                    "INSERT INTO ProductImages (ProductID, ImageURL) VALUES (?, ?)",
                    product_id, image_url
                )

        if not update_data and not files:
            raise HTTPException(status_code=400, detail="No fields to update")

        conn.commit()
        return {"message": "Product updated successfully"}
    
    except Exception as e:
        conn.rollback()
        print(f"ERROR updating product {product_id}: {e}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")
    finally:
        conn.close()

@router.patch("/{product_id}/lock", status_code=status.HTTP_200_OK)
def lock_product(product_id: int, current_user_id: int = Depends(get_current_user)):
    """Lock a product to prevent deletion (Admin only)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user is admin (role 2 or 3)
        cursor.execute("SELECT Role FROM Users WHERE UserID = ?", current_user_id)
        user_role = cursor.fetchone()[0]
        if user_role < 2:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cursor.execute("UPDATE Products SET IsLocked = 1 WHERE ProductID = ?", product_id)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        conn.commit()
        return {"message": "Product locked successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.patch("/{product_id}/unlock", status_code=status.HTTP_200_OK)
def unlock_product(product_id: int, current_user_id: int = Depends(get_current_user)):
    """Unlock a product to allow deletion (Admin only)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user is admin (role 2 or 3)
        cursor.execute("SELECT Role FROM Users WHERE UserID = ?", current_user_id)
        user_role = cursor.fetchone()[0]
        if user_role < 2:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cursor.execute("UPDATE Products SET IsLocked = 0 WHERE ProductID = ?", product_id)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        conn.commit()
        return {"message": "Product unlocked successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close() 