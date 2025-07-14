from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Dict, Any
import logging

from app.auth import get_current_user
from app.models.chatbot import ChatMessage, ChatResponse
from app.services.improved_chatbot import ImprovedChatbotService

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])
security = HTTPBearer()

# Use the improved chatbot service with conversation memory
chatbot = ImprovedChatbotService()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    message: ChatMessage,
    current_user_id: int = Depends(get_current_user)
):
    """
    Send a message to the AI chatbot with conversation memory and context awareness
    """
    try:
        user_id = current_user_id
        
        logger.info(f"User {user_id} sent message: {message.message}")
        
        # Use the improved chatbot service
        result = chatbot.chat(user_id, message.message)
        
        response = ChatResponse(
            response=result["response"],
            products=result.get("products", []),
            actions_performed=result.get("actions_performed", []),
            conversation_id=result.get("conversation_id", 1)
        )
        
        logger.info(f"Bot responded to user {user_id} with intent: {result.get('intent')}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}"
        )

@router.get("/history")
async def get_conversation_history(
    limit: int = 10,
    current_user_id: int = Depends(get_current_user)
):
    """
    Get conversation history for the current user
    """
    try:
        user_id = current_user_id
        
        from app.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TOP (?) ConversationID, Role, Message, CreatedAt
            FROM Conversations 
            WHERE UserID = ? 
            ORDER BY CreatedAt DESC
        """, (limit * 2, user_id))
        
        results = cursor.fetchall()
        conn.close()
        
        conversations = []
        for row in results:
            conversations.append({
                "conversation_id": row[0],
                "role": "user" if row[1] == 1 else "assistant",
                "message": row[2],
                "created_at": str(row[3]) if row[3] else ""
            })
        
        return {
            "conversations": list(reversed(conversations)),
            "total": len(conversations)
        }
        
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching conversation history: {str(e)}"
        )

@router.post("/product-search")
async def natural_language_product_search(
    message: ChatMessage,
    current_user_id: int = Depends(get_current_user)
):
    """
    Search products using natural language with AI and slot filling
    """
    try:
        user_id = current_user_id
        
        # Use improved chatbot for product search
        result = chatbot.chat(user_id, message.message)
        
        return {
            "query": message.message,
            "response": result["response"],
            "products": result["products"],
            "total_found": len(result["products"]),
            "intent": result["intent"]
        }
        
    except Exception as e:
        logger.error(f"Error in product search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching products: {str(e)}"
        )

@router.post("/cart-action")
async def cart_action(
    message: ChatMessage,
    current_user_id: int = Depends(get_current_user)
):
    """
    Perform cart actions (add, remove, view) using natural language
    """
    try:
        user_id = current_user_id
        
        # Process through chatbot
        result = chatbot.chat(user_id, message.message)
        
        # Check if it was a cart-related action
        cart_actions = ["add_to_cart", "remove_from_cart", "view_cart"]
        if result.get("intent") in cart_actions:
            return {
                "success": True,
                "action": result["intent"],
                "response": result["response"],
                "products": result.get("products", [])
            }
        else:
            return {
                "success": False,
                "action": "none",
                "response": "Please specify a cart action (add, remove, or view cart).",
                "products": []
            }
        
    except Exception as e:
        logger.error(f"Error in cart action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing cart action: {str(e)}"
        )

@router.get("/cart-contents")
async def get_cart_contents(
    current_user_id: int = Depends(get_current_user)
):
    """
    Get current cart contents for the user
    """
    try:
        user_id = current_user_id
        
        # Use chatbot to get formatted cart contents
        result = chatbot.chat(user_id, "show my cart")
        
        return {
            "cart_summary": result["response"],
            "items": result.get("products", []),
            "total_items": len(result.get("products", []))
        }
        
    except Exception as e:
        logger.error(f"Error getting cart contents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cart contents: {str(e)}"
        )

@router.post("/quick-chat")
async def quick_chat(
    message: ChatMessage,
    current_user_id: int = Depends(get_current_user)
):
    """
    Quick chat with context-aware AI chatbot
    """
    try:
        user_id = current_user_id
        
        # Use the improved chatbot
        result = chatbot.chat(user_id, message.message)
        
        return {
            "response": result["response"],
            "intent": result["intent"],
            "actions": result["actions_performed"]
        }
        
    except Exception as e:
        logger.error(f"Error in quick-chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/reset")
async def reset_conversation(
    current_user_id: int = Depends(get_current_user)
):
    """
    Reset conversation state and start fresh
    """
    try:
        user_id = current_user_id
        
        logger.info(f"User {user_id} requested conversation reset")
        
        # Reset conversation using the improved chatbot service
        result = chatbot.reset_conversation(user_id)
        
        response = ChatResponse(
            response=result["response"],
            products=result.get("products", []),
            actions_performed=result.get("actions_performed", []),
            conversation_id=result.get("conversation_id", None)
        )
        
        logger.info(f"Reset conversation for user {user_id}, status: {result.get('status')}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in reset endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 