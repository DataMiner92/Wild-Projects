// Farm Fresh Produce Ecommerce Backend
const express = require('express');
const cors = require('cors');
const app = express();

// Middleware
app.use(express.json());
app.use(cors());

// Sample data for our farm fresh produce store
let products = [
    { id: 1, name: "Organic Tomatoes", price: 4.99, category: "vegetables", stock: 50, description: "Fresh organic tomatoes picked daily", image: "tomatoes.jpg", harvestDate: "2023-06-15", farmer: "Green Valley Farms" },
    { id: 2, name: "Fresh Spinach", price: 3.49, category: "leafy-greens", stock: 30, description: "Crisp fresh spinach leaves", image: "spinach.jpg", harvestDate: "2023-06-16", farmer: "Sunshine Organics" },
    { id: 3, name: "Honeycrisp Apples", price: 5.99, category: "fruits", stock: 40, description: "Sweet and crunchy apples", image: "apples.jpg", harvestDate: "2023-06-14", farmer: "Apple Orchard Farms" },
    { id: 4, name: "Carrots", price: 2.99, category: "vegetables", stock: 60, description: "Crunchy orange carrots", image: "carrots.jpg", harvestDate: "2023-06-17", farmer: "Root Veggie Growers" },
    { id: 5, name: "Blueberries", price: 6.99, category: "fruits", stock: 25, description: "Sweet wild blueberries", image: "blueberries.jpg", harvestDate: "2023-06-16", farmer: "Berry Picking Co." }
];

let orders = [];
let customers = [];

// Helper function to generate unique IDs
const generateId = (collection) => {
    return collection.length > 0 ? Math.max(...collection.map(item => item.id)) + 1 : 1;
};

// Product Management Functions

/**
 * Get all products with optional filtering
 */
const getAllProducts = (req, res) => {
    const { category, minPrice, maxPrice, search } = req.query;
    let filteredProducts = [...products];
    
    // Filter by category
    if (category) {
        filteredProducts = filteredProducts.filter(product => 
            product.category.toLowerCase() === category.toLowerCase()
        );
    }
    
    // Filter by price range
    if (minPrice) {
        filteredProducts = filteredProducts.filter(product => 
            product.price >= parseFloat(minPrice)
        );
    }
    
    if (maxPrice) {
        filteredProducts = filteredProducts.filter(product => 
            product.price <= parseFloat(maxPrice)
        );
    }
    
    // Search by name
    if (search) {
        filteredProducts = filteredProducts.filter(product => 
            product.name.toLowerCase().includes(search.toLowerCase())
        );
    }
    
    res.json(filteredProducts);
};

/**
 * Get a specific product by ID
 */
const getProductById = (req, res) => {
    const productId = parseInt(req.params.id);
    const product = products.find(p => p.id === productId);
    
    if (!product) {
        return res.status(404).json({ error: 'Product not found' });
    }
    
    res.json(product);
};

/**
 * Add a new product
 */
const addProduct = (req, res) => {
    const { name, price, category, stock, description, image, farmer } = req.body;
    
    // Validate required fields
    if (!name || !price || !category || typeof stock === 'undefined') {
        return res.status(400).json({ error: 'Missing required fields' });
    }
    
    const newProduct = {
        id: generateId(products),
        name,
        price: parseFloat(price),
        category,
        stock: parseInt(stock),
        description: description || '',
        image: image || 'default-product.jpg',
        harvestDate: new Date().toISOString().split('T')[0], // Today's date
        farmer: farmer || 'Local Farmer'
    };
    
    products.push(newProduct);
    res.status(201).json(newProduct);
};

/**
 * Update a product
 */
const updateProduct = (req, res) => {
    const productId = parseInt(req.params.id);
    const productIndex = products.findIndex(p => p.id === productId);
    
    if (productIndex === -1) {
        return res.status(404).json({ error: 'Product not found' });
    }
    
    const updates = req.body;
    products[productIndex] = { ...products[productIndex], ...updates };
    
    if (typeof updates.price !== 'undefined') {
        products[productIndex].price = parseFloat(updates.price);
    }
    
    if (typeof updates.stock !== 'undefined') {
        products[productIndex].stock = parseInt(updates.stock);
    }
    
    res.json(products[productIndex]);
};

/**
 * Delete a product
 */
const deleteProduct = (req, res) => {
    const productId = parseInt(req.params.id);
    const productIndex = products.findIndex(p => p.id === productId);
    
    if (productIndex === -1) {
        return res.status(404).json({ error: 'Product not found' });
    }
    
    const deletedProduct = products.splice(productIndex, 1)[0];
    res.json({ message: 'Product deleted successfully', product: deletedProduct });
};

// Customer Management Functions

/**
 * Register a new customer
 */
const registerCustomer = (req, res) => {
    const { firstName, lastName, email, phone, address } = req.body;
    
    // Validate required fields
    if (!firstName || !lastName || !email) {
        return res.status(400).json({ error: 'First name, last name, and email are required' });
    }
    
    // Check if customer already exists
    const existingCustomer = customers.find(c => c.email === email);
    if (existingCustomer) {
        return res.status(409).json({ error: 'Customer with this email already exists' });
    }
    
    const newCustomer = {
        id: generateId(customers),
        firstName,
        lastName,
        email,
        phone: phone || '',
        address: address || {},
        joinDate: new Date().toISOString(),
        totalOrders: 0,
        totalSpent: 0
    };
    
    customers.push(newCustomer);
    res.status(201).json(newCustomer);
};

/**
 * Get customer by ID
 */
