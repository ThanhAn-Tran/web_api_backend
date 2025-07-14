from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class ChatMessage(BaseModel):
    message: str

class ActionPerformed(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    products: Optional[List[Dict[str, Any]]] = None
    actions_performed: Optional[List[Union[str, ActionPerformed]]] = None
    conversation_id: Optional[int] = None

class ProductRecommendation(BaseModel):
    product_id: int
    name: str
    description: str
    price: float
    color: str
    style: str
    relevance_score: float
    reason: str

class ChatContext(BaseModel):
    user_id: int
    recent_messages: List[Dict[str, str]]
    user_preferences: Dict[str, Any]
    current_intent: Optional[str] = None 