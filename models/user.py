from datetime import date
import uuid


class User:
    def __init__(self, name, email, phone_number, password, address=""):
        self.user_id = str(uuid.uuid4())[:8]
        self.name = name
        self.email = email
        self.phone_number = phone_number
        self.password = password
        self.address = address
        self.account_status = "active"
        self.registration_date = date.today()

    def login(self, email, password):
        return self.email == email and self.password == password

    def logout(self):
        pass

    def update_profile(self, name, phone, address):
        self.name = name
        self.phone_number = phone
        self.address = address

    def change_password(self, old_password, new_password):
        if self.password == old_password:
            self.password = new_password
            return True
        return False

    def get_user_details(self):
        return f"ID: {self.user_id} | Name: {self.name} | Email: {self.email}"


class Customer(User):
    def __init__(self, name, email, phone_number, password, address=""):
        super().__init__(name, email, phone_number, password, address)
        self.customer_id = self.user_id
        self.cart = None
        self.order_history = []
        self.shipping_address = address
        self.loyalty_points = 0

    def browse_products(self, store):
        return store.smartphones

    def search_product(self, keyword, store):
        kw = keyword.lower()
        return [p for p in store.smartphones
                if kw in p.brand.lower() or kw in p.model.lower()]

    def add_to_cart(self, phone, quantity):
        if self.cart:
            self.cart.add_item(phone, quantity)

    def remove_from_cart(self, phone_id):
        if self.cart:
            self.cart.remove_item(phone_id)

    def view_cart(self):
        return self.cart

    def place_order(self, store):
        if not self.cart or not self.cart.items:
            return None
        from models.order import Order
        order = Order(self, self.cart.items[:])
        self.order_history.append(order)
        store.orders.append(order)
        self.cart.clear_cart()
        return order

    def view_orders(self):
        return self.order_history


class Admin(User):
    def __init__(self, name, email, phone_number, password):
        super().__init__(name, email, phone_number, password)
        self.admin_id = self.user_id
        self.role = "admin"
        self.permissions = "full"

    def add_product(self, phone, store):
        store.smartphones.append(phone)

    def update_product(self, phone_id, price, quantity, store):
        for p in store.smartphones:
            if p.phone_id == phone_id:
                p.price = price
                p.stock_quantity = quantity
                return True
        return False

    def remove_product(self, phone_id, store):
        store.smartphones = [p for p in store.smartphones if p.phone_id != phone_id]

    def manage_orders(self, order, status):
        order.update_order_status(status)

    def generate_sales_report(self, store):
        from models.report import Report
        report = Report(store.orders)
        store.reports.append(report)
        return report
