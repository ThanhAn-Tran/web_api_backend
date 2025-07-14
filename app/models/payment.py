from pydantic import BaseModel
from typing import Optional

class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str  # 'Momo', 'COD', 'Credit Card', 'ZaloPay'

class PaymentStatusUpdate(BaseModel):
    payment_status: str  # 'Paid', 'Unpaid', 'Failed', 'Refunded'

class PaymentResponse(BaseModel):
    payment_id: int
    order_id: int
    payment_method: str
    payment_status: str
    transaction_code: Optional[str]
    paid_at: Optional[str] 