# Bazaar Inventory Tracking System

An inventory tracking system designed to evolve from a single kiryana store to a multi-store, multi-supplier platform with audit capabilities.

## Overview

This system provides an efficient way to track product inventory and stock movements across stores. It supports:

- Product management (add, view, list)
- Stock movement tracking (stock-in, sales, manual removals)
- Real-time stock level monitoring
- Multi-store inventory management (in later stages)

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

#### CLI Usage

```bash
# Add a product
python -m src.main product add --name "Rice" --description "Basmati Rice 5kg" --sku "RICE-001"

# Add stock
python -m src.main stock add --product-id 1 --quantity 100 --notes "Initial stock"

# Record a sale
python -m src.main stock sell --product-id 1 --quantity 5 --notes "Customer sale"

# Remove stock manually
python -m src.main stock remove --product-id 1 --quantity 2 --notes "Damaged packaging"

# Check stock level
python -m src.main stock level --product-id 1

# View stock movement history
python -m src.main stock history
python -m src.main stock history --product-id 1
python -m src.main stock history --movement-type sale
```

#### API Server

```bash
python -m src.main serve --host 127.0.0.1 --port 8000
```

Then access the API documentation at: http://127.0.0.1:8000/docs

## System Design

### Stage 1: Single Store Implementation

#### Data Model
- **Product**: Basic product information (name, SKU, description)
- **StockMovement**: Records of stock changes (stock-in, sales, removals)
- **StockLevel**: Current quantity of a product

#### Architecture
- Simple SQLite database for persistence
- CLI interface for basic operations
- REST API for integration capabilities

#### Key Features
- Track product stock-in, sales, and manual removals
- Real-time stock level calculation
- Basic reporting through CLI

### Stage 2: Multi-Store Expansion (500+ Stores)

#### Enhanced Data Model
- Add `Store` entity with store-specific information
- Extend stock movements and levels to be store-specific
- Implement central product catalog with store-specific stock

#### Architecture Changes
- Migrate from SQLite to PostgreSQL for better concurrency
- Implement comprehensive REST API
- Add filtering and reporting by store, date range
- Introduce basic authentication and request throttling

#### New Features
- Store-specific inventory tracking
- Advanced filtering and reporting
- API rate limiting to prevent abuse
- User authentication and authorization

### Stage 3: Enterprise Scale (1000+ Stores)

#### Advanced Data Model
- Add supplier relationships
- Implement audit logging and traceability
- Add product categories and attributes

#### Architecture Evolution
- Horizontally scalable services
- Asynchronous processing using message queue (Kafka/RabbitMQ)
- Read/write separation (CQRS pattern)
- Caching layer (Redis) for frequently accessed data
- Strong API rate-limiting and security

#### Enterprise Features
- Near real-time stock sync across stores
- Full audit trail of all inventory changes
- Performance optimization for high-volume operations
- Data analytics capabilities
- Multi-tenant support

## API Design

### Stage 1 API Endpoints

- `GET /products/`: List all products
- `POST /products/`: Create a new product
- `GET /products/{product_id}`: Get a specific product
- `GET /stock-levels/{product_id}`: Get current stock level
- `POST /stock-movements/`: Record a stock movement
- `GET /stock-movements/`: List stock movements

### Stage 2 API Additions

- `GET /stores/`: List all stores
- `POST /stores/`: Create a new store
- `GET /stores/{store_id}`: Get a specific store
- `GET /stores/{store_id}/stock-levels`: Get stock levels for a store
- `GET /stock-movements/?store_id={store_id}&date_from={date}&date_to={date}`: Advanced filtering

### Stage 3 API Extensions

- `POST /batch-stock-movements/`: Process multiple movements asynchronously
- `GET /audit-logs/`: Access audit trail
- `GET /analytics/stock-trends`: Stock level trends over time
- `GET /analytics/sales-velocity`: Product sales velocity

## Design Decisions and Trade-offs

### Local Storage vs. RDBMS
- **Stage 1**: SQLite for simplicity and easy deployment
- **Stage 2**: PostgreSQL for concurrency, transactions, and advanced querying
- **Trade-off**: Initial simplicity vs. future scalability

### Synchronous vs. Asynchronous Processing
- **Stage 1-2**: Synchronous operations for simplicity and immediate consistency
- **Stage 3**: Asynchronous event-driven architecture for scaling
- **Trade-off**: Consistency vs. performance at scale

### Data Modeling Approach
- Designed core models (Product, StockMovement) to be extensible
- Used default values where appropriate to maintain backward compatibility
- **Trade-off**: Some redundancy in early stages to enable easier evolution

### Caching Strategy
- **Stage 1-2**: No caching, direct database access
- **Stage 3**: Redis caching for product catalog and stock levels
- **Trade-off**: System complexity vs. performance at scale

## Assumptions

1. A product can only exist once in the central catalog (unique SKU)
2. Stock quantities are non-negative integers
3. In Stage 1, a single store is assumed (store_id=1)
4. Each stock movement affects exactly one product at one store
5. All dates and times are stored in UTC
6. The system will progressively evolve from Stage 1 to Stage 3

## Future Considerations

- **Mobile App Integration**: API design considers future mobile applications
- **Data Warehousing**: Schema supports extraction for analytics
- **Multi-Region Deployment**: Architecture can evolve to global distribution
- **Offline Support**: Could add sync capabilities for offline operation
- **IoT Integration**: API supports integration with smart shelf systems
