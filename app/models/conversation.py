from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
 
class ConversationCreate(BaseModel):
    message: str
    role: Optional[int] = 1 

class ConversationMessage(BaseModel):
    conversation_id: int
    user_id: int
    role: str  # "user" or "assistant"
    message: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class ConversationContext(BaseModel):
    user_id: int
    messages: List[Dict[str, str]]
    current_intent: Optional[str] = None
    slot_state: Optional[Dict[str, Any]] = None
    last_products_shown: Optional[List[Dict]] = None
    last_action: Optional[str] = None

class SlotState(BaseModel):
    category: Optional[str] = None
    style: Optional[str] = None  
    color: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None
    additional_attributes: Optional[Dict[str, Any]] = None 