const getCustomerById = (req, res) => {
    const customerId = parseInt(req.params.id);
    const customer = customers.find(c => c.id === customerId);
    
    if (!customer) {
        return res.status(404).json({ error: 'Customer not found' });
    }
    
    res.json(customer);
};

// Order Management Functions

/**
 * Create a new order
 */
const createOrder = (req, res) => {
    const { customerId, items, shippingAddress, paymentMethod } = req.body;
    
    // Validate required fields
    if (!customerId || !items || !Array.isArray(items) || items.length === 0) {
        return res.status(400).json({ error: 'Customer ID and items are required' });
    }
    
    // Validate customer exists
    const customer = customers.find(c => c.id === customerId);
    if (!customer) {
        return res.status(404).json({ error: 'Customer not found' });
    }
    
    // Validate products and calculate total
    let totalAmount = 0;
    const orderItems = [];
    
    for (const item of items) {
        const product = products.find(p => p.id === item.productId);
        
        if (!product) {
            return res.status(400).json({ error: `Product with ID ${item.productId} not found` });
        }
        
        if (product.stock < item.quantity) {
            return res.status(400).json({ 
                error: `Insufficient stock for ${product.name}. Requested: ${item.quantity}, Available: ${product.stock}` 
            });
        }
        
        const itemTotal = product.price * item.quantity;
        totalAmount += itemTotal;
        
        orderItems.push({
            productId: item.productId,
            productName: product.name,
            quantity: item.quantity,
            unitPrice: product.price,
            subtotal: itemTotal
        });
    }
    
    // Update product stock
    for (const item of items) {
        const productIndex = products.findIndex(p => p.id === item.productId);
        products[productIndex].stock -= item.quantity;
    }
    
    // Create order
    const newOrder = {
        id: generateId(orders),
        customerId,
        items: orderItems,
        totalAmount: parseFloat(totalAmount.toFixed(2)),
        status: 'pending',
        orderDate: new Date().toISOString(),
        shippingAddress: shippingAddress || customer.address,
        paymentMethod: paymentMethod || 'credit_card',
        estimatedDelivery: calculateEstimatedDelivery()
    };
    
    orders.push(newOrder);
    
    // Update customer stats
    const customerIndex = customers.findIndex(c => c.id === customerId);
    if (customerIndex !== -1) {
        customers[customerIndex].totalOrders += 1;
        customers[customerIndex].totalSpent += totalAmount;
    }
    
    res.status(201).json(newOrder);
};

/**
 * Calculate estimated delivery date (2-3 business days)
 */
const calculateEstimatedDelivery = () => {
    const today = new Date();
    const deliveryDate = new Date(today);
    // Add 3 days (2-3 business days)
    deliveryDate.setDate(today.getDate() + 3);
    return deliveryDate.toISOString().split('T')[0];
};

/**
 * Get order by ID
 */
const getOrderById = (req, res) => {
    const orderId = parseInt(req.params.id);
    const order = orders.find(o => o.id === orderId);
    
    if (!order) {
        return res.status(404).json({ error: 'Order not found' });
    }
    
    res.json(order);
};

/**
 * Get orders for a specific customer
 */
const getCustomerOrders = (req, res) => {
    const customerId = parseInt(req.params.customerId);
    const customerOrders = orders.filter(o => o.customerId === customerId);
    
    res.json(customerOrders);
};

/**
 * Update order status
 */
const updateOrderStatus = (req, res) => {
    const orderId = parseInt(req.params.id);
    const { status } = req.body;
    
    const order = orders.find(o => o.id === orderId);
    
    if (!order) {
        return res.status(404).json({ error: 'Order not found' });
    }
    
    // Validate status
    const validStatuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled'];
    if (!validStatuses.includes(status)) {
        return res.status(400).json({ error: 'Invalid status' });
    }
    
    order.status = status;
    res.json(order);
};

// Routes for products
app.get('/api/products', getAllProducts);
app.get('/api/products/:id', getProductById);
app.post('/api/products', addProduct);
app.put('/api/products/:id', updateProduct);
app.delete('/api/products/:id', deleteProduct);

// Routes for customers
app.post('/api/customers', registerCustomer);
app.get('/api/customers/:id', getCustomerById);

// Routes for orders
app.post('/api/orders', createOrder);
app.get('/api/orders/:id', getOrderById);
app.get('/api/customers/:id/orders', getCustomerOrders);
app.put('/api/orders/:id/status', updateOrderStatus);

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

// Handle 404 for undefined routes
app.use('*', (req, res) => {
    res.status(404).json({ error: 'Route not found' });
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`Farm Fresh Produce Ecommerce Server running on port ${PORT}`);
    console.log('Available endpoints:');
    console.log('GET    /api/products - Get all products');
    console.log('POST   /api/products - Add a new product');
    console.log('GET    /api/products/:id - Get a specific product');
    console.log('PUT    /api/products/:id - Update a product');
    console.log('DELETE /api/products/:id - Delete a product');
    console.log('POST   /api/customers - Register a new customer');
    console.log('POST   /api/orders - Create a new order');
    console.log('GET    /api/orders/:id - Get an order by ID');
    console.log('PUT    /api/orders/:id/status - Update order status');
});

module.exports = {
    app,
    products,
    orders,
    customers,
    getAllProducts,
    getProductById,
    addProduct,
    updateProduct,
    deleteProduct,
    registerCustomer,
    getCustomerById,
    createOrder,
    getOrderById,
    getCustomerOrders,
    updateOrderStatus
};