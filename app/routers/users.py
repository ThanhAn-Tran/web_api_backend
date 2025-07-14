from fastapi import APIRouter, HTTPException, Depends
from app.models import UserResponse
from app.auth import get_current_user
from app.database import get_connection

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user_id: int = Depends(get_current_user)):
    """Get current user profile"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT UserID, Username, Email, Role, CreatedAt FROM Users WHERE UserID = ?",
            current_user_id
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            user_id=user[0],
            username=user[1],
            email=user[2],
            role=user[3],
            created_at=str(user[4])
        )
    finally:
        conn.close() 