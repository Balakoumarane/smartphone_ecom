import uuid


class Smartphone:
    def __init__(self, brand, model, price, storage, ram, battery_capacity,
                 camera_spec, display_size, operating_system, stock_quantity):
        self.phone_id = str(uuid.uuid4())[:8]
        self.brand = brand
        self.model = model
        self.price = float(price)
        self.storage = storage
        self.ram = ram
        self.battery_capacity = int(battery_capacity)
        self.camera_spec = camera_spec
        self.display_size = float(display_size)
        self.operating_system = operating_system
        self.stock_quantity = int(stock_quantity)

    def get_specifications(self):
        return (f"Brand: {self.brand} | Model: {self.model} | Price: ${self.price:.2f}\n"
                f"RAM: {self.ram} | Storage: {self.storage} | OS: {self.operating_system}\n"
                f"Battery: {self.battery_capacity}mAh | Camera: {self.camera_spec}\n"
                f"Display: {self.display_size}\" | Stock: {self.stock_quantity} units")

    def update_price(self, new_price):
        self.price = float(new_price)

    def update_stock(self, quantity):
        self.stock_quantity = int(quantity)

    def check_availability(self):
        return self.stock_quantity > 0

    def display_product_details(self):
        return self.get_specifications()


class Category:
    def __init__(self, category_name, description=""):
        self.category_id = str(uuid.uuid4())[:8]
        self.category_name = category_name
        self.description = description
        self.product_list = []

    def add_smartphone(self, phone):
        self.product_list.append(phone)

    def remove_smartphone(self, phone_id):
        self.product_list = [p for p in self.product_list if p.phone_id != phone_id]

    def get_products(self):
        return self.product_list

    def update_category(self, name, description):
        self.category_name = name
        self.description = description
