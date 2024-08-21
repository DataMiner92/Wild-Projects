import tkinter as tk
from tkinter import messagebox



class ECommerceGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("E-Commerce System")

        self.label = tk.Label(master, text="Welcome to Sneakers Pro© E-Com System!")
        self.label.pack()

        self.products_button = tk.Button(master, text="Show Products", command=self.show_products)
        self.products_button.pack(pady=5)

        self.add_button = tk.Button(master, text="Add Product to Cart", command=self.show_add_dialog)
        self.add_button.pack(pady=5)

        self.remove_button = tk.Button(master, text="Remove Product from Cart", command=self.show_remove_dialog)
        self.remove_button.pack(pady=5)

        self.cart_button = tk.Button(master, text="Show Cart", command=self.show_cart)
        self.cart_button.pack(pady=5)

        self.order_button = tk.Button(master, text="Place Order", command=self.place_order)
        self.order_button.pack(pady=5)

        self.exit_button = tk.Button(master, text="Exit", command=self.master.quit)
        self.exit_button.pack()

        self.output_text = tk.Text(master, height=10, width=50)
        self.output_text.pack()

        self.ecommerce_system = ECommerceSystem()

    def show_products(self):
        self.update_output(self.ecommerce_system.show_products())

    def show_cart(self):
        self.update_output(self.ecommerce_system.show_cart())

    def place_order(self):
        self.update_output(self.ecommerce_system.place_order())

    def show_add_dialog(self):
        add_dialog = AddProductDialog(self.master, self.ecommerce_system, self.update_output)

    def show_remove_dialog(self):
        remove_dialog = RemoveProductDialog(self.master, self.ecommerce_system, self.update_output)

    def update_output(self, message):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, message)

class AddProductDialog:
    def __init__(self, master, ecommerce_system, update_output):
        self.master = master
        self.ecommerce_system = ecommerce_system
        self.update_output = update_output

        self.dialog = tk.Toplevel(master)
        self.dialog.title("Add Product to Cart")

        self.label = tk.Label(self.dialog, text="Enter Product ID and Quantity:")
        self.label.pack()

        self.product_id_entry = tk.Entry(self.dialog)
        self.product_id_entry.pack()

        self.quantity_entry = tk.Entry(self.dialog)
        self.quantity_entry.pack()

        self.add_button = tk.Button(self.dialog, text="Add", command=self.add_product)
        self.add_button.pack()

    def add_product(self):
        product_id = self.product_id_entry.get()
        quantity = self.quantity_entry.get()
        if product_id.isdigit() and quantity.isdigit():
            result = self.ecommerce_system.add_product_to_cart(int(product_id), int(quantity))
            self.update_output(result)
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Invalid input. Please enter valid product ID and quantity.")

class RemoveProductDialog:
    def __init__(self, master, ecommerce_system, update_output):
        self.master = master
        self.ecommerce_system = ecommerce_system
        self.update_output = update_output

        self.dialog = tk.Toplevel(master)
        self.dialog.title("Remove Product from Cart")

        self.label = tk.Label(self.dialog, text="Enter Product ID:")
        self.label.pack()

        self.product_id_entry = tk.Entry(self.dialog)
        self.product_id_entry.pack()

        self.remove_button = tk.Button(self.dialog, text="Remove", command=self.remove_product)
        self.remove_button.pack()

    def remove_product(self):
        product_id = self.product_id_entry.get()
        if product_id.isdigit():
            result = self.ecommerce_system.remove_product_from_cart(int(product_id))
            self.update_output(result)
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Invalid input. Please enter valid product ID.")

class Product:
    def __init__(self, id, name, price):
        self.id = id
        self.name = name
        self.price = price
        

class CartItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    def get_total_price(self):
        return self.product.price * self.quantity

class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, product, quantity):
        existing_item = next((item for item in self.items if item.product.id == product.id), None)
        if existing_item:
            existing_item.quantity += quantity
        else:
            self.items.append(CartItem(product, quantity))

    def remove_item(self, product_id):
        self.items = [item for item in self.items if item.product.id != product_id]

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items)

    def show_cart(self):
        output = 'Cart:\n'
        for item in self.items:
            output += f"{item.product.name} - Quantity: {item.quantity} - Total Price: ${item.get_total_price()}\n"
        output += f"Total Price: ${self.get_total_price()}"
        return output

class ECommerceSystem:
    def __init__(self):
        self.products = [
            Product(1, 'Sport Sneakers', 100),
            Product(2, 'Sport Race', 200),
            Product(3, 'Baby Shoes ', 100),
            Product(4, 'Skates', 200),
            Product(5, 'Hiking Boots', 400),
            Product(6, 'Rompers', 1500),
            Product(7, 'Baby Gloves', 200),
            
            
           ]
        self.cart = Cart()

    def show_products(self):
        output = 'Available Products:\n'
        for product in self.products:
            output += f"ID: {product.id} - {product.name} - Price: ${product.price}\n"
        return output

    def add_product_to_cart(self, product_id, quantity):
        product = next((p for p in self.products if p.id == product_id), None)
        if product:
            self.cart.add_item(product, quantity)
            return f"{quantity} {product.name}(s) added to cart."
        else:
            return 'Product not found.'

    def remove_product_from_cart(self, product_id):
        self.cart.remove_item(product_id)
        return 'Product removed from cart.'

    def show_cart(self):
        return self.cart.show_cart()

    def place_order(self):
        output = 'You"ve successfully ordered! Thank you. ShopPro© 2024.'
        self.cart = Cart()
        return output

def main():
    root = tk.Tk()
    ecommerce_gui = ECommerceGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    
