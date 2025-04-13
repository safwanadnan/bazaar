import os
import click
import uvicorn
from datetime import datetime

from .database import Database
from .models import Product, StockMovement, MovementType
from .api import app

# Initialize database
db = Database()


@click.group()
def cli():
    """Bazaar Inventory Management System"""
    pass


# Product management commands
@cli.group()
def product():
    """Manage products"""
    pass


@product.command("add")
@click.option("--name", required=True, help="Product name")
@click.option("--description", required=True, help="Product description")
@click.option("--sku", required=True, help="Product SKU (Stock Keeping Unit)")
def add_product(name, description, sku):
    """Add a new product"""
    product = Product(name=name, description=description, sku=sku)
    
    try:
        product_id = db.add_product(product)
        click.echo(f"Product added successfully with ID: {product_id}")
    except Exception as e:
        click.echo(f"Error adding product: {str(e)}")


@product.command("list")
def list_products():
    """List all products"""
    products = db.get_all_products()
    
    if not products:
        click.echo("No products found")
        return
    
    click.echo("\nProduct List:")
    click.echo("=" * 80)
    click.echo(f"{'ID':<5} {'SKU':<15} {'Name':<25} {'Current Stock':<15} {'Description':<20}")
    click.echo("-" * 80)
    
    for product in products:
        stock = db.get_stock_level(product["id"])
        click.echo(
            f"{product['id']:<5} {product['sku']:<15} {product['name']:<25} "
            f"{stock['quantity']:<15} {product['description'][:20]:<20}"
        )


# Stock management commands
@cli.group()
def stock():
    """Manage inventory stock"""
    pass


@stock.command("add")
@click.option("--product-id", type=int, required=True, help="Product ID")
@click.option("--quantity", type=int, required=True, help="Quantity to add")
@click.option("--notes", help="Optional notes")
def stock_in(product_id, quantity, notes):
    """Add stock for a product"""
    if quantity <= 0:
        click.echo("Quantity must be positive")
        return
    
    # Check if product exists
    product = db.get_product(product_id)
    if not product:
        click.echo(f"Product with ID {product_id} not found")
        return
    
    movement = StockMovement(
        product_id=product_id,
        quantity=quantity,
        movement_type=MovementType.STOCK_IN,
        notes=notes
    )
    
    try:
        movement_id = db.record_stock_movement(movement)
        stock = db.get_stock_level(product_id)
        click.echo(
            f"Stock added successfully. Current stock for {product['name']}: {stock['quantity']}"
        )
    except Exception as e:
        click.echo(f"Error adding stock: {str(e)}")


@stock.command("sell")
@click.option("--product-id", type=int, required=True, help="Product ID")
@click.option("--quantity", type=int, required=True, help="Quantity to sell")
@click.option("--notes", help="Optional notes")
def sell(product_id, quantity, notes):
    """Record sale of a product"""
    if quantity <= 0:
        click.echo("Quantity must be positive")
        return
    
    # Check if product exists
    product = db.get_product(product_id)
    if not product:
        click.echo(f"Product with ID {product_id} not found")
        return
    
    # Check if enough stock
    stock = db.get_stock_level(product_id)
    if stock["quantity"] < quantity:
        click.echo(
            f"Insufficient stock. Available: {stock['quantity']}, Requested: {quantity}"
        )
        return
    
    movement = StockMovement(
        product_id=product_id,
        quantity=quantity,
        movement_type=MovementType.SALE,
        notes=notes
    )
    
    try:
        movement_id = db.record_stock_movement(movement)
        stock = db.get_stock_level(product_id)
        click.echo(
            f"Sale recorded successfully. Current stock for {product['name']}: {stock['quantity']}"
        )
    except Exception as e:
        click.echo(f"Error recording sale: {str(e)}")


@stock.command("remove")
@click.option("--product-id", type=int, required=True, help="Product ID")
@click.option("--quantity", type=int, required=True, help="Quantity to remove")
@click.option("--notes", required=True, help="Reason for removal")
def remove(product_id, quantity, notes):
    """Manually remove stock (damaged, lost, etc.)"""
    if quantity <= 0:
        click.echo("Quantity must be positive")
        return
    
    # Check if product exists
    product = db.get_product(product_id)
    if not product:
        click.echo(f"Product with ID {product_id} not found")
        return
    
    # Check if enough stock
    stock = db.get_stock_level(product_id)
    if stock["quantity"] < quantity:
        click.echo(
            f"Insufficient stock. Available: {stock['quantity']}, Requested: {quantity}"
        )
        return
    
    movement = StockMovement(
        product_id=product_id,
        quantity=quantity,
        movement_type=MovementType.MANUAL_REMOVAL,
        notes=notes
    )
    
    try:
        movement_id = db.record_stock_movement(movement)
        stock = db.get_stock_level(product_id)
        click.echo(
            f"Stock removed successfully. Current stock for {product['name']}: {stock['quantity']}"
        )
    except Exception as e:
        click.echo(f"Error removing stock: {str(e)}")


@stock.command("level")
@click.option("--product-id", type=int, required=True, help="Product ID")
def stock_level(product_id):
    """Check current stock level for a product"""
    # Check if product exists
    product = db.get_product(product_id)
    if not product:
        click.echo(f"Product with ID {product_id} not found")
        return
    
    stock = db.get_stock_level(product_id)
    click.echo(f"Current stock for {product['name']} (SKU: {product['sku']}): {stock['quantity']}")


@stock.command("history")
@click.option("--product-id", type=int, help="Filter by product ID")
@click.option("--movement-type", type=click.Choice(['stock_in', 'sale', 'manual_removal']), 
              help="Filter by movement type")
def stock_history(product_id, movement_type):
    """View stock movement history"""
    movement_type_enum = None
    if movement_type:
        movement_type_enum = MovementType(movement_type)
    
    movements = db.get_stock_movements(product_id=product_id, movement_type=movement_type_enum)
    
    if not movements:
        click.echo("No stock movements found")
        return
    
    click.echo("\nStock Movement History:")
    click.echo("=" * 100)
    click.echo(
        f"{'ID':<5} {'Date':<20} {'Product ID':<12} {'Type':<15} {'Quantity':<10} {'Notes':<30}"
    )
    click.echo("-" * 100)
    
    for m in movements:
        # Get product name for better display
        product = db.get_product(m["product_id"])
        product_display = f"{m['product_id']} ({product['name']})" if product else m["product_id"]
        
        # Format date
        date_str = datetime.fromisoformat(m["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        
        click.echo(
            f"{m['id']:<5} {date_str:<20} {product_display:<12} {m['movement_type']:<15} "
            f"{m['quantity']:<10} {m['notes'] or '':<30}"
        )


# API server command
@cli.command("serve")
@click.option("--host", default="127.0.0.1", help="Host to bind")
@click.option("--port", default=8000, help="Port to bind")
def serve(host, port):
    """Start the API server"""
    click.echo(f"Starting Inventory API server at http://{host}:{port}")
    uvicorn.run("src.api:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    cli()
