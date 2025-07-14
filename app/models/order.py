from pydantic import BaseModel

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int
 
class OrderCreate(BaseModel):
    cart_id: int 