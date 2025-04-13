from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MovementType(str, Enum):
    STOCK_IN = "stock_in"
    SALE = "sale"
    MANUAL_REMOVAL = "manual_removal"


class Product(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    sku: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        orm_mode = True


class StockMovement(BaseModel):
    id: Optional[int] = None
    product_id: int
    store_id: int = 1  # Default to single store in Stage 1
    quantity: int
    movement_type: MovementType
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        orm_mode = True


class StockLevel(BaseModel):
    product_id: int
    store_id: int = 1  # Default to single store in Stage 1
    quantity: int
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        orm_mode = True


class Store(BaseModel):
    id: Optional[int] = None
    name: str
    location: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        orm_mode = True
