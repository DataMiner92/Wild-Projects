# Farm Fresh Produce Ecommerce Backend

A Node.js backend for a farm fresh produce ecommerce website built with Express.js.

## Features

- Product management (CRUD operations)
- Customer registration and management
- Order processing system
- Inventory management
- Harvest date tracking
- Farmer information
- Stock level monitoring

## API Endpoints

### Products

- `GET /api/products` - Get all products (with optional filtering by category, price, or search term)
- `GET /api/products/:id` - Get a specific product
- `POST /api/products` - Add a new product
- `PUT /api/products/:id` - Update a product
- `DELETE /api/products/:id` - Delete a product

### Customers

- `POST /api/customers` - Register a new customer
- `GET /api/customers/:id` - Get customer details

### Orders

- `POST /api/orders` - Create a new order
- `GET /api/orders/:id` - Get order details
- `GET /api/customers/:id/orders` - Get all orders for a customer
- `PUT /api/orders/:id/status` - Update order status

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Or start the production server:
```bash
npm start
```

The server will run on port 3000 by default.

## Example Usage

### Adding a Product

```bash
curl -X POST http://localhost:3000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fresh Strawberries",
    "price": 7.99,
    "category": "fruits",
    "stock": 30,
    "description": "Sweet and juicy strawberries",
    "farmer": "Berry Good Farms"
  }'
```

### Creating an Order

```bash
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": 1,
    "items": [
      {
        "productId": 1,
        "quantity": 2
      },
      {
        "productId": 3,
        "quantity": 1
      }
    ],
    "shippingAddress": {
      "street": "123 Main St",
      "city": "Anytown",
      "state": "CA",
      "zipCode": "12345"
    }
  }'
```

## Data Models

### Product
- `id`: Unique identifier
- `name`: Product name
- `price`: Price per unit
- `category`: Product category (fruits, vegetables, leafy-greens, etc.)
- `stock`: Available quantity
- `description`: Product description
- `image`: Image filename
- `harvestDate`: Date when produce was harvested
- `farmer`: Name of the farmer

### Customer
- `id`: Unique identifier
- `firstName`: Customer's first name
- `lastName`: Customer's last name
- `email`: Customer's email address
- `phone`: Customer's phone number (optional)
- `address`: Shipping address object
- `joinDate`: Registration date
- `totalOrders`: Total number of orders placed
- `totalSpent`: Total amount spent

### Order
- `id`: Unique identifier
- `customerId`: Reference to the customer who placed the order
- `items`: Array of ordered items with product info and quantities
- `totalAmount`: Total cost of the order
- `status`: Order status (pending, processing, shipped, delivered, cancelled)
- `orderDate`: Date when the order was placed
- `shippingAddress`: Address where the order will be delivered
- `paymentMethod`: Payment method used
- `estimatedDelivery`: Estimated delivery date

## Farm-Specific Features

This backend is designed specifically for farm fresh produce and includes features such as:

- Harvest date tracking to ensure freshness
- Farmer attribution to support local growers
- Inventory management to prevent overselling
- Quality tracking through product descriptions
- Seasonal availability indicators

## Contributing

Feel free to submit issues and enhancement requests via GitHub.

## License

MIT License