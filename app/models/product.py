from pydantic import BaseModel, Field
from typing import Optional, List

class CategoryCreate(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    category_id: int
    name: str

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    color: str
    style: str
    category_id: int

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    color: Optional[str] = None
    style: Optional[str] = None
    category_id: Optional[int] = None
    is_locked: Optional[bool] = None

class ProductImageResponse(BaseModel):
    image_id: int
    image_url: str

class ProductResponse(BaseModel):
    product_id: int
    name: str
    description: str
    price: float
    stock: int
    color: str
    style: str
    category_id: int
    is_locked: bool
    image_path: Optional[str]
    images: List[ProductImageResponse]
    created_at: str 