from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from app.models import CategoryCreate, CategoryResponse
from app.auth import get_current_user
from app.database import get_connection

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryResponse])
def get_categories():
    """Get all categories"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT CategoryID, Name FROM Categories")
        categories = cursor.fetchall()
        return [CategoryResponse(category_id=cat[0], name=cat[1]) for cat in categories]
    finally:
        conn.close()

@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, current_user_id: int = Depends(get_current_user)):
    """Create a new category (Admin only)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user is admin (role 2 or 3)
        cursor.execute("SELECT Role FROM Users WHERE UserID = ?", current_user_id)
        user_role = cursor.fetchone()[0]
        if user_role < 2:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cursor.execute("INSERT INTO Categories (Name) VALUES (?)", category.name)
        conn.commit()
        return {"message": "Category created successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close() 