import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .models import Product, StockMovement, StockLevel, MovementType


class Database:
    def __init__(self, db_path="inventory.db"):
        self.db_path = db_path
        self.conn = None
        self.initialize_db()
    
    def initialize_db(self):
        """Create database and tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Create Products table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            sku TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')
        
        # Create StockMovements table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            store_id INTEGER DEFAULT 1,
            quantity INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        
        # Create StockLevels table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_levels (
            product_id INTEGER NOT NULL,
            store_id INTEGER DEFAULT 1,
            quantity INTEGER NOT NULL DEFAULT 0,
            last_updated TIMESTAMP,
            PRIMARY KEY (product_id, store_id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        
        # Create Stores table (for future use)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            created_at TIMESTAMP
        )
        ''')
        
        # Insert default store for Stage 1
        cursor.execute('''
        INSERT OR IGNORE INTO stores (id, name, location, created_at)
        VALUES (1, 'Default Store', 'Default Location', ?)
        ''', (datetime.now().isoformat(),))
        
        self.conn.commit()
    
    def add_product(self, product: Product) -> int:
        """Add a new product and return its ID"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute(
            '''
            INSERT INTO products (name, description, sku, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (product.name, product.description, product.sku, now, now)
        )
        self.conn.commit()
        
        return cursor.lastrowid
    
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a product by ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get a product by SKU"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM products WHERE sku = ?', (sku,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM products')
        return [dict(row) for row in cursor.fetchall()]
    
    def record_stock_movement(self, movement: StockMovement) -> int:
        """Record a stock movement and update stock levels"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        # Insert the movement record
        cursor.execute(
            '''
            INSERT INTO stock_movements 
            (product_id, store_id, quantity, movement_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                movement.product_id, 
                movement.store_id, 
                movement.quantity, 
                movement.movement_type, 
                movement.notes, 
                now
            )
        )
        
        # Update stock levels
        quantity_change = movement.quantity
        if movement.movement_type in [MovementType.SALE, MovementType.MANUAL_REMOVAL]:
            quantity_change = -quantity_change
        
        # Check if record exists
        cursor.execute(
            '''
            SELECT quantity FROM stock_levels 
            WHERE product_id = ? AND store_id = ?
            ''',
            (movement.product_id, movement.store_id)
        )
        
        row = cursor.fetchone()
        
        if row:
            # Update existing record
            cursor.execute(
                '''
                UPDATE stock_levels 
                SET quantity = quantity + ?, last_updated = ?
                WHERE product_id = ? AND store_id = ?
                ''',
                (quantity_change, now, movement.product_id, movement.store_id)
            )
        else:
            # Insert new record
            cursor.execute(
                '''
                INSERT INTO stock_levels 
                (product_id, store_id, quantity, last_updated)
                VALUES (?, ?, ?, ?)
                ''',
                (movement.product_id, movement.store_id, quantity_change, now)
            )
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_stock_level(self, product_id: int, store_id: int = 1) -> Dict[str, Any]:
        """Get current stock level for a product"""
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            SELECT * FROM stock_levels 
            WHERE product_id = ? AND store_id = ?
            ''',
            (product_id, store_id)
        )
        
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return {"product_id": product_id, "store_id": store_id, "quantity": 0}
    
    def get_stock_movements(
        self, 
        product_id: Optional[int] = None,
        store_id: Optional[int] = None,
        movement_type: Optional[MovementType] = None
    ) -> List[Dict[str, Any]]:
        """Get stock movements with optional filters"""
        cursor = self.conn.cursor()
        query = "SELECT * FROM stock_movements WHERE 1=1"
        params = []
        
        if product_id:
            query += " AND product_id = ?"
            params.append(product_id)
        
        if store_id:
            query += " AND store_id = ?"
            params.append(store_id)
        
        if movement_type:
            query += " AND movement_type = ?"
            params.append(movement_type)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
