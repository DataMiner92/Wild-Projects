// Example usage of the Farm Fresh Produce Ecommerce Backend functions

// Import the functions from our server module
const {
    addProduct,
    registerCustomer,
    createOrder,
    getAllProducts,
    getCustomerById,
    getOrderById
} = require('./server');

// Mock request and response objects for demonstration
const mockReq = (body, params = {}, query = {}) => ({ body, params, query });
const mockRes = () => {
    const res = {};
    res.status = (code) => {
        res.statusCode = code;
        return res;
    };
    res.json = (data) => {
        res.data = data;
        return res;
    };
    return res;
};

console.log("=== Farm Fresh Produce Ecommerce Backend Example ===\n");

// Example 1: Adding a new product
console.log("1. Adding a new product:");
const newProductRequest = mockReq({
    name: "Fresh Corn",
    price: 3.99,
    category: "vegetables",
    stock: 40,
    description: "Sweet corn picked fresh this morning",
    farmer: "Cornfield Farms"
});

const newProductResponse = mockRes();
addProduct(newProductRequest, newProductResponse);
console.log("Added product:", newProductResponse.data);
console.log("");

// Example 2: Registering a new customer
console.log("2. Registering a new customer:");
const newCustomerRequest = mockReq({
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com",
    phone: "555-1234",
    address: {
        street: "123 Main St",
        city: "Anytown",
        state: "CA",
        zipCode: "12345"
    }
});

const newCustomerResponse = mockRes();
registerCustomer(newCustomerRequest, newCustomerResponse);
console.log("Registered customer:", newCustomerResponse.data);
console.log("");

// Example 3: Creating an order
console.log("3. Creating an order:");
const newOrderRequest = mockReq({
    customerId: 1, // Using the ID of the newly registered customer
    items: [
        { productId: 1, quantity: 2 }, // 2 Organic Tomatoes
        { productId: 2, quantity: 1 }  // 1 Fresh Spinach
    ],
    shippingAddress: {
        street: "123 Main St",
        city: "Anytown",
        state: "CA",
        zipCode: "12345"
    }
});

const newOrderResponse = mockRes();
createOrder(newOrderRequest, newOrderResponse);
console.log("Created order:", newOrderResponse.data);
console.log("");

// Example 4: Getting all products with filtering
console.log("4. Getting all vegetable products:");
const getProductsRequest = mockReq({}, {}, { category: "vegetables" });
const getProductsResponse = mockRes();
getAllProducts(getProductsRequest, getProductsResponse);
console.log("Vegetable products:", getProductsResponse.data);
console.log("");

// Example 5: Getting a specific customer
console.log("5. Getting customer by ID:");
const getCustomerRequest = mockReq({}, { id: 1 });
const getCustomerResponse = mockRes();
getCustomerById(getCustomerRequest, getCustomerResponse);
console.log("Customer details:", getCustomerResponse.data);
console.log("");

console.log("=== Examples completed ===");