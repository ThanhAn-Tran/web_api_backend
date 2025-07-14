from fastapi import APIRouter, HTTPException, status
from app.models import UserCreate, UserLogin
from app.auth import hash_password, verify_password, create_access_token
from app.database import get_connection

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    """Register a new user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username already exists
        cursor.execute("SELECT Username FROM Users WHERE Username = ?", user.username)
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Hash password and insert user
        hashed_password = hash_password(user.password)
        cursor.execute(
            "INSERT INTO Users (Username, PasswordHash, Email, Role) VALUES (?, ?, ?, ?)",
            user.username, hashed_password, user.email, user.role
        )
        conn.commit()
        return {"message": "User created successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/login")
def login_user(user: UserLogin):
    """User login"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT UserID, Username, PasswordHash, Email, Role FROM Users WHERE Username = ?",
            user.username
        )
        db_user = cursor.fetchone()
        
        if not db_user or not verify_password(user.password, db_user[2]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token({"user_id": db_user[0], "username": db_user[1]})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": db_user[0],
                "username": db_user[1],
                "email": db_user[3],
                "role": db_user[4]
            }
        }
    finally:
        conn.close() 