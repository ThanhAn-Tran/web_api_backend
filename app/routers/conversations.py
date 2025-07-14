from fastapi import APIRouter, HTTPException, Depends, status
from app.models import ConversationCreate
from app.auth import get_current_user
from app.database import get_connection

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_conversation(conversation: ConversationCreate, current_user_id: int = Depends(get_current_user)):
    """Save a chat message"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO Conversations (UserID, Role, Message) VALUES (?, ?, ?)",
            current_user_id, conversation.role, conversation.message
        )
        conn.commit()
        return {"message": "Conversation saved successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("")
def get_user_conversations(current_user_id: int = Depends(get_current_user)):
    """Get user's chat history"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT ConversationID, Role, Message, CreatedAt
            FROM Conversations
            WHERE UserID = ?
            ORDER BY CreatedAt ASC
        """, current_user_id)
        
        conversations = cursor.fetchall()
        
        return [
            {
                "conversation_id": conv[0],
                "role": conv[1],
                "message": conv[2],
                "created_at": str(conv[3])
            } for conv in conversations
        ]
    finally:
        conn.close() 