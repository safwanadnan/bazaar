from fastapi import FastAPI, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from .models import Product, StockMovement, MovementType, StockLevel
from .database import Database

app = FastAPI(title="Bazaar Inventory API")

# Dependency to get database connection
def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()


# API Models
class ProductCreate(BaseModel):
    name: str
    description: str
    sku: str


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    sku: str
    created_at: str
    updated_at: str


class StockMovementCreate(BaseModel):
    product_id: int
    quantity: int
    movement_type: MovementType
    notes: Optional[str] = None
    store_id: int = 1  # Default to single store in Stage 1


class StockMovementResponse(BaseModel):
    id: int
    product_id: int
    store_id: int
    quantity: int
    movement_type: MovementType
    notes: Optional[str]
    created_at: str


class StockLevelResponse(BaseModel):
    product_id: int
    store_id: int
    quantity: int
    last_updated: str


# API Routes
@app.get("/")
def read_root():
    return {"message": "Welcome to Bazaar Inventory API"}


@app.post("/products/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Database = Depends(get_db)):
    # Check if product with SKU already exists
    existing = db.get_product_by_sku(product.sku)
    if existing:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    product_obj = Product(**product.dict())
    product_id = db.add_product(product_obj)
    
    return db.get_product(product_id)


@app.get("/products/", response_model=List[ProductResponse])
def list_products(db: Database = Depends(get_db)):
    return db.get_all_products()


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Database = Depends(get_db)):
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/stock-movements/", response_model=StockMovementResponse)
def create_stock_movement(movement: StockMovementCreate, db: Database = Depends(get_db)):
    # Validate product exists
    product = db.get_product(movement.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # For sales or removals, check if enough stock is available
    if movement.movement_type in [MovementType.SALE, MovementType.MANUAL_REMOVAL]:
        stock_level = db.get_stock_level(movement.product_id, movement.store_id)
        if stock_level["quantity"] < movement.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Available: {stock_level['quantity']}"
            )
    
    movement_obj = StockMovement(**movement.dict())
    movement_id = db.record_stock_movement(movement_obj)
    
    # Get the created movement
    all_movements = db.get_stock_movements(product_id=movement.product_id)
    for m in all_movements:
        if m["id"] == movement_id:
            return m
    
    # This should not happen, but just in case
    raise HTTPException(status_code=500, detail="Failed to retrieve created stock movement")


@app.get("/stock-movements/", response_model=List[StockMovementResponse])
def list_stock_movements(
    product_id: Optional[int] = None,
    store_id: Optional[int] = None,
    movement_type: Optional[MovementType] = None,
    db: Database = Depends(get_db)
):
    return db.get_stock_movements(product_id, store_id, movement_type)


@app.get("/stock-levels/{product_id}", response_model=StockLevelResponse)
def get_stock_level(
    product_id: int, 
    store_id: int = 1,
    db: Database = Depends(get_db)
):
    # Validate product exists
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return db.get_stock_level(product_id, store_id)
